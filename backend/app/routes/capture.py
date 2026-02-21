"""Capture session storage and receipt upload."""

from fastapi import APIRouter, HTTPException, UploadFile

from app.logging_config import get_logger
from app.models import CaptureSession
from app.routes.receipt import process_receipt_upload
from app.services.storage import read_json, sessions_dir, write_json

logger = get_logger(__name__)

router = APIRouter(prefix="/capture", tags=["capture"])

MAX_STEPS = 200


@router.post("/sessions")
def post_capture_sessions(session: CaptureSession) -> dict:
    """
    Store a capture session to disk under demo/sessions/{session_id}.json.

    Validates: steps not empty, at most 200 steps.
    """
    steps = session.steps
    if not steps:
        logger.warning(
            "capture_session_rejected",
            reason="steps_empty",
            session_id=session.session_id,
        )
        raise HTTPException(status_code=400, detail="steps must not be empty")
    if len(steps) > MAX_STEPS:
        logger.warning(
            "capture_session_rejected",
            reason="steps_over_limit",
            session_id=session.session_id,
            count=len(steps),
            max=MAX_STEPS,
        )
        raise HTTPException(
            status_code=400,
            detail=f"steps must have at most {MAX_STEPS} items",
        )

    path = sessions_dir() / f"{session.session_id}.json"
    data = session.model_dump(mode="json")
    write_json(path, data)
    logger.info(
        "capture_session_stored",
        session_id=session.session_id,
        steps=len(steps),
        path=str(path),
    )
    return {"session_id": session.session_id, "stored": True}


@router.get("/sessions/{session_id}")
def get_capture_session(session_id: str) -> dict:
    """Load and return a stored capture session by id, or 404."""
    path = sessions_dir() / f"{session_id}.json"
    if not path.exists():
        logger.info("capture_session_not_found", session_id=session_id)
        raise HTTPException(status_code=404, detail="session not found")
    data = read_json(path)
    logger.info("capture_session_loaded", session_id=session_id)
    return data


@router.get("/receipt")
def get_receipt_info():
    """Debug: confirms receipt endpoint is reachable. Use POST with multipart file for upload."""
    return {"ok": True, "message": "Use POST with multipart/form-data and 'file' field to upload a receipt."}


@router.post("/receipt")
async def post_capture_receipt(file: UploadFile) -> dict:
    """Receipt image upload: extract, create session, infer workflow."""
    return await process_receipt_upload(file)
