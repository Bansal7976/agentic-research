# Docker & Microservice Architecture

## Why microservices?
We split the system into 4 independently deployable pieces:

| Service | Port | Responsibility |
|---|---|---|
| gateway (nginx) | 80 | Public entry, routing, rate limiting, static UI |
| agent-service | 8000 | API + LangGraph agents + guardrails |
| rag-service | 8001 | Documents, embeddings, vector search |
| mcp-tools-server | 8100 | Tools over MCP |

Benefits we actually use: **independent scaling** (K8s runs 2–5 agent replicas
but 1 MCP replica), **fault isolation** (rag-service down → research still works,
agent's doc tool just reports unavailable), **clear contracts** (HTTP/MCP between
services). Honest trade-off: more moving parts — for a small team a monolith is
often the right call; we do microservices here to LEARN them.

## What is Docker?
A container packages your app + Python + dependencies into one **image** that
runs identically on your laptop, a VM, or Kubernetes — the end of "works on my
machine". Unlike a VM it shares the host kernel, so it starts in seconds.

Each service has a [Dockerfile](../services/agent-service/Dockerfile):
```dockerfile
FROM python:3.12-slim        # base image (layer 1)
COPY requirements.txt .      # copy deps list first...
RUN pip install ...          # ...so this heavy layer is CACHED unless deps change
COPY . .                     # app code changes often -> cheap top layer
CMD ["uvicorn", ...]
```
Layer-order is deliberate: edit app code → rebuild takes seconds, not minutes.

## docker-compose ([deploy/docker-compose.yml](../deploy/docker-compose.yml))
Compose runs all 4 containers on one private network where **service names are
hostnames** — agent-service reaches `http://mcp-tools:8100/mcp` by name. Only
nginx publishes a port (80) to the outside; the backends are unreachable
directly. Named volume `rag-data` keeps the vector store across restarts.

```bash
docker compose -f deploy/docker-compose.yml up --build   # → http://localhost
```

## What breaks without it
Without containers, the VM/K8s deployment story becomes "manually install Python
and pray". Without the compose network model, every service would need public
ports — a security hole nginx currently prevents.
