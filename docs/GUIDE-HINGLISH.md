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

**Docker ke sab tech words — ek jagah:**

| Word | Matlab (simple) |
|---|---|
| **Image** | Tiffin ki READY-MADE packing — recipe se bani, ab copy kar sakte ho. `docker build` se banti hai |
| **Container** | Chalta hua tiffin — ek image se 100 containers chala sakte ho. `docker run` |
| **Dockerfile** | Packing ki recipe (kaunsa Python, kaunsi libraries, kaise start karna) |
| **Engine** | Docker ka dil — background me containers chalata hai ("Engine running" jo aapko dikha) |
| **WSL2** | Windows ke andar asli Linux — Docker Engine isi me chalta hai (jo humne install kiya) |
| **docker-compose** | Ek YAML file = poori team ek command me: `docker compose up` |
| **Volume** | Container ki permanent almari — container mare to bhi data bacha rahe (hamara `rag-data` = Chroma vectors) |
| **Port mapping** | `"80:80"` = laptop ka port 80 → container ka port 80 (isliye `http://localhost` chalta hai) |
| **Registry** | Images ka godown — Docker Hub (public) ya Artifact Registry (hamara, GCP me) |
| **Tag** | Image ka version label — `:latest`, `:abc123` (git commit) — rollback isi se hota hai |
| **Layer** | Image ki parat — har Dockerfile line ek layer; unchanged layers CACHE hoti hain (isliye dobara build fast) |
| **Docker Desktop** | GUI app jo aapne kholi — Engine + WSL manage karti hai, containers dikhaati hai |

**Ek aur pro word — compose override**: hamari `docker-compose.adc.yml` ek
override file hai — base compose me sirf common cheezein, override me
laptop-specific (GCP credentials mount). VM pe override use hi nahi hoti —
wahan service account khud auth karta hai. Real teams isi pattern se
dev/staging/prod alag rakhti hain.

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

### 🔴 LIVE JOURNEY — humne GKE pe EXACTLY ye kiya (har step ka KYU)

**Step 1 — APIs enable + Artifact Registry banaya.** KYU: GCP me har service ka
switch by-default OFF hota hai (safety+billing); Artifact Registry = hamari
Docker images ka private godown — K8s wahi se images kheenchta hai.

**Step 2 — Cloud Build se 3 images banayi.** KYU: laptop se GB-bhar images
upload karna slow hai; `gcloud builds submit` sirf CODE upload karta hai
(chhota), image GOOGLE ke server pe banti hai aur seedha registry me jaati hai.
Teeno builds PARALLEL chalayi — time ⅓.

**Step 3 — Node service account ko 3 naye roles.** KYU: cluster ke nodes bhi
VMs hain jo hamare `agentic-app` robot se chalte hain — unhe images READ karne
ki permission (`artifactregistry.reader`) chahiye warna `ImagePullBackOff`
error. Logging/monitoring roles bhi, warna cluster andha.

**Step 4 — Cluster banaya:** `gcloud container clusters create agentic-cluster
--num-nodes=2 --machine-type=e2-medium --service-account=agentic-app@...`
KYU service-account: pods me wahi keyless auth jo VM pe thi — continuity!

**Step 5 — `kubectl apply -f` sab manifests.** Declarative jadoo: humne sirf
"KYA chahiye" bola, Kubernetes ne pods schedule kiye, internal DNS banaya, aur
`type: LoadBalancer` dekhte hi GCP se ek **asli public IP** (34.47.212.125)
provision karwa liya.

**Step 6 — REAL PROBLEM aayi (aur yehi best lesson hai):** agent-service pods
`Pending` atke. `kubectl describe` bola: **"Insufficient cpu"**. Nikla ye:
e2-medium me 2 vCPU hote hain par **allocatable sirf 940m** (GKE khud OS +
kubelet ke liye reserve karta hai), aur system pods (DNS, metrics...) bhi
usi me rehte hain. Hamari `requests: cpu: 250m` × 2 replicas fit nahi hui.
**Fix**: request 250m→100m (request = guaranteed booking, limit = burst max —
scheduler sirf REQUEST dekhta hai) aur replicas 2→1 (HPA load pe badha dega).
**Yaad rakhna**: requests jitni honest, cluster utna efficient.

**Step 7 — LB pe research test:** `http://34.47.212.125/api/agent/research` →
10 sources → report GCS me. Internet → GCP LB → nginx pod → agent pod → MCP pod
→ Vertex AI — sab Kubernetes ke andar.

**Step 8 — SELF-HEALING DEMO (Kubernetes ka asli jadoo):**
```
kubectl delete pod -l app=agent-service     # pod MAAR diya (crash simulation)
8 second baad:  NAYA pod aa gaya (naya naam, khud bana)
38 second baad: 1/1 Running — traffic wapas chalu
```
Kisi insaan ne kuch NAHI kiya. Deployment ka register bola "1 replica chahiye",
reality me 0 tha, Kubernetes ne गैप bhar diya. VM pe yehi crash = site DOWN
jab tak aap khud na jaao.

**Step 9 — Cluster DELETE.** KYU: kaam khatam, screenshot le liye, ab har
ghanta paisa kyu jale. Images Artifact Registry me hain — cluster dobara banao
to 5 minute me sab wapas. **Cattle, not pets** — infra ko disposable rakho.

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

### 🔴 LIVE JOURNEY — Phase 12 me humne kya kiya

1. **Alag deploy robot banaya**: `github-deploy@...` — runtime robot (`agentic-app`)
   se ALAG, sirf 2 roles: Artifact Registry Writer + Kubernetes Engine Developer.
   KYU alag: GitHub ki key kabhi leak ho to attacker sirf deploy kar sakta hai,
   data (GCS/BigQuery) nahi padh sakta. **Har kaam ka apna robot, minimum permissions.**
2. **Is robot ki JSON key banayi** — haan, wahi "key file" jise hum avoid karte
   aaye! KYU majboori: GitHub GCP ke BAHAR hai — metadata server nahi hai wahan,
   to koi to credential dena padega. Ye single exception hai, tightly-scoped.
   **Enterprise isse bhi hataata hai**: *Workload Identity Federation* (WIF) —
   GitHub apna OIDC token dikhata hai, GCP usi pe bharosa kar leta hai, key file
   zero. Interview me "SA key vs WIF" bol doge to senior lagoge.
3. **Workflow smart banaya**: deploy job pehle images push karta hai, PHIR check
   karta hai "cluster zinda hai?" — nahi hai to gracefully skip (hum cluster
   delete kar chuke the — pipeline phir bhi green). Infra aaye-jaaye, pipeline
   kabhi na toote.
4. Push karte hi **pehla CI run** GitHub pe chala — lint + 6 tests, bina kisi
   secret ke (test job ko GCP chahiye hi nahi).

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

## 8. IAM samjho — HAMARE project me kaun-kaun "log" hain

IAM = **"kaun kya kar sakta hai"** ka system. 3 concepts:
**Principal** (kaun — insaan ya robot) + **Role** (permissions ka bundle) +
**Binding** (is principal ko ye role do). Bas.

Hamare project me 3 identities + 4 keys hain — sab ka alag kaam:

| # | Identity/Key | Kya hai | Kahan use hui |
|---|---|---|---|
| 1 | `ritikabansal...@gmail.com` | **Insaan (Owner)** — `gcloud auth login` se | Saari gcloud commands: project/VM/bucket banana |
| 2 | **ADC file** (usi account ki) | `gcloud auth application-default login` se bani ek **credentials file** jo CODE use karta hai | Laptop pe Python/Docker se Vertex AI, GCS, BigQuery calls |
| 3 | `agentic-app@...gserviceaccount.com` | **Robot (service account)** — sirf 3 roles: Storage Object Admin, BigQuery Data Editor, Vertex AI User | VM se saari GCP calls — **koi key file NAHI** |
| 4 | `GOOGLE_API_KEY` (AIza...) | Gemini AI Studio key | Ab sirf fallback (USE_VERTEX_AI=false pe) |
| 5 | `LANGSMITH_API_KEY` (lsv2...) | LangSmith SaaS ki key — **GCP se koi lena-dena nahi** | Tracing/evals |
| 6 | `TAVILY_API_KEY` (tvly...) | Tavily search SaaS ki key | Web search tool |
| 7 | `SERVICE_API_KEY` | **HAMARI khud ki API ka password** — GCP nahi, hamara middleware check karta hai | Client → `X-API-Key` header |

**Sabse bada lesson — VM pe auth kaise hua (bina kisi key ke):**
```
VM banate waqt: --service-account=agentic-app@...
→ VM ke andar ek "metadata server" hota hai (Google ka)
→ Python library (storage.Client, ChatVertexAI) khud usse token maangti hai
→ token me sirf wahi 3 permissions jo humne binding me di
= koi password/key file kahin nahi — chori hone ko kuch hai hi nahi
```
Laptop pe metadata server nahi hota, isliye wahan ADC file (identity #2) lagti
hai — Docker containers me humne wahi file mount ki (docker-compose.adc.yml).

**Vertex AI setup — total 3 cheezein ki thi:**
1. `gcloud services enable aiplatform.googleapis.com` (API ka switch ON)
2. Auth pehle se thi (laptop = ADC, VM = service account) — **key banayi hi nahi**
3. Code me `ChatVertexAI(model, project="agentic-research-81536", location="global")`
   — billing project ke credits se, quota enterprise-level

**Least privilege ka matlab hamare project me**: robot ko Owner/Editor NAHI diya.
Kal ko service account leak bhi ho jaye to attacker sirf bucket/BigQuery/Vertex
tak jaa sakta hai — project delete nahi kar sakta, VM nahi bana sakta, billing
nahi chhed sakta.

---

## 9. Doosre clouds ke naam — confusion mat khao

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

**Vertex AI kya hai?** GCP ka **enterprise AI platform** — wahi Gemini, par
"office wala setup": API key ki jagah IAM/ADC se auth, billing account se
pay-per-use, badi quotas, model tuning/vector search sab ek jagah.

**Hum AB Vertex AI hi use kar rahe hain** (`.env` me `USE_VERTEX_AI=true`) —
kyunki GCP credits hain aur AI Studio free tier ki quota chhoti thi (flash =
20 req/day). Code me DONO supported hain — flag false karo to wapas free AI
Studio key pe (graph.py ka `_llm()` dekho, bas ek if-else hai). Yehi pattern
real companies use karti hain: dev me free tier, prod me Vertex.

---

## 10. Message Queues & Pub/Sub — "order abhi lo, kaam baad me karo"

### Problem jo ye solve karta hai
Hamara `/research` endpoint 2-5 MINUTE chalta hai aur user ko intezaar karna
padta hai (browser ghoomta rehta hai). Agar 100 users ek saath aaye? Sab atak
jayenge. Real systems me lambe kaam ka rule: **"request turant accept karo,
kaam PEECHE karo"** — isi ke liye message queue hoti hai.

### Queue ka concept — "tiffin wale ka order register"
Dukaan pe 50 order ek saath aaye to dukandar bhagta nahi — sab orders ek
**register (queue)** me likhta hai, aur 3 worker ek-ek karke banate hain:

```
ABHI (synchronous):                     QUEUE KE SAATH (asynchronous):
User → /research → 3 min wait → report  User → /research → turant "ticket #42" milta hai
                                        Ticket queue me → free WORKER uthata hai
                                        → kaam hota hai → report GCS me
                                        User: GET /status/42 → "ready! ye raha link"
```

### Words jo interview me aayenge
| Word | Matlab |
|---|---|
| **Producer/Publisher** | Jo message queue me DAALTA hai (hamara API) |
| **Consumer/Subscriber** | Jo message UTHATA hai (worker service) |
| **Topic** | Queue ka naam/channel (jaise `research-jobs`) |
| **Ack (acknowledge)** | Worker bola "kaam ho gaya" → message queue se delete |
| **Retry / Dead-letter queue** | Worker fail hua? Message wapas queue me; baar-baar fail = alag "DLQ" me (postmortem ke liye) |
| **Decoupling** | Producer/consumer ek doosre ko jaante hi nahi — koi bhi giro, doosra chalta rahe |

### Pub/Sub = GCP ki managed queue (AWS me SQS/SNS, self-hosted me RabbitMQ/Kafka)
Server nahi chalana padta, unlimited scale, per-message paisa. Hamare project me
aise lagta (agar lagate):
```
agent-service /research → Pub/Sub topic "research-jobs" me message publish
→ turant job_id return                          (user ka wait khatam)
naya "worker-service" (4th microservice) topic subscribe kare
→ message aaya → LangGraph chalao → report GCS → status BigQuery me update
```
Command sirf itni: `gcloud pubsub topics create research-jobs`.
**Kafka** bhi yehi hai par self-hosted + streaming-focused (events ka replay ho
sakta hai) — bade data pipelines me milta hai.

---

## 11. Jo aur concepts ab tak cover nahi hue — sab yahan

### Cloud Run — "VM/K8s ka aalsi cousin" (serverless)
Container do → Google chala dega. Na VM, na cluster, na nodes. Traffic zero =
**scale to zero = bill zero**. Request aayi to milliseconds me jag jaata hai.
`gcloud run deploy agent-service --image <hamari-image> --region asia-south1`
— bas. *To K8s kyu seekha?* Cloud Run simple cheezon ke liye perfect hai;
K8s tab jab multi-service control, custom networking, long-running jobs
chahiye. Interview me dono ka trade-off bolna = strong signal.

### Secret Manager — passwords ki asli tijori
Humne secrets `.env`/K8s Secret me rakhe (theek hai learning ke liye). Production
me **Secret Manager**: central tijori, **versioning** (purani key wapas la sakte
ho), **audit log** (kisne kab padha), IAM se access. Code me:
`secretmanager.SecretManagerServiceClient().access_secret_version(...)`.
K8s Secret sirf base64 hota hai — encryption nahi, ye yaad rakhna.

### VPC & Networking — cloud ka apna mohalla
- **VPC** = aapka private network (hamari VM `default` VPC me thi, internal IP 10.160.0.2)
- **Subnet** = VPC ka region-wise tukda
- **Firewall rules** = kaun andar aa sakta hai (humne sirf :80 khola tha — yehi VPC firewall tha!)
- **Internal vs External IP** = mohalle ke andar ka pata vs duniya wala pata.
  Pods/services aapas me internal IP pe baat karte hain — free + fast + secure.

### HTTPS/TLS — ab tak hamara sabse bada GAP 🔴
Hamari VM/LB **http://** pe hai = data raste me PLAIN dikh sakta hai (API key
bhi!). Production me hamesha **https://**. Kaise: (1) domain kharido (₹100-800/saal),
(2) DNS me IP point karo, (3) **cert-manager + Let's Encrypt** (K8s me free
auto-renew certificates) ya GCP **managed certificate** LB pe. Learning project
me chhoda kyunki domain paid hai — par interview me gap khud batana = maturity.

### Terraform / IaC — "infrastructure ki recipe file"
Humne sab `gcloud` commands se banaya — **clicks/commands gayab, yaad kisko?**
IaC = infra ko CODE me likho:
```hcl
resource "google_storage_bucket" "reports" {
  name     = "agentic-reports-81536"
  location = "ASIA-SOUTH1"
}
```
`terraform apply` = sab ban gaya. `terraform destroy` = sab saaf. Git me history.
Naya environment (staging) = same file dobara chalao. Kubernetes YAML bhi isi
philosophy ka hissa hai — **declarative**: "kya chahiye" likho, "kaise" tool dekhe.

### Caching & Redis — "baar-baar mat banao"
Same topic pe 50 log research maangein to 50 baar LLM chalana bewakoofi (paisa
+ time). **Cache**: pehli baar ka jawab **Redis** (in-memory, microseconds) me
rakho `key=topic_hash`, **TTL** (expiry, jaise 24h) ke saath. Agli baar seedha
cache se. GCP me managed Redis = **Memorystore**. LLM apps me semantic cache
bhi hota hai (milte-julte sawal = same jawab).

### Scaling: Horizontal vs Vertical
- **Vertical** = machine BADI karo (e2-small → e2-medium) — limit hai, restart lagta hai
- **Horizontal** = machines ZYADA karo (hamara HPA: 2→5 pods) — asli scale yahi
- Horizontal ke liye service **stateless** honi chahiye (state bahar: GCS/BigQuery/
  Redis me) — isi liye hamne reports GCS me rakhi, container me nahi! Ab samjhe
  architecture aisi kyu banayi 😉

### SQL vs NoSQL vs Warehouse — data kahan rakhein
| Type | Example | Kab | Hamare project me |
|---|---|---|---|
| SQL (OLTP) | Postgres, **Cloud SQL** | Users, orders, transactions | (nahi laga — hota to user accounts) |
| NoSQL | Firestore, MongoDB | Flexible/JSON data, chat history | (LangGraph checkpoints yahan ja sakte) |
| Warehouse (OLAP) | **BigQuery** | Analytics on karodo rows | ✅ request analytics |
| Object store | **GCS** | Files/blobs | ✅ reports, uploads |
| Vector DB | **Chroma**, pgvector | Embeddings similarity | ✅ RAG |

### Webhooks — "hum tumhe bulayenge, tum mat aao"
Polling (baar-baar "ho gaya?" poochna) ki jagah ulta: kaam khatam → SERVER khud
aapke diye URL pe POST kar de. Async research + webhook = "report ready hote hi
mere Slack pe bhej do". GitHub Actions bhi webhooks pe hi chalta hai (push hua
→ GitHub ne workflow ko bulaya).

### Blue-Green & Canary deploys — bina dare release karna
- **Rolling** (hamara K8s default): pods ek-ek karke naye hote hain
- **Blue-Green**: poora naya environment (green) khada karo, traffic switch — issue? switch back
- **Canary**: naya version pehle sirf 5% users ko → metrics theek → 100%
LLM apps me canary + evals ka combo = prompt changes safely ship karna.

---

## 12. Ab aage kya? (current status)

- [x] Phases 0-9: sab bana, sab VERIFIED (local + GCP writes)
- [x] Docker + compose full stack → `http://localhost` ✅
- [x] Phase 10: VM deploy — internet pe live chala, verify karke VM STOP ki ✅
- [x] Phase 11: GKE — cluster, LB, self-healing demo, phir cluster DELETE ✅
- [ ] Phase 12: CI/CD live karo (GitHub repo secrets: `GCP_SA_KEY` + `GCP_PROJECT_ID` set karke workflow chalana)
- [ ] Phase 13: README me screenshots + final teardown (`gcloud projects delete agentic-research-81536` → bill ₹0 forever)
