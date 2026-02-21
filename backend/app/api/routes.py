"""API routes for workflow inference and agent execution."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.logging_config import get_logger
from app.services.nova_integration import execute_agent, infer_workflow

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["shadow-ops"])


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------


class WorkflowInferenceRequest(BaseModel):
    """Request body for workflow inference (Nova 2 Lite)."""

    prompt: str | None = Field(None, description="Natural language description of the workflow")
    context: dict[str, Any] = Field(default_factory=dict, description="Optional context (e.g. tenant, app state)")
    user_actions_snapshot: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Optional snapshot of user actions for learning",
    )


class AgentExecutionRequest(BaseModel):
    """Request body for agent execution (Nova Act)."""

    workflow_id: str = Field(..., description="ID of the approved workflow to execute")
    workflow: dict[str, Any] = Field(..., description="Full workflow definition")
    options: dict[str, Any] = Field(default_factory=dict, description="Execution options (e.g. dry_run)")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/workflow/infer")
def post_workflow_infer(body: WorkflowInferenceRequest) -> dict[str, Any]:
    """
    Infer an expense workflow from the given prompt/context using Nova 2 Lite.

    Returns a structured workflow suitable for review and approval on the dashboard.
    """
    try:
        payload = body.model_dump()
        result = infer_workflow(payload)
        logger.info("workflow_inferred", workflow_id=result.get("workflow_id"))
        return result
    except Exception as e:
        logger.exception("workflow_inference_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}") from e


@router.post("/agent/execute")
def post_agent_execute(body: AgentExecutionRequest) -> dict[str, Any]:
    """
    Execute an approved workflow via Nova Act.

    Requires workflow_id and full workflow definition; optional execution options.
    """
    try:
        result = execute_agent(
            workflow_id=body.workflow_id,
            workflow=body.workflow,
            options=body.options or None,
        )
        logger.info("agent_execution_completed", run_id=result.get("run_id"), workflow_id=body.workflow_id)
        return result
    except Exception as e:
        logger.exception("agent_execution_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Execution failed: {e}") from e


@router.get("/health")
def get_health() -> dict[str, str]:
    """Health check for load balancers and monitoring; includes mode and version."""
    return {
        "status": "ok",
        "service": "shadow-ops-expense",
        "version": "0.1.0",
        "mode": settings.nova_mode,
    }
