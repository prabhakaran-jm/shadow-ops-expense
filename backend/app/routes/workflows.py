"""Workflow review APIs: list, get by id, approve."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.logging_config import get_logger
from app.services.storage import (
    approvals_dir,
    list_workflow_session_ids,
    read_json,
    write_json,
    workflows_dir,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("")
def get_workflows() -> list[dict]:
    """
    List inferred workflows from demo/workflows/*.workflow.json.

    Returns array of {session_id, title, risk_level, time_saved_minutes}.
    """
    session_ids = list_workflow_session_ids()
    result = []
    for sid in session_ids:
        path = workflows_dir() / f"{sid}.workflow.json"
        try:
            data = read_json(path)
            result.append({
                "session_id": sid,
                "title": data.get("title", ""),
                "risk_level": data.get("risk_level", ""),
                "time_saved_minutes": data.get("time_saved_minutes", 0),
            })
        except (FileNotFoundError, TypeError, KeyError):
            continue
    logger.info("workflows_listed", count=len(result))
    return result


@router.get("/{session_id}")
def get_workflow(session_id: str) -> dict:
    """Return full workflow JSON for the given session_id, or 404."""
    path = workflows_dir() / f"{session_id}.workflow.json"
    if not path.exists():
        logger.info("workflow_not_found", session_id=session_id)
        raise HTTPException(status_code=404, detail="workflow not found")
    data = read_json(path)
    logger.info("workflow_loaded", session_id=session_id)
    return data


@router.post("/{session_id}/approve")
def post_workflow_approve(session_id: str) -> dict:
    """
    Record approval under demo/approvals/{session_id}.json with timestamp.
    Returns {approved: true}.
    """
    path = workflows_dir() / f"{session_id}.workflow.json"
    if not path.exists():
        logger.info("workflow_approve_not_found", session_id=session_id)
        raise HTTPException(status_code=404, detail="workflow not found")

    approval = {
        "approved": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    approval_path = approvals_dir() / f"{session_id}.json"
    write_json(approval_path, approval)
    logger.info("workflow_approved", session_id=session_id, path=str(approval_path))
    return {"approved": True}
