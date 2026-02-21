"""Agent generation and execution: generate from approved workflow, run mock."""

from fastapi import APIRouter, HTTPException

from app.logging_config import get_logger
from app.models import ActAgentSpec, ExecutionRequest, ExecutionResult, InferredWorkflow
from app.services.act_client import ActClientMock
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
act_client = ActClientMock()


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


@router.post("/{session_id}/run")
def post_agents_run(session_id: str, body: ExecutionRequest) -> ExecutionResult:
    """
    Load agent spec, run mock execution, store demo/runs/{run_id}.json, return result.
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
        path=str(run_path),
    )
    return result
