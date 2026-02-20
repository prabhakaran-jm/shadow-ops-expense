"""GET /schemas – example JSON payloads for core data contracts."""

from fastapi import APIRouter

from app.models import (
    CaptureSession,
    CaptureStep,
    InferredWorkflow,
    WorkflowParameter,
    WorkflowStep,
)

router = APIRouter(tags=["schemas"])


def _example_capture_session() -> dict:
    """Build example CaptureSession as JSON-serializable dict."""
    example = CaptureSession(
        session_id="cap_20250220_001",
        steps=[
            CaptureStep(
                step_index=0,
                url="https://expense.example.com/new",
                action="click",
                element_text="New expense",
                field_label=None,
                value_redacted=None,
                screenshot_path="/captures/cap_001_step_0.png",
                timestamp="2025-02-20T10:00:00Z",
            ),
            CaptureStep(
                step_index=1,
                url="https://expense.example.com/new",
                action="type",
                element_text="",
                field_label="Amount",
                value_redacted="***",
                screenshot_path="/captures/cap_001_step_1.png",
                timestamp="2025-02-20T10:00:15Z",
            ),
            CaptureStep(
                step_index=2,
                url="https://expense.example.com/new",
                action="click",
                element_text="Submit",
                field_label=None,
                value_redacted=None,
                screenshot_path="/captures/cap_001_step_2.png",
                timestamp="2025-02-20T10:00:45Z",
            ),
        ],
        metadata={"app_version": "2.1", "tenant_id": "acme"},
    )
    return example.model_dump(mode="json")


def _example_inferred_workflow() -> dict:
    """Build example InferredWorkflow as JSON-serializable dict."""
    example = InferredWorkflow(
        session_id="cap_20250220_001",
        title="Submit travel expense",
        description=(
            "Creates a new travel expense, fills amount and category, "
            "attaches receipt, and submits for approval."
        ),
        parameters=[
            WorkflowParameter(
                name="expense_amount",
                type="number",
                required=True,
                example="125.50",
            ),
            WorkflowParameter(
                name="category",
                type="string",
                required=True,
                example="Travel",
            ),
        ],
        steps=[
            WorkflowStep(
                order=1,
                intent="navigate",
                instruction="Open the new expense form",
                selector_hint="a[href='/new']",
                uses_parameters=[],
            ),
            WorkflowStep(
                order=2,
                intent="fill_field",
                instruction="Enter the expense amount in the Amount field",
                selector_hint="input[name='amount']",
                uses_parameters=["expense_amount"],
            ),
            WorkflowStep(
                order=3,
                intent="fill_field",
                instruction="Select the expense category",
                selector_hint="select[name='category']",
                uses_parameters=["category"],
            ),
            WorkflowStep(
                order=4,
                intent="submit_form",
                instruction="Click Submit to send the expense for approval",
                selector_hint="button[type='submit']",
                uses_parameters=[],
            ),
        ],
        risk_level="low",
        time_saved_minutes=5,
    )
    return example.model_dump(mode="json")


@router.get("/schemas")
def get_schemas() -> dict:
    """
    Return example JSON for CaptureSession and InferredWorkflow.

    Use as reference for request/response shapes and integration tests.
    """
    return {
        "CaptureSession": _example_capture_session(),
        "InferredWorkflow": _example_inferred_workflow(),
    }
