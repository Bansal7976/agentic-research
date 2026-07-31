# Google Cloud Basics — Start Here If You've Never Used a Cloud Before

Everything else in `docs/` assumes you already know what a "project," a
"region," or "the console" means. This doc fills that gap. Read this first,
then go to [TECHNOLOGIES.md](TECHNOLOGIES.md) for the technology-by-technology
tour. If a word anywhere in these docs confuses you, check the
[glossary](#jargon-buster-every-short-word-explained) at the bottom first.

## 1. What "the cloud" actually is

There is no actual cloud. "The cloud" means **someone else's computers**,
sitting in a data center, that you rent by the second/hour/month instead of
buying, wiring, and maintaining hardware yourself. Google, Amazon, and
Microsoft each run huge data centers full of servers and rent out pieces of
them — that's Google Cloud (GCP), AWS, and Azure.

What you get for renting instead of owning:
- **No upfront cost** — a server that would cost you ₹50,000 to buy, you can
  rent for a few rupees an hour, and stop paying the moment you're done ([doc 10](10-vm-nginx-deployment.md)).
- **Elastic scale** — need 10x the servers for one hour of traffic? Ask for
  them, pay for that hour, give them back ([doc 11](11-kubernetes-gke.md)).
- **Managed services** — instead of installing and patching a database
  yourself, GCP hands you one that's already running and backed up
  (BigQuery, Cloud Storage — [doc 09](09-gcp-iam-storage-bigquery.md)).

### The three service "shapes" (you'll see these terms everywhere)
| Shape | You manage | Google manages | Example we use |
|---|---|---|---|
| **IaaS** (Infrastructure as a Service) | OS, runtime, your app | Physical hardware, network | Compute Engine (our VM, doc 10) |
| **PaaS** (Platform as a Service) | Just your app/container | OS, scaling, patching | GKE Autopilot, Cloud Run (doc 11, guide §11) |
| **SaaS-like managed data services** | Nothing but your data/queries | Everything | BigQuery, Cloud Storage (doc 09) |

Our project deliberately touches all three — that's why it's a good learning
project: you feel the difference between "I manage the OS" (VM) and "I never
think about servers" (BigQuery) in the same afternoon.

## 2. The resource hierarchy — where everything lives

```
Organization (a company's Google Workspace domain — we don't have one)
   └── Folder (optional grouping — we don't use one)
         └── Project  ← agentic-research-81536, EVERYTHING below lives here
               ├── Compute Engine VMs
               ├── GKE clusters
               ├── Cloud Storage buckets
               ├── BigQuery datasets
               ├── Service accounts (identities)
               └── ... every other resource
```

**Project** is the real unit that matters for a solo learner/small team: it's
a billing boundary, a permissions boundary, and a namespace, all at once.
`agentic-research-81536` has three names:
- **Project name** — human label, `Agentic Research` (can change)
- **Project ID** — globally unique, permanent, used in commands/URLs —
  `agentic-research-81536` (the `-81536` suffix got appended because the
  plain name was already taken by someone, somewhere in the world)
- **Project number** — an internal numeric ID Google assigns, rarely typed by hand

**Rule of thumb we followed:** one project per learning experiment. Delete
the project at the end ([ROADMAP.md §6](../ROADMAP.md)) and every resource
inside it — buckets, clusters, service accounts, everything — goes with it.
No hunting for stray bills.

## 3. Regions and zones — *where* your resources physically run

- **Region** = a geographic area with its own data centers, e.g.
  `asia-south1` = Mumbai. We picked this one so latency to India is low and
  data stays in India (relevant for real companies under data-residency rules).
- **Zone** = one physical data center inside a region, e.g. `asia-south1-a`.
  Our VM and GKE cluster both live in this exact zone.
- **Multi-region / global** resources (like Cloud Storage's location setting,
  or our Vertex AI `location: global`) aren't pinned to one data center —
  Google routes to whichever is best, trading a little control for more
  resilience.

Why this matters practically: a resource in `asia-south1-a` can talk to
another resource in the same zone over Google's internal network — fast,
free, and (in our case) how the GKE nodes talk to the Artifact Registry
image store. Cross-region traffic is slower and can cost more.

## 4. The GCP Console — a 2-minute tour

[console.cloud.google.com](https://console.cloud.google.com) is the web UI.
Everything we did by `gcloud` command, you can also click through here:
- **Top project switcher** — confirms which project you're "in" (always
  check this first; the wrong project = looking at nothing, or worse,
  billing the wrong account)
- **☰ hamburger menu (left)** — every product GCP offers, organized by
  category (Compute, Storage, Databases, AI/ML, Networking...)
- **Cloud Shell (`>_` icon, top right)** — a free temporary Linux terminal
  with `gcloud` pre-installed, running in your browser — no local setup
- **Billing** — see spend, set budgets (we set a A$10 alert), view invoices
- **IAM & Admin** — who/what has access to what ([doc 09](09-gcp-iam-storage-bigquery.md))

We drove this whole project from the `gcloud` CLI instead of clicking through
the console, because commands are **repeatable and scriptable** — the exact
commands in [doc 10](10-vm-nginx-deployment.md) and [doc 11](11-kubernetes-gke.md)
are the "recipe," reusable any time.

## 5. Billing — how you actually get charged

- **Pay-as-you-go**: no fixed monthly fee. A stopped VM's disk still costs a
  little (storage), a deleted VM costs nothing. This is why we obsessively
  stop/delete things when done ([ROADMAP.md §6](../ROADMAP.md)).
- **Free tier**: GCP gives new accounts **$300 (or local-currency equivalent)
  of free credit for 90 days** — plus some products (BigQuery, Cloud Storage)
  have an *always-free* monthly quota on top of that.
  Small workloads like ours barely dent it.
- **Billing account vs project**: a billing account (yours might be in AUD,
  as ours is) is linked *to* one or more projects. The project is what gets
  charged; the billing account is where the invoice goes.
  `gcloud billing projects link <project> --billing-account=<id>` is the
  command that connects them (we ran this in Phase 9).
- **Budgets & alerts**: a budget doesn't stop spending — it just emails you
  at thresholds (we set 50/90/100% of A$10). Real spend control is stopping/
  deleting resources, which is why the teardown habit matters more than the
  alert itself.

## 6. "Enabling an API" vs "creating an API key" — commonly confused

Two different things share the word "API" and trip people up:

- **Enabling an API** = flipping a switch that lets your project use a
  Google Cloud *service* at all. Each product (Vertex AI, Cloud Storage,
  Kubernetes Engine...) has to be turned on per-project before you can use
  it: `gcloud services enable aiplatform.googleapis.com`. This is not a
  secret and can't be "leaked."
- **Creating an API key** = generating a secret credential string (like
  `AIza...`) that proves *who's calling*. This project deliberately avoids
  this pattern for GCP services — see the IAM section below and
  [docs/GUIDE-HINGLISH.md §8](GUIDE-HINGLISH.md) for the full walkthrough of
  why we used IAM identities instead.

## 7. Identity: `gcloud` CLI, and the two logins we used

The `gcloud` command-line tool needs to know **who you are** before it'll do
anything. Two separate logins matter, and confusing them is a classic
new-user trap:

| Command | What it authenticates | Used by |
|---|---|---|
| `gcloud auth login` | *You*, for running `gcloud`/`kubectl` commands yourself | Terminal commands (creating VMs, clusters, etc.) |
| `gcloud auth application-default login` | *Your code*, when it calls Google client libraries directly | Python scripts, local Docker containers |

Both open a browser window and use the same Google account, but they write
credentials to different places, and code only reads the second one. This is
the ADC (Application Default Credentials) file mentioned throughout
[doc 09](09-gcp-iam-storage-bigquery.md) and the Hinglish guide.

**Full identity/IAM model** (service accounts, roles, least privilege, why the
VM and GKE pods needed *zero* key files) is covered in depth in
[doc 09](09-gcp-iam-storage-bigquery.md) — read this basics doc first, then that one.

## 8. Where our project's pieces map to GCP products

| GCP Product | What it is, in one line | Doc |
|---|---|---|
| Compute Engine | Rentable virtual machines (IaaS) | [10](10-vm-nginx-deployment.md) |
| Google Kubernetes Engine (GKE) | Managed Kubernetes clusters | [11](11-kubernetes-gke.md) |
| Cloud Storage (GCS) | Object/file storage (buckets) | [09](09-gcp-iam-storage-bigquery.md) |
| BigQuery | Serverless SQL data warehouse | [09](09-gcp-iam-storage-bigquery.md) |
| Artifact Registry | Private storage for Docker images | [11](11-kubernetes-gke.md), [12](12-mlops-cicd-monitoring.md) |
| Vertex AI | Enterprise-grade access to Gemini models via IAM | [02](02-langchain-gemini.md) |
| IAM | Who/what can do what, project-wide | [09](09-gcp-iam-storage-bigquery.md) |
| Cloud Build | Builds Docker images on Google's servers, not yours | [11](11-kubernetes-gke.md) |

## 9. Same concepts, other clouds (so job listings don't confuse you)

| Concept | GCP | AWS | Azure |
|---|---|---|---|
| Rentable VM | Compute Engine | EC2 | Virtual Machines |
| Object storage | Cloud Storage | S3 | Blob Storage |
| Managed Kubernetes | GKE | EKS | AKS |
| Docker image registry | Artifact Registry | ECR | ACR |
| SQL data warehouse | BigQuery | Redshift | Synapse |
| Permissions system | IAM | IAM | Entra ID |

---

## Jargon buster — every short word, explained

A quick-reference table for terms used casually throughout `docs/01`–`docs/12`
and the code, in case one flies by without context.

| Term | Plain-English meaning |
|---|---|
| **API** | A defined way for one program to ask another program to do something (e.g. "give me the weather") over the network, usually using HTTP |
| **REST API / endpoint** | An API where each "thing you can ask for" has its own URL (`/research`, `/health`); "endpoint" = one such URL |
| **HTTP method** (GET/POST/etc.) | The *verb* of a request — GET = "give me data," POST = "here's data, do something with it" |
| **JSON** | A text format for structured data, `{"key": "value"}` — how our API sends/receives data |
| **YAML** | Another text format for structured data, indentation-based, used for config files (`docker-compose.yml`, Kubernetes manifests) |
| **CLI** | Command-Line Interface — a tool you type commands into (`gcloud`, `kubectl`, `git`) instead of clicking buttons |
| **SDK** | Software Development Kit — a bundle of libraries/tools a company gives you to use their product from code (the "Google Cloud SDK" is `gcloud` + friends) |
| **Environment variable** | A named value your OS/shell holds that a program can read at startup (our `.env` file defines these — `GOOGLE_API_KEY`, etc.) |
| **Container** | A packaged app + everything it needs to run, isolated from the host machine (see [doc 08](08-docker-microservices.md)) |
| **Image** | The frozen, shareable *template* a container is started from |
| **Repository (repo)** | A folder of code tracked by Git, with full history of every change |
| **Commit** | One saved snapshot of changes to a repo, with a message explaining why |
| **CI/CD** | Continuous Integration / Continuous Deployment — automatically testing and shipping code on every change ([doc 12](12-mlops-cicd-monitoring.md)) |
| **Service account** | An identity *for a program*, not a human — see [doc 09](09-gcp-iam-storage-bigquery.md) |
| **Token** | A short-lived, narrowly-scoped proof of identity a program presents instead of a password |
| **Load balancer** | A traffic cop that spreads incoming requests across multiple identical backend copies |
| **DNS** | The system that turns a name (`google.com`) into an IP address (`142.250.x.x`) |
| **Port** | A numbered "door" on a machine a specific program listens on (`:8000` = our agent-service) |
| **localhost / 127.0.0.1** | "This same machine," used when a service talks to another service on the same computer |
| **Middleware** | Code that runs on *every* request before/after your actual handler — see [doc 01](01-fastapi-and-middlewares.md) |
| **Orchestration** | Automatically deciding *where* and *how* to run many containers across many machines — what Kubernetes does ([doc 11](11-kubernetes-gke.md)) |
| **Idempotent** | An operation that gives the same end result no matter how many times you run it (important for deploy scripts) |
| **Latency** | How long a request takes to get a response — lower is faster |
