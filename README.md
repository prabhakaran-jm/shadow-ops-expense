# Shadow Ops – Expense Report Shadow

AI-powered web application that infers expense submission workflows from user behavior (or prompts) and runs them via **Amazon Nova 2 Lite** (inference) and **Nova Act** (agent execution).

## Features by category

| Category | Features |
|----------|----------|
| **Agentic AI** | Workflow inference from capture sessions; human approval gate; agent generation from approved workflow; parameterized execution with run log and confirmation ID; UI-change adaptation simulation (failure → recovery → retry). |
| **UI Automation** | Inferred steps (navigate, open form, upload receipt, fill fields, submit, confirmation); execution run log; mock agent that simulates step-by-step automation and adapts when UI text changes (e.g. Submit → Confirm). |
| **Multimodal** | Capture session model supports `screenshot_path` and field labels per step; schema and prompts ready for vision/screenshot input in Nova 2 Lite inference (extension point). |

## Screenshots

*(Add 3–5 screenshots for submission; place files in `docs/screenshots/` or link here.)*

| # | Description | Filename |
|---|-------------|----------|
| 1 | Dashboard – workflow list and selection | `docs/screenshots/01-dashboard-workflow-list.png` |
| 2 | Workflow detail – parameters and steps | `docs/screenshots/02-workflow-detail.png` |
| 3 | Run Agent modal – parameter form | `docs/screenshots/03-run-agent-modal.png` |
| 4 | Run result – confirmation and run log | `docs/screenshots/04-run-result.png` |
| 5 | Run log with UI-change adaptation highlighted | `docs/screenshots/05-run-log-adaptation.png` |

## Project structure

```
shadow-ops-expense/
├── backend/       # FastAPI – workflow inference & agent execution APIs
├── frontend/      # React (Vite) – dashboard, approval, execution trigger
├── prompts/       # AI prompt templates
├── demo/          # Demo assets and sample payloads
├── docs/          # Architecture and documentation
└── README.md      # This file
```

## Prerequisites

- **Python 3.11+** (backend)
- **Node.js 18+** (frontend)

## Setup

### 1. Backend

```bash
cd backend
python -m venv .venv
```

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
cp .env.example .env
# Optional: edit .env and set Nova API keys. Without them, mock responses are used.
```

### 2. Frontend

```bash
cd frontend
npm install
```

### 3. Environment

Copy `backend/.env.example` to `backend/.env`. Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Server bind host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `DEBUG` | Debug mode | `false` |
| `NOVA_MODE` | Inference mode: `mock` or `real` | `mock` |
| `NOVA_2_LITE_API_KEY` | Nova 2 Lite API key (real mode) | — |
| `NOVA_2_LITE_REGION` | Nova 2 Lite region | `us-east-1` |
| `NOVA_2_LITE_ENDPOINT` | Nova 2 Lite endpoint override | — |
| `NOVA_ACT_API_KEY` | Nova Act API key (real mode) | — |
| `NOVA_ACT_REGION` | Nova Act region | `us-east-1` |
| `NOVA_ACT_ENDPOINT` | Nova Act endpoint override | — |
| `LOG_LEVEL` | Log level | `INFO` |

Frontend (optional): `VITE_API_BASE` – API base URL (leave unset in dev to use proxy).

## Run

**Terminal 1 – Backend:**
```bash
cd backend
.venv\Scripts\activate   # or source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 – Frontend:**
```bash
cd frontend
npm run dev
```

- **App:** http://localhost:5173  
- **API docs:** http://localhost:8000/docs  
- **Health:** http://localhost:8000/api/health  

The frontend proxies `/api` to the backend, so the dashboard can infer workflows and trigger execution without CORS setup.

## Quick Demo (Mock Mode)

With the backend running (and `NOVA_MODE=mock` in `backend/.env`, or unset), run the full flow from the project root:

```bash
python backend/scripts/demo_flow.py
```

The script will:

1. Post `demo/sample_logs.json` to **POST /api/capture/sessions**
2. Call **POST /api/infer/{session_id}** to infer a workflow
3. Call **POST /api/workflows/{session_id}/approve**
4. Call **POST /api/agents/{session_id}/generate**
5. Call **POST /api/agents/{session_id}/run** with sample parameters
6. Print **confirmation_id** and **run_id**

Ensure the backend is up (`uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` from `backend/`). To point at another host/port, set `DEMO_BASE_URL` (e.g. `DEMO_BASE_URL=http://localhost:8000 python backend/scripts/demo_flow.py`).

## Usage

1. Open the **Dashboard** at http://localhost:5173.
2. Enter a prompt (e.g. *Submit travel expense with receipts*) and click **Infer**.
3. Review the inferred workflow steps.
4. Click **Approve** to mark it ready for execution.
5. Click **Execute** to run the workflow via the agent (Nova Act placeholder or live).

## API summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/api/workflow/infer` | Infer workflow from prompt/context (Nova 2 Lite) |
| POST   | `/api/agent/execute`  | Execute approved workflow (Nova Act) |
| GET    | `/api/health`         | Health check |

## Documentation

- [Architecture](docs/architecture.md) – mermaid diagrams, components, and configuration.
- [Demo script (3 min)](docs/demo-script.md) – narration for judges.
- [Judges notes](docs/judges-notes.md) – Nova services, mocked vs real, how to run demo.
- [Backend README](backend/README.md) – backend-specific setup and endpoints.

## License

See [LICENSE](LICENSE).
