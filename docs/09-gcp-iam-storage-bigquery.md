# GCP Foundations — IAM, Cloud Storage, BigQuery

## Projects & the gcloud CLI
Everything in GCP lives inside a **project** (billing, permissions, resources).
```bash
gcloud auth login
gcloud projects create agentic-research-<yourname> --name="Agentic Research"
gcloud config set project agentic-research-<yourname>
gcloud services enable storage.googleapis.com bigquery.googleapis.com \
  compute.googleapis.com container.googleapis.com artifactregistry.googleapis.com
```
**Do this first:** Billing → Budgets & alerts → budget ₹500 with email alerts.

## IAM — who can do what
- **Principal**: who (a user, or a **service account** = identity for programs)
- **Role**: a bundle of permissions (`roles/storage.objectAdmin`)
- **Least privilege**: grant the smallest role that works — never Owner/Editor to apps.

```bash
gcloud iam service-accounts create agentic-app --display-name "Agentic app"
SA=agentic-app@$(gcloud config get-value project).iam.gserviceaccount.com
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
  --member=serviceAccount:$SA --role=roles/storage.objectAdmin
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
  --member=serviceAccount:$SA --role=roles/bigquery.dataEditor
```
**Best practice we follow:** attach the service account TO the VM/GKE workload
(`--service-account=$SA` at VM creation). Google injects credentials
automatically (metadata server → Application Default Credentials) — our code
(`storage.Client()`, `bigquery.Client()`) picks them up with **no JSON key file
ever downloaded**. Downloaded keys are the #1 cloud-security mistake.

## Cloud Storage (GCS) — object storage
Buckets hold objects (files) at global-unique names; used by
[save_report](../services/mcp-tools-server/server.py) and rag-service uploads.
```bash
gcloud storage buckets create gs://agentic-reports-<yourname> --location=asia-south1
```
Set `GCS_BUCKET=agentic-reports-<yourname>` in `.env` → code switches from local
`reports/` folder to the bucket automatically (graceful-fallback pattern).

## BigQuery — the analytics warehouse
Serverless SQL over huge data; our
[TimingAnalyticsMiddleware](../services/agent-service/app/middlewares.py) streams
one row per request via [analytics.py](../services/agent-service/app/analytics.py).
```bash
bq mk agent_analytics
bq mk --table agent_analytics.requests \
  request_id:STRING,ts:TIMESTAMP,method:STRING,path:STRING,status:INT64,duration_ms:FLOAT64,client:STRING
```
Set `GCP_PROJECT_ID` in `.env`, make some requests, then:
```sql
SELECT path, COUNT(*) requests, ROUND(AVG(duration_ms)) avg_ms,
       COUNTIF(status >= 400) errors
FROM agent_analytics.requests GROUP BY path ORDER BY requests DESC;
```

## What breaks without it
Without IAM discipline: one leaked Editor key = attacker owns your project.
Without BigQuery: "how slow is the agent, who uses it, what fails?" has no answer.
