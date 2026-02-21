# Judges notes – Shadow Ops – Expense Report Shadow

## Amazon Nova services used

| Service | Intended role | Current integration |
|--------|----------------|----------------------|
| **Amazon Nova 2 Lite** | Workflow inference: turn a capture session (or prompt) into a structured workflow (title, description, parameters, steps, risk, time saved). | **Stub only.** Extension point in `backend/app/services/inference.py`: `NOVA_MODE=real` raises `NotImplementedError` with a clear message. No API calls. |
| **Amazon Nova Act** | Agent execution: create an agent from an approved workflow and run it with parameters. | **Stub only.** Mock in `backend/app/services/act_client.py`: `ActClientMock` creates agent specs and runs with deterministic run_log and confirmation_id. No Nova Act API calls. |

Both services are **designed in** (config, env vars, docstrings) and **called via** clear extension points; the app is fully runnable in mock mode for judging.

---

## What is mocked vs real

- **Real (implemented and working):**
  - Capture session storage (POST/GET, disk under `demo/sessions/`).
  - Workflow inference **mock**: deterministic workflow from session (fixed parameters and steps).
  - Workflow review APIs (list, get, approve) and persistence (`demo/workflows/`, `demo/approvals/`).
  - Agent generation **mock**: agent spec built from workflow, stored under `demo/agents/`.
  - Agent execution **mock**: run_log and confirmation_id (e.g. EXP-2026-000123); optional UI-change simulation (failure at Submit → “UI changed: Submit renamed to Confirm” → retry).
  - Full React dashboard: workflow list, detail, Approve, Generate Agent, Run Agent (form + results with highlighted adaptation).
  - Demo script: end-to-end flow from CLI.

- **Mocked (no Nova API calls):**
  - Nova 2 Lite inference: `NOVA_MODE=mock` (default) returns a fixed InferredWorkflow; `NOVA_MODE=real` raises `NotImplementedError`.
  - Nova Act: `ActClientMock` only; no real agent runtime.

---

## How to run the demo

### Prerequisites

- Python 3.11+ (backend), Node.js 18+ (frontend).
- Backend: `cd backend && pip install -r requirements.txt && cp .env.example .env` (optional: set `NOVA_MODE=mock` explicitly).
- Frontend: `cd frontend && npm install`.

### Option A – UI demo

1. **Start backend** (Terminal 1):
   ```bash
   cd backend
   .venv\Scripts\activate   # or source .venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start frontend** (Terminal 2):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Seed data (one-time):** From project root:
   ```bash
   python backend/scripts/demo_flow.py
   ```
   This creates a session, infers a workflow, approves it, generates an agent, and runs it once. Output includes `confirmation_id` and `run_id`.

4. **Open dashboard:** http://localhost:5173  
   - Select the workflow “Submit expense (inferred)” (or the only one in the list).  
   - Show detail, Approve (if not already), Generate Agent, then Run Agent.  
   - Run once without “Simulate UI change,” then once with it and point out the highlighted adaptation lines in the run log.

### Option B – CLI-only quick demo

1. Start the backend only (as above).
2. From project root:
   ```bash
   python backend/scripts/demo_flow.py
   ```
3. Confirm output shows `confirmation_id` and `run_id`.

To use another host/port: `DEMO_BASE_URL=http://localhost:8000/api python backend/scripts/demo_flow.py`.

### API docs

- Swagger UI: http://localhost:8000/docs  
- Health: http://localhost:8000/api/health  

### Suggested talking points

- **Agentic AI:** Human-in-the-loop (approve workflow) then automated agent (generate + run with parameters).
- **UI Automation:** Inferred steps (navigate, fill, submit, etc.); run_log reflects automation; UI-change simulation shows adaptation when “Submit” becomes “Confirm.”
- **Multimodal:** Capture session supports `screenshot_path` and field labels; inference prompt and schema support future use of screenshots/vision (Nova 2 Lite extension).
