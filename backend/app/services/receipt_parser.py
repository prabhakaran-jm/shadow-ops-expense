"""Receipt image parsing via Nova 2 Lite multimodal or mock."""

import json
from pathlib import Path

from fastapi import HTTPException

from app.config import settings
from app.logging_config import get_logger
from app.services.inference import extract_json_object, normalize_model_output
from app.services import nova_client

logger = get_logger(__name__)

# Backend root (backend/ when local, /app in Docker) so prompts are inside the image
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_RECEIPT_PROMPT_PATH = _BACKEND_ROOT / "prompts" / "receipt_extraction_prompt.txt"
_MAX_SAFE_PREVIEW_CHARS = 300


def _parse_receipt_json(raw_text: str) -> dict:
    """Parse model output to dict with amount, merchant, date, category, currency, confidence."""
    raw_text = (raw_text or "").strip()
    cleaned = normalize_model_output(raw_text)
    try:
        obj = json.loads(cleaned)
    except json.JSONDecodeError:
        try:
            extracted = extract_json_object(cleaned)
            obj = json.loads(extracted)
        except (ValueError, json.JSONDecodeError):
            preview = (cleaned[:_MAX_SAFE_PREVIEW_CHARS] if cleaned else "(empty)")
            raise HTTPException(
                status_code=502,
                detail=f"Receipt extraction returned invalid JSON. Preview: {preview!r}",
            ) from None
    if not isinstance(obj, dict):
        raise HTTPException(status_code=502, detail="Receipt extraction did not return a JSON object.")
    return obj


def parse_receipt(image_bytes: bytes, media_type: str) -> dict:
    """
    Extract receipt fields from image. Returns dict with keys:
    amount, merchant, date, category, currency, confidence.
    Missing fields default to null; confidence defaults to 0.0.
    """
    if settings.nova_mode == "mock":
        return {
            "amount": "45.50",
            "merchant": "Demo Cafe",
            "date": "2025-02-20",
            "category": "Meals",
            "currency": "USD",
            "confidence": 0.95,
        }
    if not _RECEIPT_PROMPT_PATH.exists():
        raise HTTPException(status_code=502, detail="Receipt extraction prompt not found.")
    prompt = _RECEIPT_PROMPT_PATH.read_text(encoding="utf-8").strip()
    try:
        raw = nova_client.call_nova_2_lite_multimodal(prompt, image_bytes, media_type)
    except Exception as e:
        logger.warning("receipt_extraction_failed", error=str(e))
        raise HTTPException(status_code=502, detail="Receipt extraction service unavailable.") from e
    try:
        obj = _parse_receipt_json(raw)
    except HTTPException:
        raise
    out = {
        "amount": obj.get("amount"),
        "merchant": obj.get("merchant"),
        "date": obj.get("date"),
        "category": obj.get("category"),
        "currency": obj.get("currency"),
        "confidence": obj.get("confidence"),
    }
    if out["confidence"] is not None and not isinstance(out["confidence"], (int, float)):
        out["confidence"] = 0.0
    elif out["confidence"] is None:
        out["confidence"] = 0.0
    return out
