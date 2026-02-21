"""Shadow Ops – Expense Report Shadow – FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings
from app.routes.agents import router as agents_router
from app.routes.capture import router as capture_router
from app.routes.infer import router as infer_router
from app.routes.schemas import router as schemas_router
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

# All API routes live under /api (health, capture, infer, workflows, agents, schemas)
app.include_router(router)  # /api/health, /api/workflow/infer, /api/agent/execute
app.include_router(schemas_router, prefix="/api")
app.include_router(capture_router, prefix="/api")
app.include_router(infer_router, prefix="/api")
app.include_router(workflows_router, prefix="/api")
app.include_router(agents_router, prefix="/api")


@app.get("/")
def root() -> dict[str, str]:
    """Root redirect/info."""
    return {
        "service": "Shadow Ops – Expense Report Shadow",
        "docs": "/docs",
        "health": "/api/health",
    }
