#!/usr/bin/env python3
"""
Run the full demo flow against a local backend (mock mode).

Calls GET /api/health first (retries 3x) then capture → infer → approve → generate → run.
BASE_URL defaults to http://localhost:8000/api (all paths are relative to that).
Override with DEMO_BASE_URL (e.g. http://localhost:8000/api or http://host:port/api).

Usage:
  From repo root:  python backend/scripts/demo_flow.py
  From backend/:   python scripts/demo_flow.py
"""

import json
import os
import sys
import time
from pathlib import Path

import urllib.error
import urllib.request

_SCRIPT_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _SCRIPT_DIR.parent
_PROJECT_ROOT = _BACKEND_DIR.parent
SAMPLE_LOGS_PATH = _PROJECT_ROOT / "demo" / "sample_logs.json"

# Single base URL including /api; paths are e.g. /health, /capture/sessions
BASE_URL = os.environ.get("DEMO_BASE_URL", "http://localhost:8000/api").rstrip("/")

SAMPLE_PARAMETERS = {
    "amount": "125.50",
    "date": "2025-02-20",
    "category": "Travel",
    "description": "Client meeting",
    "receipt_file": "receipt.pdf",
}

HEALTH_RETRIES = 3
HEALTH_DELAY_SEC = 1.0


def _request(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} {path}: {e.read().decode()}", file=sys.stderr)
        raise
    except OSError as e:
        print(f"Request failed: {e}", file=sys.stderr)
        raise


def _wait_for_health() -> None:
    """Call GET /api/health; retry up to HEALTH_RETRIES times with HEALTH_DELAY_SEC between."""
    path = "/health"
    for attempt in range(1, HEALTH_RETRIES + 1):
        try:
            _request("GET", path)
            return
        except (urllib.error.HTTPError, OSError) as e:
            if attempt == HEALTH_RETRIES:
                print(
                    f"Backend not ready after {HEALTH_RETRIES} attempts: {e}",
                    file=sys.stderr,
                )
                print(
                    "Start backend with: uvicorn app.main:app --reload "
                    "--host 0.0.0.0 --port 8000",
                    file=sys.stderr,
                )
                sys.exit(1)
            time.sleep(HEALTH_DELAY_SEC)


def main() -> None:
    print(f"BASE_URL = {BASE_URL}")

    if not SAMPLE_LOGS_PATH.exists():
        print(f"Missing {SAMPLE_LOGS_PATH}", file=sys.stderr)
        sys.exit(1)

    print("0) Checking backend health...")
    _wait_for_health()
    print("   ok")

    print("1) Posting capture session...")
    with open(SAMPLE_LOGS_PATH, encoding="utf-8") as f:
        session_payload = json.load(f)
    _request("POST", "/capture/sessions", session_payload)
    session_id = session_payload["session_id"]
    print(f"   session_id: {session_id}")

    print("2) Inferring workflow...")
    _request("POST", f"/infer/{session_id}")
    print("   done")

    print("3) Approving workflow...")
    _request("POST", f"/workflows/{session_id}/approve")
    print("   done")

    print("4) Generating agent...")
    _request("POST", f"/agents/{session_id}/generate")
    print("   done")

    print("5) Running agent...")
    run_body = {
        "parameters": SAMPLE_PARAMETERS,
        "simulate_ui_change": False,
    }
    result = _request("POST", f"/agents/{session_id}/run", run_body)
    print("   done")

    confirmation_id = result.get("confirmation_id")
    run_id = result.get("run_id")
    print()
    print("--- Demo complete ---")
    print(f"  confirmation_id: {confirmation_id}")
    print(f"  run_id:          {run_id}")


if __name__ == "__main__":
    main()
