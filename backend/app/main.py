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
