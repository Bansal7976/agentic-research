# Deployment 1 — Compute Engine VM + nginx

First real deployment: one Linux VM running the whole docker-compose stack, with
nginx as the single public door. This is the classic "one server" architecture —
learn it before Kubernetes abstracts it away.

## What is a VM?
Compute Engine rents you a virtual Linux machine. **Machine type** = CPU/RAM
(e2-small: 2 vCPU, 2GB — enough here). You pay per second WHILE IT RUNS —
**stop it when idle**.

## Create everything (from your laptop)
```bash
# Firewall: allow web traffic to instances tagged http-server
gcloud compute firewall-rules create allow-http \
  --allow tcp:80,tcp:443 --target-tags=http-server

SA=agentic-app@$(gcloud config get-value project).iam.gserviceaccount.com
gcloud compute instances create agentic-vm \
  --zone=asia-south1-a --machine-type=e2-small \
  --image-family=debian-12 --image-project=debian-cloud \
  --tags=http-server --service-account=$SA \
  --scopes=cloud-platform      # SA + scopes = keyless GCS/BigQuery access (doc 09)

gcloud compute ssh agentic-vm --zone=asia-south1-a
```
On the VM, run [deploy/vm/setup.sh](../deploy/vm/setup.sh) (installs Docker,
clones repo, `.env` setup, compose up). Then open `http://<EXTERNAL_IP>/`.

**Security note:** ports 8000/8001/8100 are NOT in the firewall rule — backends
are only reachable through nginx on port 80. Firewall = first guardrail.

## nginx — the traffic manager ([nginx.conf](../gateway/nginx/nginx.conf))
- **Reverse proxy**: clients see ONE server; nginx forwards `/api/agent/*` →
  agent-service:8000, `/api/rag/*` → rag-service:8001. Backends stay hidden.
- **Load balancing**: an `upstream` block with multiple servers round-robins
  between them (on K8s, replicas make this real).
- **Edge rate limiting**: `limit_req` rejects floods before they touch Python —
  cheaper than doing it in the app (which still has its own layer — defense in depth).
- **Static serving**: nginx serves the frontend HTML itself; Python never sees
  those requests.
- `proxy_read_timeout 300s` because agent research legitimately takes minutes —
  the #1 cause of mysterious 504s with LLM apps.

## Operating the VM
```bash
gcloud compute instances stop agentic-vm --zone=asia-south1-a    # 💰 when done
gcloud compute instances start agentic-vm --zone=asia-south1-a
docker compose -f deploy/docker-compose.yml logs -f agent-service  # on the VM
```

## Limits of this setup (why Phase 11 exists)
One VM = single point of failure, manual scaling, downtime on every deploy.
Kubernetes fixes exactly these three problems.
