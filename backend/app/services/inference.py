"""Workflow inference from capture sessions. Mock mode is deterministic; real mode uses Nova 2 Lite (stub)."""

from app.config import settings
from app.logging_config import get_logger
from app.models import (
    CaptureSession,
    InferredWorkflow,
    WorkflowParameter,
    WorkflowStep,
)

logger = get_logger(__name__)

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


def _infer_workflow_real(session: CaptureSession) -> InferredWorkflow:
    """Call Nova 2 Lite to infer workflow. Not implemented yet."""
    # Extension point: load prompts/inference_prompt.txt, send session + prompt to Nova 2 Lite,
    # parse response into InferredWorkflow.
    raise NotImplementedError(
        "Nova 2 Lite inference is not implemented. Set NOVA_MODE=mock for deterministic mock, "
        "or implement _infer_workflow_real using Nova 2 Lite API."
    )


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
