# LangSmith — Tracing, Evaluation & Monitoring

LangSmith is observability + quality measurement for LLM apps ("the MLOps layer
for agents"). Free tier at [smith.langchain.com](https://smith.langchain.com).

## 1. Tracing
Set 3 env vars ([config.py](../services/agent-service/app/config.py) exports them)
and every LangChain/LangGraph call is auto-recorded:
```
LANGSMITH_TRACING=true  LANGSMITH_API_KEY=...  LANGSMITH_PROJECT=agentic-research
```
Open a trace and you SEE the whole graph run: guard_input → planner (exact prompt
+ sub-questions) → researcher (every tool call + result) → writer, with per-step
latency and token counts. We attach our `request_id` as metadata
([main.py](../services/agent-service/app/main.py)), so one ID links the nginx log,
BigQuery row, and LangSmith trace — end-to-end debugging.

## 2. Evaluation ([evals/run_evals.py](../evals/run_evals.py))
"Looks good to me" is not engineering. The eval flow:

1. **Dataset** — 5 fixed research topics uploaded to LangSmith (`research-topics-v1`).
2. **Target** — calls our real API for each topic.
3. **LLM-as-judge** — Gemini grades every report 0–1 on three criteria:
   *relevance* (answers the topic?), *structure* (summary/sections/sources?),
   *groundedness* (claims backed by cited URLs?). Structured output forces a
   `{score, reasoning}` shape.
4. **Experiment** — results appear in LangSmith; change a prompt, re-run, and
   compare experiments side-by-side. Numbers, not vibes.

```bash
python evals/run_evals.py   # stack must be running; see README
```

**MLOps connection:** the CI pipeline ([ci-cd.yml](../.github/workflows/ci-cd.yml))
notes where this becomes a quality gate — a prompt change that drops the average
score below a threshold fails the build, exactly like failing unit tests.

## 3. Monitoring
The LangSmith dashboard charts request volume, error rate, latency percentiles
(P50/P99), token usage and cost over time — per project. Pair with Cloud
Monitoring (infra-level) from [doc 12](12-mlops-cicd-monitoring.md): LangSmith
answers "is the AI good?", Cloud Monitoring answers "is the service up?".

## What breaks without it
An agent fails on step 4 of 7 and all you have is a bad final answer with no idea
why. Prompt changes ship on gut feeling and silently make quality worse.
