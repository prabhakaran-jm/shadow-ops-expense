"""Mock Nova Act client for agent generation and execution."""

import uuid
from typing import Any

from app.logging_config import get_logger
from app.models import ActAgentSpec, ExecutionResult, InferredWorkflow

logger = get_logger(__name__)


def _workflow_to_parameter_schema(workflow: InferredWorkflow) -> dict[str, Any]:
    """Build a minimal JSON Schema for workflow parameters."""
    props = {}
    for p in workflow.parameters:
        props[p.name] = {
            "type": p.type,
            "description": f"Parameter: {p.name}",
        }
        if p.example is not None:
            props[p.name]["example"] = p.example
    return {
        "type": "object",
        "properties": props,
        "required": [p.name for p in workflow.parameters if p.required],
    }


def _workflow_steps_as_dicts(workflow: InferredWorkflow) -> list[dict[str, Any]]:
    """Convert workflow steps to serializable dicts for agent spec."""
    return [s.model_dump(mode="json") for s in workflow.steps]


class ActClientMock:
    """Mock Nova Act client: create_agent from workflow, run_agent with step log."""

    def create_agent(self, workflow: InferredWorkflow) -> ActAgentSpec:
        """Produce an agent spec from an inferred workflow."""
        agent_id = f"agent_{workflow.session_id}_{uuid.uuid4().hex[:8]}"
        spec = ActAgentSpec(
            agent_id=agent_id,
            name=workflow.title,
            description=workflow.description,
            parameter_schema=_workflow_to_parameter_schema(workflow),
            steps=_workflow_steps_as_dicts(workflow),
        )
        logger.info("act_agent_created", agent_id=agent_id, session_id=workflow.session_id)
        return spec

    def run_agent(
        self,
        agent_spec: ActAgentSpec,
        parameters: dict[str, Any],
        simulate_ui_change: bool = False,
    ) -> ExecutionResult:
        """Run the agent mock: produce run_log and a confirmation_id like EXP-2026-000123."""
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        mode = "simulate" if simulate_ui_change else "execute"
        run_log: list[str] = [
            f"[{mode}] Starting agent: {agent_spec.name}",
            f"[{mode}] Run ID: {run_id}",
            f"[{mode}] Parameters: {parameters!r}",
        ]
        steps = sorted(
            (s for s in agent_spec.steps if isinstance(s, dict) and "order" in s),
            key=lambda s: s.get("order", 0),
        )
        for i, step in enumerate(steps, start=1):
            intent = step.get("intent", "step")
            instruction = step.get("instruction", "")
            run_log.append(f"[{mode}] Step {i}: {intent} – {instruction}")
        run_log.append(f"[{mode}] All steps completed.")
        confirmation_id = f"EXP-2026-{uuid.uuid4().int % 1000000:06d}"
        run_log.append(f"[{mode}] Confirmation ID: {confirmation_id}")

        result = ExecutionResult(
            status="completed",
            confirmation_id=confirmation_id,
            run_id=run_id,
            run_log=run_log,
        )
        logger.info(
            "act_run_completed",
            run_id=run_id,
            confirmation_id=confirmation_id,
            agent_id=agent_spec.agent_id,
        )
        return result
