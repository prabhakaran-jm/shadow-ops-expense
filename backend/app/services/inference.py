"""Workflow inference from capture sessions. Mock mode is deterministic; real mode uses Nova 2 Lite."""

import json
from pathlib import Path

from fastapi import HTTPException

from app.config import settings
from app.logging_config import get_logger
from app.models import (
    CaptureSession,
    InferredWorkflow,
    WorkflowParameter,
    WorkflowStep,
)

logger = get_logger(__name__)

# Backend root (backend/ when local, /app in Docker) so prompts are inside the image
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_INFERENCE_PROMPT_PATH = _BACKEND_ROOT / "prompts" / "inference_prompt.txt"
_MAX_SAFE_PREVIEW_CHARS = 300
STRICT_PROMPT_SUFFIX = (
    "Return ONLY raw JSON, no markdown, no code fences, no commentary. "
    "First char { last char }."
)

MOCK_PARAMETERS = [
    WorkflowParameter(name="amount", type="number", required=True, example="125.50"),
    WorkflowParameter(name="date", type="date", required=True, example="2025-02-20"),
    WorkflowParameter(name="category", type="string", required=True, example="Travel"),
    WorkflowParameter(name="description", type="string", required=False, example="Client meeting"),
    WorkflowParameter(name="receipt_file", type="string", required=True, example="receipt.pdf"),
]

MOCK_STEPS = [
    WorkflowStep(
        order=1,
        intent="navigate",
        instruction="Navigate to the expense application entry URL",
        selector_hint=None,
        uses_parameters=[],
    ),
    WorkflowStep(
        order=2,
        intent="open_form",
        instruction="Open the new expense form (e.g. click 'New expense')",
        selector_hint=None,
        uses_parameters=[],
    ),
    WorkflowStep(
        order=3,
        intent="upload_receipt",
        instruction="Upload or attach the receipt file",
        selector_hint=None,
        uses_parameters=["receipt_file"],
    ),
    WorkflowStep(
        order=4,
        intent="fill_field",
        instruction="Fill amount, date, category, and description fields",
        selector_hint=None,
        uses_parameters=["amount", "date", "category", "description"],
    ),
    WorkflowStep(
        order=5,
        intent="submit_form",
        instruction="Submit the expense form",
        selector_hint=None,
        uses_parameters=[],
    ),
    WorkflowStep(
        order=6,
        intent="confirmation",
        instruction="Confirm submission if a confirmation step is shown",
        selector_hint=None,
        uses_parameters=[],
    ),
]


def _infer_workflow_mock(session: CaptureSession) -> InferredWorkflow:
    """Deterministic mock: build workflow from session using detected form fields and actions."""
    # Optional: narrow parameters/steps from session; for reproducibility we return fixed shape.
    return InferredWorkflow(
        session_id=session.session_id,
        title="Submit expense (inferred)",
        description=(
            "Creates a new expense, uploads receipt, fills amount, date, category and description, "
            "then submits and confirms. Inferred from capture session."
        ),
        parameters=list(MOCK_PARAMETERS),
        steps=list(MOCK_STEPS),
        risk_level="low",
        time_saved_minutes=5,
    )


def normalize_model_output(text: str) -> str:
    """
    Strip whitespace and remove Markdown code fences (e.g. ```json ... ```).
    Handles opening ``` or ```json on the first line and trailing ```.
    """
    text = (text or "").strip()
    # Remove opening fence: first line if it starts with ```
    if text.startswith("```"):
        idx = text.find("\n")
        if idx != -1:
            text = text[idx + 1 :].lstrip()
        else:
            text = text[3:].lstrip()
    # Remove trailing fence
    if text.rstrip().endswith("```"):
        text = text.rstrip()[:-3].rstrip()
    return text


def extract_json_object(text: str) -> str:
    """
    Return the substring from the first '{' to its matching '}' (brace-matched).
    Raises ValueError if no JSON object bounds are found.
    Ignores { and } inside double-quoted strings.
    """
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found")
    depth = 0
    in_string = False
    escape_next = False
    for i in range(start, len(text)):
        c = text[i]
        if escape_next:
            escape_next = False
            continue
        if in_string:
            if c == "\\":
                escape_next = True
            elif c == '"':
                in_string = False
            continue
        if c == '"':
            in_string = True
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise ValueError("No JSON object found")


def _parse_workflow_json(raw_text: str) -> dict:
    """
    Parse model output to a dict suitable for InferredWorkflow.
    Tries: json.loads(raw) -> normalize (strip fences) -> extract first/last { }.
    Raises HTTPException(502) with a safe preview (first 300 chars of cleaned output) if parsing fails.
    """
    raw_text = (raw_text or "").strip()
    cleaned = raw_text

    # 1) Try raw
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass

    # 2) Try normalized (strip markdown fences)
    cleaned = normalize_model_output(raw_text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 3) Try extracted (first { to last })
    try:
        extracted = extract_json_object(cleaned)
        return json.loads(extracted)
    except (ValueError, json.JSONDecodeError):
        pass

    preview = (cleaned[: _MAX_SAFE_PREVIEW_CHARS] if cleaned else "(empty)")
    raise HTTPException(
        status_code=502,
        detail=f"Inference model returned invalid JSON. Preview: {preview!r}",
    )


def _try_infer_once(prompt: str, session: CaptureSession) -> InferredWorkflow:
    """
    One attempt: call Nova, parse JSON, validate to InferredWorkflow.
    Raises HTTPException(502) on any failure (service, parse, or validation).
    """
    from app.services import nova_client

    try:
        raw = nova_client.call_nova_2_lite(prompt)
    except Exception as e:
        logger.warning("nova_inference_failed", error=str(e))
        raise HTTPException(
            status_code=502,
            detail="Inference service unavailable.",
        ) from e

    try:
        parsed = _parse_workflow_json(raw)
    except HTTPException:
        raise

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=502,
            detail="Inference model did not return a JSON object.",
        )
    parsed.setdefault("session_id", session.session_id)
    try:
        return InferredWorkflow.model_validate(parsed)
    except Exception as e:
        logger.warning("inferred_workflow_validation_failed", error=str(e))
        raise HTTPException(
            status_code=502,
            detail="Inference model output did not match workflow schema.",
        ) from e


def _infer_workflow_real(session: CaptureSession) -> InferredWorkflow:
    """Call Nova 2 Lite to infer workflow; on parse/validation failure retry once with stricter prompt."""
    if not _INFERENCE_PROMPT_PATH.exists():
        raise HTTPException(
            status_code=502,
            detail="Inference prompt file not found.",
        )
    instruction = _INFERENCE_PROMPT_PATH.read_text(encoding="utf-8").strip()
    session_json = session.model_dump_json(exclude_none=False)
    prompt = f"{instruction}\n\nInput capture session (JSON):\n{session_json}"

    try:
        return _try_infer_once(prompt, session)
    except HTTPException as e:
        if e.status_code != 502:
            raise
        logger.info(
            "inference_retry_with_strict_prompt",
            session_id=session.session_id,
        )
        retry_prompt = f"{prompt}\n\n{STRICT_PROMPT_SUFFIX}"
        try:
            return _try_infer_once(retry_prompt, session)
        except HTTPException:
            raise


def infer_workflow(session: CaptureSession) -> InferredWorkflow:
    """
    Infer an InferredWorkflow from a CaptureSession.

    Mode is controlled by env NOVA_MODE: mock (default) or real.
    - mock: deterministic workflow with parameters (amount, date, category, description, receipt_file)
      and steps (navigate, new expense, upload receipt, fill fields, submit, confirmation).
    - real: reserved for Nova 2 Lite; currently raises NotImplementedError.
    """
    mode = (settings.nova_mode or "mock").strip().lower()
    if mode == "real":
        logger.info("inference_mode_real_requested", session_id=session.session_id)
        return _infer_workflow_real(session)
    logger.info("inference_mode_mock", session_id=session.session_id)
    return _infer_workflow_mock(session)
