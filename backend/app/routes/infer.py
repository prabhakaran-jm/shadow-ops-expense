"""Workflow inference: load session, infer workflow, persist and return."""

from fastapi import APIRouter, HTTPException

from app.logging_config import get_logger
from app.models import CaptureSession
from app.services.inference import infer_workflow
from app.services.storage import read_json, sessions_dir, workflows_dir, write_json

logger = get_logger(__name__)

router = APIRouter(prefix="/infer", tags=["infer"])


@router.post("/{session_id}")
def post_infer_session(session_id: str) -> dict:
    """
    Load capture session from demo/sessions, run inference, store workflow
    under demo/workflows/{session_id}.workflow.json, and return the inferred workflow.
    """
    session_path = sessions_dir() / f"{session_id}.json"
    if not session_path.exists():
        logger.info("infer_session_not_found", session_id=session_id)
        raise HTTPException(status_code=404, detail="session not found")

    session_data = read_json(session_path)
    session = CaptureSession.model_validate(session_data)
    logger.info("infer_session_loaded", session_id=session_id, steps=len(session.steps))

    workflow = infer_workflow(session)
    workflow_path = workflows_dir() / f"{session_id}.workflow.json"
    write_json(workflow_path, workflow.model_dump(mode="json"))
    logger.info(
        "infer_workflow_stored",
        session_id=session_id,
        path=str(workflow_path),
    )

    return workflow.model_dump(mode="json")