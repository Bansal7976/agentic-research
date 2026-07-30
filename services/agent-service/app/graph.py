"""The LangGraph multi-agent workflow — the brain of the project.

Graph:  guard_input -> planner -> researcher -> summarizer -> writer
        -> guard_output -> save   (or -> blocked if guardrails reject)

Each node is a small function that reads/updates shared state. The researcher
is a ReAct agent that decides for itself which MCP tools to call and when.
"""
import logging
import re
from typing import TypedDict

import httpx
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from . import guardrails
from .config import settings

logger = logging.getLogger("agent-service.graph")


class ResearchState(TypedDict, total=False):
    topic: str
    max_subquestions: int
    blocked_reason: str
    plan: list[str]
    findings: list[str]
    sources: list[str]
    summary: str
    report: str
    report_location: str


class Plan(BaseModel):
    subquestions: list[str] = Field(description="Focused sub-questions to research")


@tool
def search_uploaded_docs(query: str) -> str:
    """Search the user's uploaded documents (private knowledge base) for context."""
    try:
        r = httpx.post(
            f"{settings.rag_service_url}/retrieve", json={"query": query, "k": 4}, timeout=30
        )
        results = r.json().get("results", [])
        return "\n\n".join(f"[{c['source']}] {c['text']}" for c in results) or "No matches."
    except Exception as e:
        return f"Document search unavailable: {e}"


def _text(content) -> str:
    """Normalize LLM output: newer Gemini models return a LIST of content
    blocks instead of a plain string — join the text parts either way."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                parts.append(block.get("text", ""))
            else:
                parts.append(getattr(block, "text", "") or "")
        return "".join(parts)
    return str(content)


def _llm(temperature: float = 0.3):
    if settings.use_vertex_ai:
        from langchain_google_vertexai import ChatVertexAI

        return ChatVertexAI(
            model=settings.gemini_model,
            project=settings.gcp_project_id,
            location=settings.gcp_location,
            temperature=temperature,
        )
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=temperature,
    )


async def build_graph(mcp_tools: list):
    llm = _llm()
    planner_llm = _llm(0.2).with_structured_output(Plan)
    researcher = create_react_agent(
        llm,
        mcp_tools + [search_uploaded_docs],
        prompt=(
            "You are a meticulous research agent. Use the available tools to gather "
            "facts about the question. Always include source URLs in your answer. "
            "Stop once you have enough information; do not call tools endlessly."
        ),
    )
    save_tool = next((t for t in mcp_tools if t.name == "save_report"), None)

    def guard_input(state: ResearchState):
        ok, reason = guardrails.check_input(state["topic"])
        return {"blocked_reason": "" if ok else reason}

    def route_after_guard(state: ResearchState):
        return "blocked" if state["blocked_reason"] else "planner"

    async def planner(state: ResearchState):
        n = state.get("max_subquestions", 3)
        plan = await planner_llm.ainvoke(
            f"Break this research topic into at most {n} focused, answerable "
            f"sub-questions:\n\nTopic: {state['topic']}"
        )
        return {"plan": plan.subquestions[:n]}

    async def researcher_node(state: ResearchState):
        findings, sources = [], []
        for question in state["plan"]:
            result = await researcher.ainvoke(
                {"messages": [("user", question)]},
                config={"recursion_limit": 12},
            )
            answer = _text(result["messages"][-1].content)
            findings.append(f"### {question}\n{answer}")
            # collect URLs from the whole conversation, tool results included
            for message in result["messages"]:
                sources += re.findall(
                    r"https?://[^\s)\]>\"']+", _text(getattr(message, "content", ""))
                )
        deduped = list(dict.fromkeys(sources))[:10]
        return {"findings": findings, "sources": deduped}

    async def summarizer(state: ResearchState):
        joined = "\n\n".join(state["findings"])
        msg = await llm.ainvoke(
            f"Summarize the key insights from this research in 5-8 bullet points:\n\n{joined}"
        )
        return {"summary": _text(msg.content)}

    async def writer(state: ResearchState):
        msg = await llm.ainvoke(
            "Write a well-structured markdown research report.\n"
            "Structure: # Title, ## Executive Summary, one ## section per sub-question "
            "(use the findings), ## Conclusion, ## Sources (list the URLs).\n\n"
            f"Topic: {state['topic']}\n\nKey insights:\n{state['summary']}\n\n"
            f"Detailed findings:\n{'\n\n'.join(state['findings'])}\n\n"
            f"Sources: {state['sources']}"
        )
        return {"report": _text(msg.content)}

    def guard_output(state: ResearchState):
        clean, redacted = guardrails.scrub_output(state["report"])
        if redacted:
            logger.warning("Output guardrail redacted PII: %s", redacted)
        return {"report": clean}

    async def save(state: ResearchState):
        if save_tool is None:
            return {"report_location": None}
        try:
            location = await save_tool.ainvoke(
                {"topic": state["topic"], "content": state["report"]}
            )
            return {"report_location": _text(location)}
        except Exception as e:
            logger.warning("save_report failed: %s", e)
            return {"report_location": None}

    def blocked(state: ResearchState):
        return {"report": f"Request blocked by guardrails: {state['blocked_reason']}",
                "sources": [], "findings": []}

    g = StateGraph(ResearchState)
    g.add_node("guard_input", guard_input)
    g.add_node("planner", planner)
    g.add_node("researcher", researcher_node)
    g.add_node("summarizer", summarizer)
    g.add_node("writer", writer)
    g.add_node("guard_output", guard_output)
    g.add_node("save", save)
    g.add_node("blocked", blocked)

    g.add_edge(START, "guard_input")
    g.add_conditional_edges("guard_input", route_after_guard,
                            {"planner": "planner", "blocked": "blocked"})
    g.add_edge("planner", "researcher")
    g.add_edge("researcher", "summarizer")
    g.add_edge("summarizer", "writer")
    g.add_edge("writer", "guard_output")
    g.add_edge("guard_output", "save")
    g.add_edge("save", END)
    g.add_edge("blocked", END)
    return g.compile()
