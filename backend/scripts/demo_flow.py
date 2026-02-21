#!/usr/bin/env python3
"""
Run the full demo flow against a local backend (mock mode).

Requires: backend running at BASE_URL (default http://localhost:8000).
Usage: from repo root: python backend/scripts/demo_flow.py
       from backend/:  python scripts/demo_flow.py
       Optional: set DEMO_BASE_URL to override (e.g. http://localhost:8000).
"""

import json
import os
import sys
from pathlib import Path

import urllib.error
import urllib.request

# Resolve paths: script may be run as backend/scripts/demo_flow.py or scripts/demo_flow.py
_SCRIPT_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _SCRIPT_DIR.parent
_PROJECT_ROOT = _BACKEND_DIR.parent
SAMPLE_LOGS_PATH = _PROJECT_ROOT / "demo" / "sample_logs.json"

BASE_URL = os.environ.get("DEMO_BASE_URL", "http://localhost:8000")
API = f"{BASE_URL.rstrip('/')}/api"

SAMPLE_PARAMETERS = {
    "amount": "125.50",
    "date": "2025-02-20",
    "category": "Travel",
    "description": "Client meeting",
    "receipt_file": "receipt.pdf",
}


def _request(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{API}{path}"
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


def main() -> None:
    if not SAMPLE_LOGS_PATH.exists():
        print(f"Missing {SAMPLE_LOGS_PATH}", file=sys.stderr)
        sys.exit(1)

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
