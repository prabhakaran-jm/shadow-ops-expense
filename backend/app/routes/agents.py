"""Agent generation and execution: generate from approved workflow, run via Nova Act."""

import threading

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.logging_config import get_logger
from app.models import ActAgentSpec, ExecutionRequest, ExecutionResult, InferredWorkflow
from app.services.act_client import get_act_client
from app.services.storage import (
    agents_dir,
    approvals_dir,
    read_json,
    runs_dir,
    write_json,
    workflows_dir,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])
act_client = get_act_client()

# In-flight runs tracked by run_id so we can poll status
_pending_runs: dict[str, dict] = {}  # run_id -> {"session_id": ..., "status": "running"}


@router.post("/{session_id}/generate")
def post_agents_generate(session_id: str) -> dict:
    """
    Generate agent spec from an approved workflow.
    Requires approval to exist; loads workflow, creates agent, stores demo/agents/{session_id}.agent.json.
    """
    approval_path = approvals_dir() / f"{session_id}.json"
    if not approval_path.exists():
        logger.info("agent_generate_not_approved", session_id=session_id)
        raise HTTPException(
            status_code=400,
            detail="Workflow must be approved before generating an agent",
        )

    workflow_path = workflows_dir() / f"{session_id}.workflow.json"
    if not workflow_path.exists():
        logger.info("agent_generate_workflow_missing", session_id=session_id)
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow_data = read_json(workflow_path)
    workflow = InferredWorkflow.model_validate(workflow_data)
    spec = act_client.create_agent(workflow)
    agent_path = agents_dir() / f"{session_id}.agent.json"
    write_json(agent_path, spec.model_dump(mode="json"))
    logger.info(
        "agent_generated",
        session_id=session_id,
        agent_id=spec.agent_id,
        path=str(agent_path),
    )
    return spec.model_dump(mode="json")


def _run_agent_background(
    session_id: str,
    run_id: str,
    agent_spec: ActAgentSpec,
    parameters: dict,
    simulate_ui_change: bool,
) -> None:
    """Execute agent in a background thread; write result to disk when done."""
    try:
        result = act_client.run_agent(agent_spec, parameters, simulate_ui_change)
        result_dict = result.model_dump(mode="json")
        result_dict["run_id"] = run_id
        run_path = runs_dir() / f"{run_id}.json"
        write_json(run_path, result_dict)
        _pending_runs[run_id] = {"session_id": session_id, "status": "completed"}
        logger.info("agent_run_stored", session_id=session_id, run_id=run_id)
    except Exception as e:
        logger.exception("agent_run_background_error", run_id=run_id, error=str(e))
        error_result = ExecutionResult(
            status="failed",
            confirmation_id=None,
            run_id=run_id,
            run_log=[f"[nova-act] Background error: {e!s}"],
        )
        run_path = runs_dir() / f"{run_id}.json"
        write_json(run_path, error_result.model_dump(mode="json"))
        _pending_runs[run_id] = {"session_id": session_id, "status": "failed"}


@router.post("/{session_id}/run")
def post_agents_run(session_id: str, body: ExecutionRequest) -> dict:
    """
    Execute agent. Runs synchronously for mock/simulate, async for real Nova Act.

    For real Nova Act mode (without simulate), launches a background thread
    and returns {status: 'running', run_id: '...'}. Poll the GET endpoint.

    For mock mode or simulate, returns the full result synchronously.
    """
    agent_path = agents_dir() / f"{session_id}.agent.json"
    if not agent_path.exists():
        logger.info("agent_run_spec_missing", session_id=session_id)
        raise HTTPException(
            status_code=404,
            detail="Agent not found; generate the agent first",
        )

    agent_data = read_json(agent_path)
    agent_spec = ActAgentSpec.model_validate(agent_data)

    from app.config import settings
    is_real = (settings.nova_act_mode or "mock").strip().lower() == "real"

    if is_real and not body.simulate_ui_change:
        # Real Nova Act: run in background thread to avoid App Runner timeout
        import uuid
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        _pending_runs[run_id] = {"session_id": session_id, "status": "running"}

        thread = threading.Thread(
            target=_run_agent_background,
            args=(session_id, run_id, agent_spec, body.parameters, body.simulate_ui_change),
            daemon=False,  # Non-daemon so it survives after response
        )
        thread.start()
        logger.info("agent_run_started_async", session_id=session_id, run_id=run_id)

        return {
            "status": "running",
            "run_id": run_id,
            "confirmation_id": None,
            "run_log": [
                f"[nova-act] Agent execution started in background",
                f"[nova-act] Run ID: {run_id}",
                f"[nova-act] Poll GET /api/agents/{session_id}/run/{run_id} for result",
            ],
            "message": "Agent execution started. Polling for result...",
        }
    else:
        # Sync: mock mode or simulate_ui_change
        result = act_client.run_agent(
            agent_spec,
            body.parameters,
            simulate_ui_change=body.simulate_ui_change,
        )
        run_path = runs_dir() / f"{result.run_id}.json"
        write_json(run_path, result.model_dump(mode="json"))
        logger.info(
            "agent_run_stored",
            session_id=session_id,
            run_id=result.run_id,
        )
        return result.model_dump(mode="json")


@router.get("/{session_id}/run/{run_id}")
def get_agent_run_status(session_id: str, run_id: str) -> dict:
    """
    Poll for agent run result. Returns the run result if completed,
    or {status: 'running'} if still in progress.
    """
    # Check if result file exists on disk
    run_path = runs_dir() / f"{run_id}.json"
    if run_path.exists():
        return read_json(run_path)

    # Check in-memory pending status
    pending = _pending_runs.get(run_id)
    if pending and pending["status"] == "running":
        return {"status": "running", "run_id": run_id, "confirmation_id": None, "run_log": []}

    raise HTTPException(status_code=404, detail="Run not found")
