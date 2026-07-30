# 🇮🇳 Complete Hinglish Guide — Sab Kuch Samjho, Ek Hi Jagah

> Ye guide AAPKE liye hai — har technology simple bhasha me, analogies ke saath.
> Portfolio ke liye English docs [TECHNOLOGIES.md](TECHNOLOGIES.md) me hain.

---

## 1. Ye project hai kya? (30 second me)

Aap ek topic dete ho → AI agents ki **team** kaam karti hai:

```
Aap: "Impact of AI on Indian jobs"
        ↓
🛡️ Guard    → "Ye request safe hai? Injection attack to nahi?"
🧠 Planner   → "Isko 3 chhote sawalon me todta hoon"
🔍 Researcher→ "Web search, Wikipedia, arXiv se jawab dhoondta hoon" (MCP tools)
📝 Summarizer→ "Sab findings ka nichod nikalta hoon"
✍️ Writer    → "Proper report likhta hoon sources ke saath"
🛡️ Guard    → "Report me kisi ka phone/email to leak nahi hua?"
💾 Save     → Report Cloud Storage me, analytics BigQuery me
```

Ye sab **verified chal raha hai** — humne test kiya, report `gs://agentic-reports-81536` me gayi.

---

## 2. Har technology kya hai — desi analogy ke saath

### FastAPI — "Restaurant ka waiter"
Customer (browser) order deta hai, waiter (FastAPI) kitchen (aapka code) tak le
jaata hai, khana (response) wapas laata hai. `@app.post("/research")` likha =
ek naya dish menu me add ho gaya. Free bonus: `/docs` pe automatic menu card
(Swagger UI) ban jaata hai.

### Middleware — "Mall ke security gates"
Mall me ghusne se pehle: gate → metal detector → token milna. Waise hi har
request endpoint tak pahunchne se PEHLE 5 gates se guzarti hai:
1. **CORS** — "kaunse browser allowed hain"
2. **Request-ID** — har request ko ek token number (`a1b2c3d4`) — baad me
   complaint aaye to isi number se poori journey trace hoti hai
3. **API-Key** — "membership card dikhao" (`X-API-Key` header) — nahi hai to 401
4. **Rate-limit** — "ek banda 1 minute me 10 baar hi aa sakta hai" — zyada to 429
5. **Timing** — stopwatch: kitna time laga, sab BigQuery me note

Code: [middlewares.py](../services/agent-service/app/middlewares.py)

### LangChain — "LLM ka universal remote"
Har AC ka apna remote hota hai, par universal remote sabpe chalta hai.
LangChain = universal remote for LLMs. Aaj Gemini, kal Claude — code me bas ek
line badlegi. Iska sabse bada kaam hamare liye: **structured output** — LLM ko
bolna "essay mat likh, EXACTLY ye format de" (planner se list of questions).

### LangGraph — "Factory ki assembly line"
Ek mega-prompt = ek bande se bolna "gaadi bana de". Assembly line = har station
apna kaam: chassis → engine → paint → QC. LangGraph me har station = **node**
(planner, researcher...), conveyor belt = **edges**, aur gaadi ke saath chalne
wala checklist = **state** (topic, plan, findings, report...).
QC fail → gaadi alag line pe (conditional edge → blocked node). Yehi hamara
graph hai: [graph.py](../services/agent-service/app/graph.py)

### ReAct agent (Researcher) — "Detective ka loop"
Detective sochta hai → suraag dhoondhta hai → jo mila usse aage sochta hai →
phir dhoondhta hai → case solve. LLM bhi: "mujhe recent data chahiye" →
`web_search` call → results padhe → "arXiv bhi dekh loon" → ... → final answer.
`recursion_limit=12` = "12 se zyada chakkar mat lagao" (warna infinite loop).

### MCP — "Tools ka USB port"
Pehle har phone ka alag charger hota tha; ab USB-C sab me. MCP = AI tools ka
USB-C. Tools ek **alag server** me hain (web_search, wiki_lookup, arxiv_search,
save_report) — koi bhi MCP-supported agent (hamara agent, Claude Desktop,
Cursor) inhe plug-in karke use kar sakta hai. Naya tool add karo server me →
agent ko AUTOMATICALLY mil jaata hai, agent ka code chhoona bhi nahi padta.

### RAG — "Open-book exam"
LLM ne aapke private documents kabhi nahi padhe. RAG = exam me book saath le
jaana: sawal aaya → book ke RELEVANT pages nikalo → unhe padh ke jawab do.
- Document upload → chhote **chunks** me toda → har chunk ka **embedding**
  (matlab ka mathematical fingerprint — "EV subsidy" aur "electric car
  incentive" ke fingerprints paas-paas honge)
- Sawal aaya → uska fingerprint banao → sabse milte-julte chunks dhoondo
  (**Chroma** vector database me) → LLM ko do
Humne test kiya: private doc me "50,000 TPS" likha tha, agent ne report me
exactly wahi nikala — internet pe ye kahin nahi tha!

### Guardrails — "Bouncer + Censor board"
- **Input guard (bouncer)**: "Ignore all previous instructions..." jaisi
  requests gate pe hi block — LLM tak pahunchne hi nahi deta (0 token kharcha)
- **Output guard (censor)**: final report me email/phone/Aadhaar jaisa kuch
  dikha to `[REDACTED]` — kyunki LLM pe kabhi 100% bharosa nahi karte

### LangSmith — "CCTV + Report card"
- **CCTV (tracing)**: har request ki poori recording — kaunsa agent chala,
  kya prompt gaya, kaunsa tool call hua, kitne tokens lage. smith.langchain.com
  pe login karo → project `agentic-research` → har run dikhega
- **Report card (evals)**: 5 fixed topics pe reports banwao, Gemini judge se
  0-1 marks dilwao (relevance, structure, groundedness). Prompt badla → phir
  test → marks compare. "Accha lag raha hai" nahi, NUMBERS.

---

## 3. Deployment — teen levels (aur har level kyun)

### Level 1: Docker (containers) — "Tiffin box system"
**Problem**: "Mere laptop pe chalta hai, server pe nahi" — kyunki server pe
Python alag, libraries alag.
**Solution**: Container = tiffin box — khana (code) + masala (dependencies) +
bartan (Python) sab pack. Kahin bhi kholo, SAME chalega.

- Har service ka **Dockerfile** = tiffin packing ki recipe
- **docker-compose** = 4 tiffin ek saath kholna, ek private network pe:
```powershell
docker compose -f deploy/docker-compose.yml up --build
# phir browser me: http://localhost  (nginx frontend)
```
Magic: compose network me service ka NAAM hi uska address hai —
`http://mcp-tools:8100` — koi IP yaad nahi rakhni.

### Level 2: VM (Compute Engine) — "Kiraye ka computer"
Google se ek Linux computer kiraye pe lo (₹1-2/hour), usme Docker daalo, wahi
compose chalao — ab duniya aapke app ko `http://VM_IP/` pe dekh sakti hai.

```bash
# 1. Firewall: sirf port 80 khula (baaki services HIDDEN — security!)
gcloud compute firewall-rules create allow-http --allow tcp:80 --target-tags=http-server

# 2. VM banao (Mumbai me, chhota wala)
gcloud compute instances create agentic-vm --zone=asia-south1-a \
  --machine-type=e2-small --image-family=debian-12 --image-project=debian-cloud \
  --tags=http-server \
  --service-account=agentic-app@agentic-research-81536.iam.gserviceaccount.com \
  --scopes=cloud-platform

# 3. Andar ghuso (SSH = remote ka terminal)
gcloud compute ssh agentic-vm --zone=asia-south1-a
# VM ke andar: deploy/vm/setup.sh ke steps (Docker install, git clone, compose up)

# 4. KAAM KHATAM? BAND KARO (paisa tabhi lagta hai jab VM ON hai):
gcloud compute instances stop agentic-vm --zone=asia-south1-a
```

**Iska sabse bada IAM lesson**: VM ko `--service-account` diya = VM ke andar ka
code AUTOMATICALLY GCS/BigQuery me likh sakta hai, koi password/key file NAHI.
(Key file download karna = cloud ki sabse badi galti, kabhi mat karna.)

**VM ki dikkat**: crash hua = app down. Zyada traffic = kuch nahi kar sakte.
Update karna = downtime. Isliye 👇

### Level 3: Kubernetes (GKE) — "Restaurant ka manager jo kabhi nahi sota"
Aap manager ko bolke jaate ho: **"HAMESHA 2 waiters honain chahiye"**. Ek waiter
bimaar? Manager turant naya bula leta hai — aapko pata bhi nahi chalta. Rush
aaya? Manager khud 2 se 5 waiter kar deta hai. Yehi Kubernetes hai —
**self-healing + autoscaling, declared by you, managed by K8s**.

| K8s cheez | Matlab | Analogy |
|---|---|---|
| **Pod** | Ek chalta hua container | Ek waiter |
| **Deployment** | "N copies hamesha chalti rahein" | Manager ka register: "2 waiter chahiye" |
| **Service** | Pods ka ek fixed naam/address + load balancing | Reception desk — kaam kisi bhi free waiter ko |
| **LoadBalancer** | Google ka public IP aapke app pe | Restaurant ka main gate board |
| **ConfigMap/Secret** | Settings/passwords alag rakhna | Recipe book / tijori |
| **HPA** | CPU badha to pods badhao | Rush me extra staff |
| **Namespace** | Apne app ka alag kamra | Alag section |

Deploy (jab Phase 11 karenge — ye MOST expensive week hai, ~A$5-8):
```bash
# 1. Images ko Google ke godown (Artifact Registry) me bhejo
# 2. Cluster banao:  gcloud container clusters create-auto agentic-cluster --region=asia-south1
# 3. YAML files apply karo:  kubectl apply -f deploy/k8s/...
# 4. Tamasha dekho:
kubectl -n agentic-research get pods -w        # pods zinda hote dekhho
kubectl -n agentic-research delete pod -l app=agent-service
#   ^ ek pod MAAR do — Kubernetes turant naya khada kar dega 🤯
# 5. KHATAM? CLUSTER DELETE KARO (screenshot pehle le lena!):
gcloud container clusters delete agentic-cluster --region=asia-south1
```
Saari YAML files ready hain: [deploy/k8s/](../deploy/k8s/) — har file me comments.

---

## 4. CI/CD — "Code push kiya, baaki sab automatic"

Abhi: code badla → khud test karo → khud build → khud deploy. 😓
CI/CD ke baad ([ci-cd.yml](../.github/workflows/ci-cd.yml)):

```
git push
   ↓ (GitHub Actions khud chalega)
lint ✓ → tests ✓ → (evals ✓) → Docker images build → Google godown me push
   ↓ ("Run workflow" button dabao)
GKE pe deploy — zero downtime (pods ek-ek karke replace hote hain)
```
Test fail = deploy RUKEGA. Isi ko **quality gate** kehte hain — kharab code
production tak pahunch hi nahi sakta. LLM apps me evals bhi gate hain: prompt
badla aur report quality giri → marks gire → build fail. **Yehi MLOps hai.**

---

## 5. Monitoring — "3 sawal, 3 tools"

| Sawal | Tool | Kahan dekhna |
|---|---|---|
| App zinda hai? Kitni fast? | Cloud Monitoring | GCP Console → Monitoring |
| AI ka jawab ACHA hai? Kaunsa step slow? | LangSmith | smith.langchain.com |
| Kaun use kar raha, kya fail ho raha? | BigQuery | Console → BigQuery → `agent_analytics.requests` |

Teeno ek doosre se `request_id` se jude hain — ek ID pakdo, poori kahani mil
jayegi (nginx log → LangSmith trace → BigQuery row).

BigQuery me khud SQL chala ke dekho:
```sql
SELECT path, COUNT(*) AS requests, ROUND(AVG(duration_ms)) AS avg_ms
FROM agent_analytics.requests GROUP BY path;
```

---

## 6. Paise ka hisaab 💰

| Cheez | Kharcha |
|---|---|
| Gemini, LangSmith, Tavily, local sab kuch | ₹0 (free tiers) |
| Cloud Storage + BigQuery (itna sa data) | ~₹0 |
| VM (e2-small, sirf jab ON ho) | ~₹1.5/hour → **STOP karna mat bhoolna** |
| GKE Autopilot (Phase 11 ka hafta) | ~A$5-8 → **DELETE same week** |
| Budget alert | A$10 pe email aa jayega (already set ✅) |

**Sab khatam hone ke baad ek hi command se SAB saaf:**
```bash
gcloud projects delete agentic-research-81536
# Project gaya = VM, cluster, bucket, BigQuery, service account — SAB gaya. Bill = ₹0 forever.
```

---

## 7. Ek request ki poori yatra (interview me yehi sunana)

```
Browser → GCP LoadBalancer → nginx (rate-limit check, route)
→ agent-service: CORS → RequestID(a1b2c3d4) → API-Key ✓ → RateLimit ✓ → Timer start
→ LangGraph: InputGuard ✓ → Planner (Gemini: 3 sawal)
→ Researcher loop: MCP server pe web_search/wiki/arxiv + rag-service pe doc search
→ Summarizer → Writer (markdown report) → OutputGuard (PII scrub)
→ MCP save_report → Cloud Storage (gs://...)
→ Response wapas: Timer stop → BigQuery me row → header me X-Request-ID
→ Poori recording LangSmith me, tagged a1b2c3d4
```
14 technologies, ek request, har ek ka apna kaam. 🎯

---

## 8. Doosre clouds ke naam — confusion mat khao

Har cloud me SAME cheezein hain, bas naam alag (jaise Ola/Uber):

| Kaam | GCP (hum ye use kar rahe) | AWS | Azure |
|---|---|---|---|
| Kiraye ka computer (VM) | **Compute Engine** | **EC2** | Virtual Machines |
| Files ka godown | **Cloud Storage (GCS)** | S3 | Blob Storage |
| Kubernetes managed | **GKE** | EKS | AKS |
| Docker images ka godown | **Artifact Registry** | ECR | ACR |
| Data warehouse (SQL analytics) | **BigQuery** | Redshift | Synapse |
| Permissions system | **IAM** | IAM | Entra ID |

Matlab: **EC2 = AWS ka Compute Engine** — jo VM hum Phase 10 me banayenge, AWS
wale usi ko EC2 kehte hain. Ek seekh liya = sab clouds ka concept aa gaya.

**Vertex AI kya hai?** GCP ka **enterprise AI platform** — Gemini ko company-grade
tareeke se use karna (IAM-based auth, private data, model training/tuning,
vector search, ML pipelines sab ek jagah). Hum abhi **AI Studio API key** use kar
rahe hain (simple + free tier — seekhne ke liye perfect). Vertex AI wahi Gemini
hai par "office wala setup": key file nahi, service account se auth; billing
account se pay-per-use. Job descriptions me "Vertex AI" dikhe to samjho: GCP pe
AI apps banana — jo aap abhi seekh hi rahe ho.

---

## 9. Ab aage kya? (current status)

- [x] Phases 0-9: sab bana, sab VERIFIED (local + GCP writes)
- [ ] **Docker Desktop app kholo** (Start menu me hai, install ho chuka) → whale 🐳 steady hone do
- [ ] `docker compose up` full stack test → `http://localhost`
- [ ] Phase 10: VM deploy (upar ke commands, ~2 din aaram se)
- [ ] Phase 11: GKE (expensive week — banao, seekho, screenshot, DELETE)
- [ ] Phase 12: CI/CD live karo (GitHub pe push + secrets set)
- [ ] Phase 13: teardown + README me screenshots
