"""Local disk storage helpers for capture sessions."""

import json
from pathlib import Path
from typing import Any


def _project_root() -> Path:
    """Project root (shadow-ops-expense)."""
    # backend/app/services/storage.py -> services -> app -> backend -> project root
    return Path(__file__).resolve().parent.parent.parent.parent


def sessions_dir() -> Path:
    """Directory for persisted capture sessions: demo/sessions."""
    return _project_root() / "demo" / "sessions"


def workflows_dir() -> Path:
    """Directory for persisted inferred workflows: demo/workflows."""
    return _project_root() / "demo" / "workflows"


def approvals_dir() -> Path:
    """Directory for workflow approval records: demo/approvals."""
    return _project_root() / "demo" / "approvals"


def agents_dir() -> Path:
    """Directory for generated agent specs: demo/agents."""
    return _project_root() / "demo" / "agents"


def runs_dir() -> Path:
    """Directory for execution run results: demo/runs."""
    return _project_root() / "demo" / "runs"


def list_workflow_session_ids() -> list[str]:
    """List session_ids of stored workflows (demo/workflows/*.workflow.json)."""
    directory = workflows_dir()
    if not directory.exists():
        return []
    return [
        p.name.replace(".workflow.json", "")
        for p in directory.glob("*.workflow.json")
    ]


def ensure_dir(path: Path) -> None:
    """Create directory and parents if they do not exist."""
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: dict[str, Any] | list[Any]) -> None:
    """Write data as JSON to path. Creates parent directories if needed."""
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any] | list[Any]:
    """Read and parse JSON from path. Raises FileNotFoundError if missing."""
    return json.loads(path.read_text(encoding="utf-8"))
