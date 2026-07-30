"""The middleware stack — every request passes through these before/after the endpoint.

Execution order (outermost first): CORS -> RequestID -> APIKey -> RateLimit -> Timing.
Note: FastAPI runs middlewares in REVERSE order of add_middleware() calls,
so main.py adds them innermost-first.
"""
import logging
import time
import uuid
from collections import defaultdict, deque
from datetime import UTC, datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from . import analytics
from .config import settings

logger = logging.getLogger("agent-service")

PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Tags every request with a unique ID for tracing across logs/LangSmith/BigQuery."""

    async def dispatch(self, request, call_next):
        request.state.request_id = uuid.uuid4().hex[:8]
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Simple auth: clients must send X-API-Key matching SERVICE_API_KEY."""

    async def dispatch(self, request, call_next):
        if request.url.path in PUBLIC_PATHS or request.method == "OPTIONS":
            return await call_next(request)
        if request.headers.get("X-API-Key") != settings.service_api_key:
            return JSONResponse({"detail": "Invalid or missing X-API-Key"}, status_code=401)
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window limiter per client IP (in-memory; nginx adds another layer)."""

    def __init__(self, app):
        super().__init__(app)
        self.hits: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request, call_next):
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = self.hits[ip]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= settings.rate_limit_per_minute:
            return JSONResponse(
                {"detail": "Rate limit exceeded, try again in a minute"}, status_code=429
            )
        window.append(now)
        return await call_next(request)


class TimingAnalyticsMiddleware(BaseHTTPMiddleware):
    """Measures latency, writes a log line, and streams a row to BigQuery."""

    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception:
            status = 500
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 1)
            request_id = getattr(request.state, "request_id", "-")
            logger.info(
                "%s %s -> %s in %sms [rid=%s]",
                request.method, request.url.path, status, duration_ms, request_id,
            )
            if request.url.path not in PUBLIC_PATHS:
                analytics.log_request({
                    "request_id": request_id,
                    "ts": datetime.now(UTC).isoformat(),
                    "method": request.method,
                    "path": request.url.path,
                    "status": status,
                    "duration_ms": duration_ms,
                    "client": request.client.host if request.client else "unknown",
                })
        response.headers["X-Response-Time-Ms"] = str(duration_ms)
        return response
