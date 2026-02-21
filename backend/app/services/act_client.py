"""Nova Act client: mock (deterministic) or real (SDK + browser)."""

import time
import uuid
from typing import Any

from app.config import settings
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


def _interpolate_instruction(
    instruction: str,
    uses_parameters: list[str],
    parameters: dict[str, Any],
) -> str:
    """Append param values to instruction for the given param names."""
    if not uses_parameters:
        return instruction
    parts = [instruction.strip()]
    for name in uses_parameters:
        val = parameters.get(name)
        if val is not None and val != "":
            parts.append(f"{name}: {val}")
    return " ".join(parts)


def _is_submit_step(intent: str, instruction: str) -> bool:
    """True if this step is the submit step (for UI-change simulation)."""
    instruction_lower = instruction.lower()
    intent_lower = intent.lower()
    return "submit" in intent_lower or "submit" in instruction_lower


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
        logger.info(
            "act_agent_created", agent_id=agent_id, session_id=workflow.session_id
        )
        return spec

    def run_agent(
        self,
        agent_spec: ActAgentSpec,
        parameters: dict[str, Any],
        simulate_ui_change: bool = False,
    ) -> ExecutionResult:
        """Run the agent mock: run_log and confirmation_id (e.g. EXP-2026-000123)."""
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

            if simulate_ui_change and _is_submit_step(intent, instruction):
                run_log.append(f"[{mode}] Step {i} failed: element not found")
                run_log.append(
                    "[simulate] UI changed: Submit renamed to Confirm"
                )
                run_log.append(f"[{mode}] Step {i} retry: Click Confirm to send.")

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


class ActClientReal:
    """Real Nova Act client: execute workflow steps in a browser via Nova Act SDK."""

    def create_agent(self, workflow: InferredWorkflow) -> ActAgentSpec:
        """Produce an agent spec from an inferred workflow (same as mock)."""
        agent_id = f"agent_{workflow.session_id}_{uuid.uuid4().hex[:8]}"
        spec = ActAgentSpec(
            agent_id=agent_id,
            name=workflow.title,
            description=workflow.description,
            parameter_schema=_workflow_to_parameter_schema(workflow),
            steps=_workflow_steps_as_dicts(workflow),
        )
        logger.info(
            "act_agent_created", agent_id=agent_id, session_id=workflow.session_id
        )
        return spec

    def run_agent(
        self,
        agent_spec: ActAgentSpec,
        parameters: dict[str, Any],
        simulate_ui_change: bool = False,
    ) -> ExecutionResult:
        """Run the agent via Nova Act SDK; build run_log from step results."""
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        run_log: list[str] = [
            "[execute] Starting agent: " + agent_spec.name,
            f"[execute] Run ID: {run_id}",
            f"[execute] Parameters: {parameters!r}",
        ]
        steps = sorted(
            (s for s in agent_spec.steps if isinstance(s, dict) and "order" in s),
            key=lambda s: s.get("order", 0),
        )
        try:
            from nova_act import NovaAct
        except ImportError:
            logger.warning("nova_act_not_installed_fallback_mock")
            run_log.append(
                "[execute] Nova Act SDK not installed; using mock."
            )
            return ActClientMock().run_agent(agent_spec, parameters, simulate_ui_change)

        if not (settings.nova_act_api_key or settings.nova_act_api_key.strip()):
            run_log.append("[execute] NOVA_ACT_API_KEY not set; run aborted.")
            return ExecutionResult(
                status="failed",
                confirmation_id=None,
                run_id=run_id,
                run_log=run_log,
            )

        try:
            with NovaAct(
                starting_page=settings.nova_act_starting_page,
                nova_act_api_key=settings.nova_act_api_key.strip(),
                headless=settings.nova_act_headless,
            ) as nova:
                for i, step in enumerate(steps, start=1):
                    intent = step.get("intent", "step")
                    instruction = step.get("instruction", "")
                    uses = step.get("uses_parameters") or []
                    interpolated = _interpolate_instruction(instruction, uses, parameters)
                    run_log.append(
                        f"[execute] Step {i}: {intent} – {interpolated}"
                    )
                    t0 = time.perf_counter()
                    result = nova.act(interpolated)
                    elapsed = time.perf_counter() - t0
                    logger.info(
                        "nova_act_step",
                        step=i,
                        success=result.success,
                        elapsed_sec=round(elapsed, 2),
                    )
                    if result.success:
                        run_log.append(f"[execute] Step {i}: completed")
                    else:
                        resp = getattr(result, "response", "") or "unknown"
                        run_log.append(
                            f"[execute] Step {i}: failed – {resp}"
                        )
                        if intent in ("submit_form", "confirm_action"):
                            run_log.append(
                                f"[execute] Step {i}: retrying with adapted instruction"
                            )
                            retry_instruction = (
                                f"{interpolated}. The button may have been "
                                "renamed. Look for submit/confirm buttons."
                            )
                            retry_result = nova.act(retry_instruction)
                            if retry_result.success:
                                run_log.append(f"[execute] Step {i}: retry succeeded")
                            else:
                                rresp = (
                                    getattr(retry_result, "response", "")
                                    or "unknown"
                                )
                                run_log.append(
                                    f"[execute] Step {i}: retry failed – {rresp}"
                                )

            run_log.append("[execute] All steps completed.")
            confirmation_id = f"EXP-2026-{uuid.uuid4().int % 1000000:06d}"
            run_log.append(f"[execute] Confirmation ID: {confirmation_id}")
            logger.info(
                "act_run_completed",
                run_id=run_id,
                confirmation_id=confirmation_id,
                agent_id=agent_spec.agent_id,
            )
            return ExecutionResult(
                status="completed",
                confirmation_id=confirmation_id,
                run_id=run_id,
                run_log=run_log,
            )
        except Exception as e:
            logger.exception("act_run_exception", error=str(e))
            run_log.append(f"[execute] Error: {e!s}")
            return ExecutionResult(
                status="failed",
                confirmation_id=None,
                run_id=run_id,
                run_log=run_log,
            )


def get_act_client() -> ActClientMock | ActClientReal:
    """Return ActClientReal if nova_act_mode=real, else ActClientMock."""
    mode = (settings.nova_act_mode or "mock").strip().lower()
    if mode == "real":
        return ActClientReal()
    return ActClientMock()
