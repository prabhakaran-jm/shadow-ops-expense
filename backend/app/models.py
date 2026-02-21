"""Core data contracts as Pydantic models."""

from pydantic import BaseModel, Field


class CaptureStep(BaseModel):
    """A single step in a captured user session (e.g. UI interaction)."""

    step_index: int = Field(..., description="0-based index of the step in the session")
    url: str = Field(..., description="Page or screen URL where the action occurred")
    action: str = Field(..., description="Type of action (e.g. click, type, select)")
    element_text: str | None = Field(None, description="Visible text of the target element")
    field_label: str | None = Field(None, description="Label of the form field if applicable")
    value_redacted: str | None = Field(None, description="Redacted or masked value entered (e.g. for PII)")
    screenshot_path: str | None = Field(None, description="Path or reference to a screenshot of the step")
    timestamp: str | None = Field(None, description="ISO-8601 timestamp when the step was captured")


class CaptureSession(BaseModel):
    """A recorded session of user actions used as input for workflow inference."""

    session_id: str = Field(..., description="Unique identifier for the capture session")
    steps: list[CaptureStep] = Field(..., description="Ordered list of captured steps")
    metadata: dict | None = Field(None, description="Optional session metadata (e.g. app version, tenant)")


class WorkflowParameter(BaseModel):
    """Declared parameter for an inferred workflow (e.g. amount, category)."""

    name: str = Field(..., description="Parameter name (e.g. expense_amount)")
    type: str = Field(..., description="Value type (e.g. string, number, date)")
    required: bool = Field(True, description="Whether the parameter must be supplied at execution")
    example: str | None = Field(None, description="Example value for documentation or UI")


class WorkflowStep(BaseModel):
    """A single step in an inferred workflow (intent + instruction for the agent)."""

    order: int = Field(..., description="Step order (1-based or execution order)")
    intent: str = Field(..., description="High-level intent (e.g. fill_field, submit_form)")
    instruction: str = Field(..., description="Natural language or structured instruction for the agent")
    selector_hint: str | None = Field(None, description="Optional selector or locator hint for the target element")
    uses_parameters: list[str] = Field(
        default_factory=list,
        description="Names of WorkflowParameters this step consumes",
    )


class InferredWorkflow(BaseModel):
    """Full inferred workflow produced from a capture session or prompt."""

    session_id: str = Field(..., description="ID of the capture session this workflow was inferred from")
    title: str = Field(..., description="Short human-readable title")
    description: str = Field(..., description="Longer description of what the workflow does")
    parameters: list[WorkflowParameter] = Field(
        default_factory=list,
        description="Parameters the workflow accepts at execution",
    )
    steps: list[WorkflowStep] = Field(..., description="Ordered steps to be executed by the agent")
    risk_level: str = Field(..., description="Assessed risk level (e.g. low, medium, high)")
    time_saved_minutes: int = Field(..., description="Estimated minutes saved per run when automated")


# ---------------------------------------------------------------------------
# Agent generation and execution (Nova Act scaffolding)
# ---------------------------------------------------------------------------


class ActAgentSpec(BaseModel):
    """Spec for an agent generated from an approved workflow."""

    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="What the agent does")
    parameter_schema: dict = Field(
        default_factory=dict,
        description="JSON Schema for execution parameters",
    )
    steps: list[dict] = Field(
        default_factory=list,
        description="Ordered steps (e.g. from workflow)",
    )


class ExecutionRequest(BaseModel):
    """Request to run an agent."""

    parameters: dict = Field(default_factory=dict, description="Parameter values")
    simulate_ui_change: bool = Field(
        False,
        description="If true, simulate UI changes without performing them",
    )


class ExecutionResult(BaseModel):
    """Result of an agent run."""

    status: str = Field(..., description="e.g. completed, failed")
    confirmation_id: str | None = Field(None, description="e.g. EXP-2026-000123")
    run_id: str = Field(..., description="Unique run identifier")
    run_log: list[str] = Field(
        default_factory=list,
        description="Step-by-step log messages",
    )


class ReceiptExtractionResult(BaseModel):
    """Result of receipt upload: session_id, extracted fields, workflow_inferred."""

    session_id: str = Field(..., description="Created capture session id")
    extracted: dict = Field(..., description="amount, merchant, date, category, currency, confidence")
    workflow_inferred: bool = Field(..., description="Whether inference was run and stored")
