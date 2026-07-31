# 📚 TECHNOLOGIES.md — Master Guide to Everything in This Project

New to this repo? Read this file, then dive into the numbered docs for depth.
Each doc explains: what the technology is, why THIS project needs it, exactly
where it lives in the code, and what would break without it.

> 🆕 **Never used a cloud before, or unsure what "project," "region," or
> "API key" even mean?** Start with [00 — Google Cloud Basics](00-google-cloud-basics.md)
> first — it also has a jargon-buster glossary for every short technical word
> used across these docs (API, container, middleware, load balancer, etc.).

| # | Doc | Technology | One-line role here |
|---|---|---|---|
| 00 | [Google Cloud Basics](00-google-cloud-basics.md) | Cloud concepts, GCP fundamentals | Read this first if any of the below is unfamiliar |
| 01 | [FastAPI & Middlewares](01-fastapi-and-middlewares.md) | FastAPI, Pydantic, middlewares | The API layer; auth, rate-limit, request-IDs, analytics on every request |
| 02 | [LangChain & Gemini](02-langchain-gemini.md) | LangChain, Gemini API | Talking to the LLM: prompts, structured output, tools |
| 03 | [RAG](03-rag.md) | Embeddings, Chroma | Your documents → searchable knowledge the agent can cite |
| 04 | [LangGraph Agents](04-langgraph-agents.md) | LangGraph, ReAct | The multi-agent brain: Planner → Researcher → Summarizer → Writer |
| 05 | [MCP](05-mcp.md) | Model Context Protocol | Tools as a separate, reusable server the agent discovers |
| 06 | [Guardrails](06-guardrails.md) | Input/output guards | Blocking prompt injection; scrubbing PII from reports |
| 07 | [LangSmith](07-langsmith-evaluation.md) | Tracing, LLM-as-judge | Seeing every agent step; measuring quality with numbers |
| 08 | [Docker & Microservices](08-docker-microservices.md) | Docker, compose | 4 services, one command, identical everywhere |
| 09 | [GCP Foundations](09-gcp-iam-storage-bigquery.md) | IAM, GCS, BigQuery | Cloud security, report storage, usage analytics |
| 10 | [VM + nginx](10-vm-nginx-deployment.md) | Compute Engine, nginx | First deployment: one VM, one public door |
| 11 | [Kubernetes](11-kubernetes-gke.md) | GKE, LB, HPA | Self-healing, autoscaling, zero-downtime deploys |
| 12 | [MLOps](12-mlops-cicd-monitoring.md) | GitHub Actions, monitoring | Code → tests → evals → build → deploy → monitor, automatically |

---

## The life of one request (how EVERYTHING connects)

`POST http://<ip>/api/agent/research {"topic": "Impact of AI on Indian jobs"}`

1. **GCP Load Balancer / firewall** admits traffic only on port 80 → **nginx**
   checks its edge rate limit, then reverse-proxies to `agent-service` (round-robin
   across K8s replicas). *(docs 10, 11)*
2. **Middlewares** fire in order: CORS → request gets ID `a1b2c3d4` → `X-API-Key`
   verified → per-IP rate limit checked → timer starts. *(doc 01)*
3. **FastAPI** validates the body against the Pydantic schema. *(doc 01)*
4. **LangGraph** starts. **Input guardrail** scans the topic — injection attempts
   die here, costing zero tokens. *(docs 04, 06)*
5. **Planner** (Gemini, structured output) → 3 sub-questions. *(doc 02)*
6. **Researcher** (ReAct agent) loops: calls `web_search`, `wiki_lookup`,
   `arxiv_search` on the **MCP tools server**, plus `search_uploaded_docs` on the
   **rag-service** (embeddings + Chroma similarity search). *(docs 03, 04, 05)*
7. **Summarizer** compresses findings → **Writer** produces the markdown report. *(doc 04)*
8. **Output guardrail** scrubs PII → **save** node calls MCP `save_report` →
   report lands in **Cloud Storage**. *(docs 06, 09)*
9. Response returns through the middlewares: timer stops, one row streams to
   **BigQuery** (`request_id, path, status, duration_ms…`). *(docs 01, 09)*
10. The entire run — every prompt, tool call, token count — is visible as one
    trace in **LangSmith**, tagged with `a1b2c3d4`. *(doc 07)*

Meanwhile, forever: **Cloud Monitoring** pings `/health`; the **CI/CD pipeline**
guards every code change with lint + tests + eval scores before rolling new
images onto the cluster. *(doc 12)*

One request touched: nginx, load balancing, middlewares, FastAPI, guardrails,
LangGraph, Gemini, MCP, RAG, Cloud Storage, BigQuery, LangSmith, Kubernetes,
IAM (the pod's service account authorized the GCS/BQ writes) — every technology
in the stack, doing a real job.
