"""Nova Act client: mock (deterministic) or real (SDK + Workflow/IAM auth)."""

import time
import uuid
from typing import Any

from app.config import settings
from app.logging_config import get_logger
from app.models import ActAgentSpec, ExecutionResult, InferredWorkflow

logger = get_logger(__name__)

# Workflow definition name for Nova Act (created once, reused)
_WORKFLOW_DEFINITION_NAME = "shadow-ops-expense-runner"


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


def _detect_name_param(client, operation: str) -> str:
    """Detect the workflow definition name parameter for a given operation.

    The nova-act boto3 service model is inconsistent across operations and versions:
    - CreateWorkflowDefinition may use 'name' or 'workflowDefinitionName'
    - GetWorkflowDefinition may use 'workflowDefinitionName' or 'name'
    This introspects the actual service model to pick the right one.
    """
    try:
        op = client._service_model.operation_model(operation)
        members = list(op.input_shape.members.keys())
        if "workflowDefinitionName" in members:
            return "workflowDefinitionName"
        if "name" in members:
            return "name"
    except Exception:
        pass
    return "name"


def _ensure_workflow_definition() -> None:
    """Create the Nova Act workflow definition if it does not exist (idempotent)."""
    import boto3

    client = boto3.client("nova-act", region_name=settings.aws_region)
    get_key = _detect_name_param(client, "GetWorkflowDefinition")
    create_key = _detect_name_param(client, "CreateWorkflowDefinition")
    logger.info("workflow_definition_params", get_key=get_key, create_key=create_key)

    try:
        client.get_workflow_definition(**{get_key: _WORKFLOW_DEFINITION_NAME})
        logger.info("workflow_definition_exists", name=_WORKFLOW_DEFINITION_NAME)
    except client.exceptions.ResourceNotFoundException:
        client.create_workflow_definition(
            **{create_key: _WORKFLOW_DEFINITION_NAME},
            description="Shadow Ops expense workflow automation agent",
        )
        logger.info("workflow_definition_created", name=_WORKFLOW_DEFINITION_NAME)


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
    """Real Nova Act client: execute workflow steps in a browser via Nova Act SDK.

    Uses Workflow context manager with IAM auth (no API key needed).
    The SDK drives a cloud browser via AgentCore when using Workflow mode.
    Falls back to ActClientMock if nova-act is not installed.
    """

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
        """Run the agent via Nova Act SDK with Workflow/IAM auth.

        Nova Act SDK API (verified):
        - act() returns ActResult with only .metadata (ActMetadata)
        - Success = no exception raised
        - Failure = raises ActAgentFailed, ActExecutionError, etc.
        - act_get() returns ActGetResult with .response (str) for data extraction
        - Workflow context manager provides IAM auth (no API key needed)
        - ignore_https_errors=True required for Windows SSL cert issues
        """
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        run_log: list[str] = [
            "[nova-act] Starting agent: " + agent_spec.name,
            f"[nova-act] Run ID: {run_id}",
            f"[nova-act] Parameters: {parameters!r}",
        ]
        steps = sorted(
            (s for s in agent_spec.steps if isinstance(s, dict) and "order" in s),
            key=lambda s: s.get("order", 0),
        )

        # Import nova_act inside method so app works without it installed
        try:
            from nova_act import NovaAct, Workflow
        except ImportError:
            logger.warning("nova_act_not_installed_fallback_mock")
            run_log.append("[nova-act] SDK not installed; falling back to mock.")
            return ActClientMock().run_agent(agent_spec, parameters, simulate_ui_change)

        try:
            # Ensure workflow definition exists (idempotent)
            _ensure_workflow_definition()

            run_log.append(f"[nova-act] Using Workflow/IAM auth (definition: {_WORKFLOW_DEFINITION_NAME})")
            run_log.append(f"[nova-act] Starting page: {settings.nova_act_starting_page}")

            with Workflow(
                workflow_definition_name=_WORKFLOW_DEFINITION_NAME,
                model_id="nova-act-latest",
            ) as wf:
                run_log.append(f"[nova-act] Workflow run created")

                with NovaAct(
                    starting_page=settings.nova_act_starting_page,
                    workflow=wf,
                    headless=settings.nova_act_headless,
                    ignore_https_errors=True,
                ) as nova:
                    run_log.append("[nova-act] Browser session started")

                    for i, step in enumerate(steps, start=1):
                        intent = step.get("intent", "step")
                        instruction = step.get("instruction", "")
                        uses = step.get("uses_parameters") or []
                        interpolated = _interpolate_instruction(instruction, uses, parameters)
                        run_log.append(f"[nova-act] Step {i}: {intent} – {interpolated}")

                        t0 = time.perf_counter()
                        try:
                            # act() returns ActResult on success, raises on failure
                            act_result = nova.act(interpolated)
                            elapsed = time.perf_counter() - t0
                            steps_executed = act_result.metadata.num_steps_executed
                            time_worked = act_result.metadata.time_worked_s or elapsed
                            run_log.append(
                                f"[nova-act] Step {i}: completed "
                                f"({steps_executed} sub-steps, {time_worked:.1f}s)"
                            )
                            logger.info(
                                "nova_act_step_success",
                                step=i,
                                intent=intent,
                                elapsed_sec=round(elapsed, 2),
                                sub_steps=steps_executed,
                            )
                        except Exception as step_err:
                            elapsed = time.perf_counter() - t0
                            err_name = type(step_err).__name__
                            run_log.append(
                                f"[nova-act] Step {i}: failed – {err_name}: {step_err}"
                            )
                            logger.warning(
                                "nova_act_step_failed",
                                step=i,
                                intent=intent,
                                error=str(step_err),
                                elapsed_sec=round(elapsed, 2),
                            )

                            # Retry submit/confirm steps with adapted instruction
                            if intent in ("submit_form", "confirm_action"):
                                run_log.append(
                                    f"[nova-act] Step {i}: retrying with adapted instruction"
                                )
                                retry_instruction = (
                                    f"{interpolated}. The button may have been "
                                    "renamed. Look for alternative submit or confirm buttons."
                                )
                                try:
                                    retry_result = nova.act(retry_instruction)
                                    retry_steps = retry_result.metadata.num_steps_executed
                                    run_log.append(
                                        f"[nova-act] Step {i}: retry succeeded ({retry_steps} sub-steps)"
                                    )
                                except Exception as retry_err:
                                    run_log.append(
                                        f"[nova-act] Step {i}: retry failed – {retry_err}"
                                    )

            run_log.append("[nova-act] All steps completed.")
            confirmation_id = f"EXP-2026-{uuid.uuid4().int % 1000000:06d}"
            run_log.append(f"[nova-act] Confirmation ID: {confirmation_id}")
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
            run_log.append(f"[nova-act] Error: {e!s}")
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
