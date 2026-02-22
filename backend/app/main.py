"""Shadow Ops – Expense Report Shadow – FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.agents import router as agents_router
from app.routes.capture import router as capture_router
from app.routes.infer import router as infer_router
from app.routes.schemas import router as schemas_router
from app.routes.receipt import router as receipt_router
from app.routes.workflows import router as workflows_router
from app.logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle."""
    logger.info("application_startup", debug=settings.debug)
    yield
    logger.info("application_shutdown")


app = FastAPI(
    title="Shadow Ops – Expense Report Shadow",
    description="AI-powered expense workflow inference and agent execution (Nova 2 Lite & Nova Act).",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Optional API key gate (only active when API_KEY env is set)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class APIKeyMiddleware(BaseHTTPMiddleware):
    """When API_KEY is set, require X-API-Key on /api/*; otherwise pass through."""

    async def dispatch(self, request, call_next):
        if not settings.api_key or not request.url.path.startswith("/api/"):
            return await call_next(request)
        key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
        if key != settings.api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid X-API-Key header"},
            )
        return await call_next(request)


app.add_middleware(APIKeyMiddleware)

# ---------------------------------------------------------------------------
# Rate limiter – protects expensive Nova endpoints from abuse.
# Allows RATE_LIMIT_MAX_CALLS calls per IP per RATE_LIMIT_WINDOW_SECONDS.
# Only applies to POST /api/capture/receipt and POST /api/agents/*/run.
# Judges doing 5-10 test runs will never hit the limit.
# ---------------------------------------------------------------------------
import time as _time
from collections import defaultdict as _defaultdict

_RATE_WINDOW = settings.rate_limit_window_seconds
_RATE_MAX = settings.rate_limit_max_calls
_EXPENSIVE_PREFIXES = ("/api/capture/receipt", "/api/agents/")
_EXPENSIVE_SUFFIXES = ("/run",)

# {ip: [timestamp, ...]}
_rate_buckets: dict[str, list[float]] = _defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Lightweight per-IP rate limiter for expensive Nova API calls."""

    async def dispatch(self, request, call_next):
        if request.method != "POST":
            return await call_next(request)
        path = request.url.path
        is_expensive = (
            path == "/api/capture/receipt"
            or (path.startswith("/api/agents/") and path.endswith("/run"))
        )
        if not is_expensive:
            return await call_next(request)

        ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
        ip = ip.split(",")[0].strip()
        now = _time.time()
        # Prune old entries
        _rate_buckets[ip] = [t for t in _rate_buckets[ip] if now - t < _RATE_WINDOW]
        if len(_rate_buckets[ip]) >= _RATE_MAX:
            logger.warning("rate_limit_exceeded", ip=ip, path=path, count=len(_rate_buckets[ip]))
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded. Max {_RATE_MAX} calls per {_RATE_WINDOW // 60} minutes. Try again later."
                },
            )
        _rate_buckets[ip].append(now)
        return await call_next(request)


app.add_middleware(RateLimitMiddleware)

# All API routes live under /api (capture, infer, workflows, agents, schemas)
app.include_router(schemas_router, prefix="/api")
app.include_router(capture_router, prefix="/api")
app.include_router(infer_router, prefix="/api")
app.include_router(workflows_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(receipt_router, prefix="/api")


@app.get("/")
def root() -> dict[str, str]:
    """Root redirect/info."""
    return {
        "service": "Shadow Ops – Expense Report Shadow",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health")
def get_health() -> dict[str, str]:
    """Health check for load balancers and monitoring; includes mode, region, model_id."""
    return {
        "status": "ok",
        "service": "shadow-ops-expense",
        "version": "0.1.0",
        "mode": settings.nova_mode,
        "region": settings.aws_region,
        "model_id": settings.nova_model_id_lite,
    }
