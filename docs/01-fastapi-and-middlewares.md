# FastAPI & Middlewares

## What is FastAPI?
FastAPI is a Python framework for building web APIs. You write a normal Python
function, decorate it with a route (`@app.post("/research")`), and FastAPI turns
it into an HTTP endpoint with automatic:
- **Validation** — request bodies are declared as Pydantic models
  ([schemas.py](../services/agent-service/app/schemas.py)); a bad request is rejected
  with a clear 422 error before your code even runs.
- **Docs** — visit `/docs` for an interactive Swagger UI, generated for free.
- **Async support** — `async def` endpoints let one worker handle many slow LLM
  requests concurrently instead of blocking on each one.

## What is a middleware?
A middleware is code that wraps EVERY request — it runs before your endpoint and
after it, like layers of an onion:

```
Request → CORS → RequestID → APIKey → RateLimit → Timing → [ /research endpoint ]
Response ←──────────────────────────────────────────────┘
```

Any layer can short-circuit: if the API key is wrong, `APIKeyMiddleware` returns
401 and the endpoint never runs.

## Our middleware stack ([middlewares.py](../services/agent-service/app/middlewares.py))
| Middleware | Job | Real-world name for this |
|---|---|---|
| `CORSMiddleware` | Lets the browser frontend call the API from another origin | CORS policy |
| `RequestIDMiddleware` | Tags each request with an ID, returned as `X-Request-ID` | Correlation ID / distributed tracing |
| `APIKeyMiddleware` | Rejects requests without the right `X-API-Key` header | Authentication |
| `RateLimitMiddleware` | Max N requests/minute per IP (sliding window) | Throttling / abuse protection |
| `TimingAnalyticsMiddleware` | Measures latency, logs, streams a row to BigQuery | Observability |

**Gotcha:** `app.add_middleware()` calls run in REVERSE order — the LAST one added
is the OUTERMOST layer. See the comment in [main.py](../services/agent-service/app/main.py).

## Try it
```bash
curl http://localhost:8000/health                          # public, no key needed
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" -H "X-API-Key: dev-secret-key" \
  -d '{"topic": "Impact of AI on jobs"}'
# Send it 11 times in a minute -> 429 rate limited
# Send without X-API-Key -> 401
```

## What breaks without it
No auth → anyone burns your Gemini quota. No rate limit → one buggy client takes
the service down. No request IDs → impossible to connect a user complaint to the
matching log line, LangSmith trace, and BigQuery row.
