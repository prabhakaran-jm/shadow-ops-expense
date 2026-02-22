"""Tests for Nova Act client: _interpolate_instruction, _workflow_to_parameter_schema, mock create/run."""
from app.models import ActAgentSpec, InferredWorkflow, WorkflowParameter, WorkflowStep
from app.services.act_client import (
    ActClientMock,
    _interpolate_instruction,
    _workflow_to_parameter_schema,
)


class TestInterpolateInstruction:
    def test_empty_uses_parameters_returns_instruction(self):
        assert _interpolate_instruction("Do the thing", [], {}) == "Do the thing"

    def test_appends_param_values(self):
        out = _interpolate_instruction(
            "Fill amount",
            ["amount", "date"],
            {"amount": "100", "date": "2025-02-20"},
        )
        assert "amount: 100" in out
        assert "date: 2025-02-20" in out

    def test_skips_missing_or_empty(self):
        out = _interpolate_instruction(
            "Fill",
            ["a", "b"],
            {"a": "x", "b": ""},
        )
        assert "a: x" in out
        assert "b:" not in out or "b: " in out  # empty skipped


class TestWorkflowToParameterSchema:
    def test_minimal_workflow(self):
        w = InferredWorkflow(
            session_id="s1",
            title="T",
            description="D",
            parameters=[
                WorkflowParameter(name="amount", type="number", required=True, example="10"),
                WorkflowParameter(name="note", type="string", required=False),
            ],
            steps=[],
            risk_level="low",
            time_saved_minutes=5,
        )
        schema = _workflow_to_parameter_schema(w)
        assert schema["type"] == "object"
        assert "amount" in schema["properties"]
        assert "note" in schema["properties"]
        assert "amount" in schema["required"]
        assert "note" not in schema["required"]


def _minimal_workflow() -> InferredWorkflow:
    return InferredWorkflow(
        session_id="test-session",
        title="Test workflow",
        description="Test",
        parameters=[WorkflowParameter(name="x", type="string", required=True)],
        steps=[
            WorkflowStep(order=1, intent="fill", instruction="Fill x", uses_parameters=["x"]),
        ],
        risk_level="low",
        time_saved_minutes=1,
    )


class TestActClientMock:
    def test_create_agent_returns_spec(self):
        mock = ActClientMock()
        workflow = _minimal_workflow()
        spec = mock.create_agent(workflow)
        assert isinstance(spec, ActAgentSpec)
        assert spec.agent_id.startswith("agent_test-session_")
        assert spec.name == "Test workflow"
        assert len(spec.steps) == 1

    def test_run_agent_returns_completed_result(self):
        mock = ActClientMock()
        workflow = _minimal_workflow()
        spec = mock.create_agent(workflow)
        result = mock.run_agent(spec, {"x": "hello"}, simulate_ui_change=False)
        assert result.status == "completed"
        assert result.run_id.startswith("run_")
        assert result.confirmation_id is not None
        assert "EXP-" in (result.confirmation_id or "")
        assert len(result.run_log) >= 1
