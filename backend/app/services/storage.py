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
