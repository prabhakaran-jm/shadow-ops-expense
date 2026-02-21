"""Receipt upload logic: parse image, create session, run inference."""

import uuid

from fastapi import HTTPException, UploadFile

from app.logging_config import get_logger
from app.models import CaptureSession, CaptureStep
from app.services.inference import infer_workflow
from app.services.receipt_parser import parse_receipt
from app.services.storage import sessions_dir, workflows_dir, write_json

logger = get_logger(__name__)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10MB


def _synthetic_steps(extracted: dict) -> list[dict]:
    """Build CaptureStep-like dicts from extracted receipt fields."""
    steps = [
        {
            "step_index": 0,
            "url": "/expense/dashboard",
            "action": "navigate",
            "element_text": None,
            "field_label": None,
            "value_redacted": None,
            "screenshot_path": None,
            "timestamp": None,
        },
        {
            "step_index": 1,
            "url": "/expense/new",
            "action": "type",
            "element_text": None,
            "field_label": "amount",
            "value_redacted": str(extracted.get("amount") or ""),
            "screenshot_path": None,
            "timestamp": None,
        },
        {
            "step_index": 2,
            "url": "/expense/new",
            "action": "type",
            "element_text": None,
            "field_label": "merchant",
            "value_redacted": str(extracted.get("merchant") or ""),
            "screenshot_path": None,
            "timestamp": None,
        },
        {
            "step_index": 3,
            "url": "/expense/new",
            "action": "type",
            "element_text": None,
            "field_label": "date",
            "value_redacted": str(extracted.get("date") or ""),
            "screenshot_path": None,
            "timestamp": None,
        },
        {
            "step_index": 4,
            "url": "/expense/new",
            "action": "select",
            "element_text": None,
            "field_label": "category",
            "value_redacted": str(extracted.get("category") or ""),
            "screenshot_path": None,
            "timestamp": None,
        },
    ]
    return steps


async def process_receipt_upload(file: UploadFile) -> dict:
    """
    Upload receipt image: extract fields (Nova 2 Lite multimodal or mock), create
    CaptureSession, run inference, store workflow. Returns session_id, extracted, workflow_inferred.
    """
    if not file.content_type or file.content_type.lower() not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type. Allowed: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
        )
    body = await file.read()
    if len(body) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_FILE_BYTES // (1024*1024)}MB",
        )
    logger.info(
        "receipt_upload_received",
        file_size=len(body),
        media_type=file.content_type,
    )
    extracted = parse_receipt(body, file.content_type or "image/jpeg")
    session_id = f"receipt_{uuid.uuid4().hex[:12]}"
    steps_data = _synthetic_steps(extracted)
    steps = [CaptureStep.model_validate(s) for s in steps_data]
    session = CaptureSession(session_id=session_id, steps=steps, metadata={"source": "receipt_upload"})
    session_path = sessions_dir() / f"{session_id}.json"
    write_json(session_path, session.model_dump(mode="json"))
    workflow = infer_workflow(session)
    workflow_path = workflows_dir() / f"{session_id}.workflow.json"
    write_json(workflow_path, workflow.model_dump(mode="json"))
    logger.info(
        "receipt_pipeline_complete",
        session_id=session_id,
        workflow_inferred=True,
    )
    return {
        "session_id": session_id,
        "extracted": extracted,
        "workflow_inferred": True,
    }
