"""agent-service: the public API in front of the LangGraph agent system."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .middlewares import (
    APIKeyMiddleware,
    RateLimitMiddleware,
    RequestIDMiddleware,
    TimingAnalyticsMiddleware,
)
from .schemas import ResearchRequest, ResearchResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent-service")


async def try_build_graph(app: FastAPI) -> None:
    """Connect to the MCP tools server and compile the agent graph."""
    from langchain_mcp_adapters.client import MultiServerMCPClient

    from .graph import build_graph

    client = MultiServerMCPClient(
        {"research_tools": {"transport": "streamable_http", "url": settings.mcp_server_url}}
    )
    tools = await client.get_tools()
    app.state.graph = await build_graph(tools)
    logger.info("Agent graph ready with %d MCP tools", len(tools))


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.graph = None
    try:
        await try_build_graph(app)
    except Exception as e:  # boot anyway; we retry on first request
        logger.warning("MCP server not reachable yet (%s). Will retry on demand.", e)
    yield


app = FastAPI(title="agent-service", version="1.0.0", lifespan=lifespan)

# Added innermost-first; requests actually flow: CORS -> RequestID -> APIKey -> RateLimit -> Timing
app.add_middleware(TimingAnalyticsMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(APIKeyMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "agent-service", "graph_ready": app.state.graph is not None}


@app.post("/research", response_model=ResearchResponse)
async def research(body: ResearchRequest, request: Request):
    if app.state.graph is None:
        try:
            await try_build_graph(app)
        except Exception as e:
            raise HTTPException(
                503, f"Agent not ready: MCP tools server unreachable ({e})"
            ) from e

    request_id = getattr(request.state, "request_id", "-")
    result = await app.state.graph.ainvoke(
        {"topic": body.topic, "max_subquestions": body.max_subquestions},
        config={"run_name": "research", "metadata": {"request_id": request_id}},
    )
    if result.get("blocked_reason"):
        raise HTTPException(400, result["report"])
    return ResearchResponse(
        topic=body.topic,
        report=result.get("report", ""),
        sources=result.get("sources", []),
        report_location=result.get("report_location"),
        request_id=request_id,
    )
