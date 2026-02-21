"""API routes: health and schema. Dashboard flow uses /api/capture, /api/infer, /api/workflows, /api/agents."""

from fastapi import APIRouter

from app.config import settings

router = APIRouter(prefix="/api", tags=["shadow-ops"])


@router.get("/health")
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
