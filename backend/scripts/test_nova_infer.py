#!/usr/bin/env python3
"""
Integration test for workflow inference (mock or real Nova 2 Lite).

Loads demo/sample_logs.json, POSTs to /api/capture/sessions, then POSTs to
/api/infer/{session_id}, and prints title, parameters count, and steps count.
Works with NOVA_MODE=mock or NOVA_MODE=real (requires AWS credentials for real).

Usage:
  From repo root:  python backend/scripts/test_nova_infer.py
  From backend/:   python scripts/test_nova_infer.py
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

BASE_URL = os.environ.get("DEMO_BASE_URL", "http://localhost:8000/api").rstrip("/")
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
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} {path}: {e.read().decode()}", file=sys.stderr)
        raise
    except OSError as e:
        print(f"Request failed: {e}", file=sys.stderr)
        raise


def _wait_for_health() -> None:
    for attempt in range(1, HEALTH_RETRIES + 1):
        try:
            out = _request("GET", "/health")
            mode = out.get("mode", "?")
            print(f"   health ok (mode={mode})")
            return
        except (urllib.error.HTTPError, OSError) as e:
            if attempt == HEALTH_RETRIES:
                print(f"Backend not ready after {HEALTH_RETRIES} attempts: {e}", file=sys.stderr)
                sys.exit(1)
            time.sleep(HEALTH_DELAY_SEC)


def main() -> None:
    print(f"BASE_URL = {BASE_URL}")

    if not SAMPLE_LOGS_PATH.exists():
        print(f"Missing {SAMPLE_LOGS_PATH}", file=sys.stderr)
        sys.exit(1)

    print("1) Checking backend health...")
    _wait_for_health()

    print("2) Posting capture session...")
    with open(SAMPLE_LOGS_PATH, encoding="utf-8") as f:
        session_payload = json.load(f)
    _request("POST", "/capture/sessions", session_payload)
    session_id = session_payload["session_id"]
    print(f"   session_id: {session_id}")

    print("3) Calling infer...")
    workflow = _request("POST", f"/infer/{session_id}")
    title = workflow.get("title", "?")
    parameters = workflow.get("parameters", [])
    steps = workflow.get("steps", [])
    print(f"   title: {title}")
    print(f"   parameters count: {len(parameters)}")
    print(f"   steps count: {len(steps)}")
    print("   done.")


if __name__ == "__main__":
    main()
