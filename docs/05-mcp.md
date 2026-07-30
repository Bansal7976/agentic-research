# MCP — Model Context Protocol

## What is MCP?
MCP is an open standard (created by Anthropic, adopted industry-wide) for
connecting AI agents to tools and data. Think of it as **USB for AI tools**:

- Without MCP: every app hand-wires its own tool functions; nothing is reusable.
- With MCP: tools live in a **server**; ANY MCP-compatible client (our agent,
  Claude Desktop, Cursor, other frameworks) can discover and call them.

Roles: **Server** exposes tools/resources · **Client** (inside the agent app)
connects to servers, lists tools, calls them.

## Our MCP server ([mcp-tools-server](../services/mcp-tools-server/server.py))
A separate microservice on port 8100 built with `FastMCP` (official MCP Python
SDK v1; pinned `<2` because our client library supports v1) — each tool is just a
decorated Python function; the docstring becomes the tool description the LLM
reads when deciding what to call:

| Tool | What it does |
|---|---|
| `web_search` | Tavily (if key set) or free DuckDuckGo search |
| `wiki_lookup` | Wikipedia summary + URL |
| `arxiv_search` | Academic papers: title, authors, abstract |
| `save_report` | Writes final report to Cloud Storage (or local `reports/`) |

Transport: `streamable-http` — the client connects over the network to
`http://mcp-tools:8100/mcp`, which is why it works across containers and pods.

## Our MCP client ([main.py](../services/agent-service/app/main.py))
```python
client = MultiServerMCPClient({"research_tools":
    {"transport": "streamable_http", "url": settings.mcp_server_url}})
tools = await client.get_tools()          # discovers tools automatically
```
`langchain-mcp-adapters` converts every discovered MCP tool into a LangChain tool,
which we hand straight to the LangGraph researcher. **The agent never hardcodes
tool logic** — add a tool to the server, restart, and the agent can use it. Zero
agent-code changes.

## Try it
Start only the MCP server, then watch agent-service logs on boot:
`Agent graph ready with 4 MCP tools`.

## What breaks without it
Tools would be locked inside agent-service: not reusable by other agents, not
independently deployable/scalable, and every tool change would mean redeploying
the whole agent. MCP is also simply the industry direction — worth knowing deeply.
