# MLOps — CI/CD, Monitoring & the Full Loop

## MLOps fundamentals — the 3 C's

Regular DevOps has two loops: **CI** (Continuous Integration — test every code
change) and **CD** (Continuous Deployment — ship the ones that pass). MLOps
adds a third:

| | Triggered by | Checks/does | Classic tool | Our tool |
|---|---|---|---|---|
| **CI** — Continuous Integration | a code change | lint, unit tests | GitHub Actions, Jenkins | GitHub Actions (`test` job) |
| **CD** — Continuous Deployment | CI passing | build, push, roll out | GitHub Actions, ArgoCD | GitHub Actions (`deploy` job) |
| **CT** — Continuous Training | new data / a schedule / a drift alert | retrain the model, re-validate it | Vertex AI Pipelines, Kubeflow, Airflow | **we don't have this — see below** |

**Where the *actual* difference from DevOps is** (deployment mechanics
themselves — Docker, Kubernetes, rollback — are genuinely identical):
1. **What can trigger a deploy** — in DevOps only code changes do. In MLOps, a
   *model* or *prompt* can change behavior with zero code changes.
2. **What "test" means** — a unit test is deterministic (`assert x == 5`).
   You can't `==`-test whether an LLM's report is "good," so MLOps adds a new
   kind of gate: **evals** (LLM-as-judge scoring — [doc 07](07-langsmith-evaluation.md)).
3. **Failure is silent** — bad code usually crashes loudly. A worse prompt
   still returns `200 OK` with valid JSON — nothing "breaks," the *quality*
   just quietly drops. This is exactly what the eval gate exists to catch.
4. **Model drift** — the classic-ML version of "things got worse without a
   code change": the live data your model sees slowly stops resembling its
   training data, and accuracy decays. The LLM-world analogue is *prompt/eval
   drift* — a model provider updates their model, or usage patterns shift,
   and your eval scores start slipping even though you changed nothing.

## MLOps vs LLMOps — which one is this project?

**Strictly, this project does LLMOps, not full MLOps.** The difference:
classic MLOps assumes *you* are training a model — so it needs a training
pipeline, a model registry, and CT. LLMOps means you're consuming an
already-trained model as a hosted service (Gemini via Vertex AI) — you never
train anything, so that whole axis disappears. What's left (and what we
actually built) is CI + CD + evals + monitoring, applied to *prompts and
agent logic* instead of model weights.

## How Continuous Training would work, if we DID train our own model

We don't do this — but understanding it makes it obvious *why* we don't need
it, and it's the piece most MLOps job descriptions actually mean. If this
project used a custom-trained model instead of hosted Gemini, Vertex AI's
platform (not just the Gemini API surface used in [doc 02](02-langchain-gemini.md))
would provide every stage:

```
New data lands (BigQuery table / GCS bucket) or a schedule fires
                          │
        Vertex AI Pipelines (a managed Kubeflow/TFX pipeline runner)
        orchestrates the steps below as one automated pipeline
                          │
  1. Vertex AI Training  — rents GPU/TPU for the training run only,
     executes your training script, outputs a model artifact
                          │
  2. Evaluation step     — scores the new model against a held-out
     validation set (accuracy/F1 for classic ML; LLM-as-judge for LLMs)
                          │
  3. Vertex AI Model Registry — if scores clear a threshold, the new
     model version is registered (v1, v2, v3...) with full lineage:
     which data, which pipeline run, which metrics produced it
                          │
  4. Vertex AI Endpoint  — the new version is deployed behind a managed
     serving endpoint, often with traffic splitting (10% canary → 100%)
                          │
  5. Vertex AI Model Monitoring — watches live prediction inputs/outputs
     for drift vs. the training data; a drift alert can re-trigger step 1
                          │
                    (loop back to the top)
```

Notice the shape: **Vertex AI Model Registry is the training-world's
equivalent of our Artifact Registry** (a versioned catalog — models instead
of Docker images), and **Vertex AI Endpoints are the equivalent of our GKE
Deployment + Service** (managed serving with rolling/canary traffic, instead
of us running the containers ourselves).

## What we actually did instead, and why that's a legitimate choice

- **No training pipeline, no Vertex AI Training job** — Gemini arrives
  pre-trained; we only ever *call* it ([doc 02](02-langchain-gemini.md)).
- **No Vertex AI Model Registry** — our "model version" is just a config
  string (`GEMINI_MODEL=gemini-3.6-flash` in `.env` / the K8s Secret). Change
  it, redeploy, done — no artifact to version.
- **Our registry-equivalent is LangSmith experiments** — instead of tracking
  *model weight versions*, we track *prompt/graph versions* (which live in
  git) against eval scores, which is the correct unit of versioning for an
  LLMOps project.
- **Our drift-monitoring-equivalent is the eval gate re-run** — instead of
  Vertex AI Model Monitoring watching for statistical drift automatically, we
  re-run `evals/run_evals.py` when we suspect prompt/model drift and compare
  scores across experiments by hand. (An automated nightly eval run + Slack
  alert on score drop would be the natural next step to make this closer to
  real CT-style monitoring.)

## Putting it together — our actual loop

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
