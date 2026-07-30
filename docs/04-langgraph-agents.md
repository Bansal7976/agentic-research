# LangGraph & Multi-Agent Systems

## Chain vs Agent
- **Chain**: fixed steps — prompt → LLM → output. Same path every time.
- **Agent**: the LLM *decides* what to do next — which tool to call, whether to
  keep researching or stop. The path is dynamic.

## What is LangGraph?
LangGraph models an LLM workflow as a **state machine**: nodes (steps) +
edges (what runs next) + shared **state** (a dict every node reads/updates).
This gives you loops, branching, retries, and checkpointing — things a linear
chain can't do cleanly.

## Our graph ([graph.py](../services/agent-service/app/graph.py))
```
START → guard_input ──(blocked?)──→ blocked → END
             │
             ▼
          planner        breaks topic into ≤N sub-questions (structured output)
             ▼
         researcher      ReAct agent: loops tool-call → observe → think → repeat
             ▼
         summarizer      compresses findings into key insights
             ▼
           writer        writes the final markdown report
             ▼
        guard_output     scrubs PII
             ▼
            save         MCP save_report → Cloud Storage / local file
             ▼
            END
```

Shared state (`ResearchState`): `topic, plan, findings, sources, summary, report,
report_location, blocked_reason`. Each node returns only the keys it changed —
LangGraph merges them.

**Conditional edge**: `route_after_guard` sends blocked inputs to a dead-end node —
this is guardrails wired INTO the graph, not bolted on outside.

## The ReAct pattern (the researcher node)
`create_react_agent(llm, tools)` builds the classic loop:
**Re**ason ("I need recent data → I should search the web") → **Act** (call
`web_search`) → observe result → reason again → ... → final answer.
`recursion_limit=12` stops runaway loops (an agent stuck calling tools forever —
a real production failure mode).

## Why multiple agents instead of one big prompt?
Each role gets a small, focused prompt → better quality, easier debugging (you
see in LangSmith exactly which step failed), and independent iteration (improve
the writer without touching the researcher).

## What breaks without it
One mega-prompt doing plan+search+write produces shallow reports, can't loop over
tools properly, and gives you zero visibility into WHERE it went wrong.
