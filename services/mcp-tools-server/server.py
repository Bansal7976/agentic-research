"""MCP server exposing research tools to any MCP client (our agent-service).

Runs as its own microservice on port 8100 using the streamable-http transport,
so clients connect over the network at http://<host>:8100/mcp
"""
import logging
import os
import pathlib
import re
import time

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

# local runs read the repo-root .env (walk upwards to find it);
# in Docker/K8s there is no .env file — env comes from compose/secrets instead
for _parent in pathlib.Path(__file__).resolve().parents:
    if (_parent / ".env").exists():
        load_dotenv(_parent / ".env")
        break

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-tools")

# mcp is pinned <2 because langchain-mcp-adapters (our client) supports SDK v1.
# containers/pods reach us via hostnames like "mcp-tools", hence no DNS-rebinding check.
mcp = FastMCP(
    "research-tools",
    host="0.0.0.0",
    port=8100,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


@mcp.tool()
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for a query. Returns titles, URLs and snippets."""
    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
    try:
        if tavily_key:
            from tavily import TavilyClient

            res = TavilyClient(tavily_key).search(query, max_results=max_results)
            items = [
                f"- {r['title']}\n  URL: {r['url']}\n  {r.get('content', '')[:300]}"
                for r in res.get("results", [])
            ]
        else:  # free fallback, no API key needed
            from ddgs import DDGS

            items = [
                f"- {r['title']}\n  URL: {r['href']}\n  {r.get('body', '')[:300]}"
                for r in DDGS().text(query, max_results=max_results)
            ]
        return "\n".join(items) or "No results found."
    except Exception as e:
        return f"web_search failed: {e}"


@mcp.tool()
def wiki_lookup(topic: str) -> str:
    """Get a factual summary of a topic from Wikipedia."""
    import wikipedia

    try:
        page = wikipedia.page(topic, auto_suggest=True)
        return f"{wikipedia.summary(topic, sentences=8, auto_suggest=True)}\nURL: {page.url}"
    except Exception as e:
        return f"wiki_lookup failed: {e}"


@mcp.tool()
def arxiv_search(query: str, max_results: int = 3) -> str:
    """Search arXiv for academic papers. Returns title, authors, summary, URL."""
    import arxiv

    try:
        results = arxiv.Client().results(arxiv.Search(query=query, max_results=max_results))
        items = [
            f"- {r.title} ({r.published.year})\n"
            f"  Authors: {', '.join(a.name for a in r.authors[:3])}\n"
            f"  URL: {r.entry_id}\n  {r.summary[:300]}"
            for r in results
        ]
        return "\n".join(items) or "No papers found."
    except Exception as e:
        return f"arxiv_search failed: {e}"


@mcp.tool()
def save_report(topic: str, content: str) -> str:
    """Save a finished markdown report. Returns its gs:// URL or local path."""
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:60]
    fname = f"{slug}-{int(time.time())}.md"
    bucket_name = os.getenv("GCS_BUCKET", "").strip()
    if bucket_name:
        from google.cloud import storage

        client = storage.Client(project=os.getenv("GCP_PROJECT_ID") or None)
        blob = client.bucket(bucket_name).blob(f"reports/{fname}")
        blob.upload_from_string(content, content_type="text/markdown")
        return f"gs://{bucket_name}/reports/{fname}"
    # local fallback when GCP is not configured yet
    out = pathlib.Path("reports")
    out.mkdir(exist_ok=True)
    path = out / fname
    path.write_text(content, encoding="utf-8")
    return str(path.resolve())


if __name__ == "__main__":
    logger.info("Starting MCP tools server on :8100/mcp")
    mcp.run(transport="streamable-http")
