# MLOps — CI/CD, Monitoring & the Full Loop

## What MLOps means for an LLM app
Classic DevOps ships code. MLOps also ships **model behavior** — prompts, graph
logic, tool sets — and behavior can regress silently without any test failing.
So the pipeline needs BOTH kinds of checks:

```
        code change (prompt tweak, new tool, refactor)
                          │
   ┌── CI: ruff lint ── pytest (guardrails/auth/API) ── LangSmith evals (quality gate)
   │                                                            │
   └── fail = blocked                    scores below threshold = blocked
                          │ pass
   CD: docker build ×3 → push to Artifact Registry → kubectl apply + rollout
                          │
   Monitor: Cloud Monitoring (infra) + LangSmith (AI quality) + BigQuery (usage)
                          │
   findings feed the next change ──────────────► (loop forever)
```

## Our pipeline ([.github/workflows/ci-cd.yml](../.github/workflows/ci-cd.yml))
- **test job** (every push): lint + unit tests. The eval gate
  ([evals/run_evals.py](../evals/run_evals.py)) plugs in here — see [doc 07](07-langsmith-evaluation.md).
- **deploy job** (manual "Run workflow" button): authenticates to GCP with a
  service-account secret, builds and pushes all three images (tagged `latest` +
  commit SHA for rollback), then applies manifests and restarts deployments —
  K8s rolls pods gradually with zero downtime.
- Setup: repo secrets `GCP_SA_KEY` (JSON of a deploy service account with
  Artifact Registry Writer + Kubernetes Engine Developer) and `GCP_PROJECT_ID`.

## Monitoring — three layers, three questions
| Layer | Tool | Question it answers |
|---|---|---|
| Infrastructure | Cloud Monitoring | Is it up? CPU? 5xx rate? |
| AI quality | LangSmith | Are reports good? Which step is slow/failing? |
| Business/usage | BigQuery | Who uses it, how often, how slow, what errors? |

Cloud Monitoring quick-start: Console → Monitoring → create an **uptime check**
on `http://<EXTERNAL-IP>/health` + an **alerting policy** (email on failure);
dashboards for GKE CPU/memory come built-in. All three layers join on
`request_id` — one ID traces a request across logs, traces, and analytics.

## Versioning & rollback
- Images tagged with git SHA → `kubectl set image ...:<old-sha>` = instant rollback.
- Prompts live in code → git history IS prompt history; LangSmith experiments
  record which prompt version scored what.

## What breaks without it
Manual deploys (scp + pray), a prompt "improvement" that quietly makes reports
worse for weeks, and outages you learn about from users instead of alerts.
