# Deployment 2 — Kubernetes on GKE

## Why Kubernetes?
The VM's problems: crash = downtime, scaling = buy bigger VM, deploy = downtime.
Kubernetes (K8s) runs containers across a **cluster** and continuously makes
reality match your declared desire: "2 agent replicas, always" — pod dies, K8s
replaces it; node dies, pods move. **Declarative, self-healing infrastructure.**

## Core objects (all used in [deploy/k8s/](../deploy/k8s/))
| Object | Meaning | Ours |
|---|---|---|
| Pod | Smallest unit: running container(s) | created for you |
| Deployment | "Run N replicas of this image, roll updates gradually" | one per service ([services.yaml](../deploy/k8s/services.yaml)) |
| Service | Stable internal DNS name + load balancing across pods | `agent-service`, `rag-service`, `mcp-tools` |
| Service (LoadBalancer) | GCP provisions a real external IP | `gateway` ([gateway.yaml](../deploy/k8s/gateway.yaml)) |
| ConfigMap / Secret | Config / credentials injected as env or files | nginx.conf / `app-secrets` |
| Namespace | Folder isolating our app | `agentic-research` |
| HPA | Autoscaler: more pods when CPU > 70% | [hpa.yaml](../deploy/k8s/hpa.yaml) |
| readinessProbe | Only send traffic to pods whose `/health` responds | on agent-service |

Note the continuity: in compose, `http://mcp-tools:8100` worked via the compose
network; in K8s the SAME hostname works because the Service is named `mcp-tools`.

## Deploy (Phase 11 — the expensive week)
```bash
# 1. Images → Artifact Registry
gcloud artifacts repositories create agentic --repository-format=docker --location=asia-south1
gcloud auth configure-docker asia-south1-docker.pkg.dev
for s in agent-service rag-service mcp-tools-server; do
  docker build -t asia-south1-docker.pkg.dev/$PROJECT/agentic/${s%-server}:latest services/$s
  docker push asia-south1-docker.pkg.dev/$PROJECT/agentic/${s%-server}:latest
done

# 2. Cluster (Autopilot = Google manages nodes; pay per pod)
gcloud container clusters create-auto agentic-cluster --region=asia-south1
gcloud container clusters get-credentials agentic-cluster --region=asia-south1

# 3. Apply manifests (fix REGION/PROJECT_ID in services.yaml; create secrets.yaml first)
kubectl apply -f deploy/k8s/namespace.yaml -f deploy/k8s/secrets.yaml
kubectl apply -f deploy/k8s/services.yaml -f deploy/k8s/gateway.yaml -f deploy/k8s/hpa.yaml

kubectl -n agentic-research get pods -w            # watch them come alive
kubectl -n agentic-research get svc gateway        # EXTERNAL-IP → open in browser
```

## Experiments that teach the most
```bash
kubectl -n agentic-research delete pod -l app=agent-service   # watch self-healing
kubectl -n agentic-research scale deploy/agent-service --replicas=4
kubectl -n agentic-research rollout restart deploy/agent-service  # zero-downtime roll
kubectl -n agentic-research logs -l app=agent-service -f
```

## ⚠️ Teardown (do this the same week)
```bash
gcloud container clusters delete agentic-cluster --region=asia-south1
```
Screenshot everything first — cluster running, pods, external IP, HPA — for the
README. The cluster is the biggest cost in the whole project.
