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

**Windows (Git Bash):**
```bash
source .venv/Scripts/activate
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
| `AWS_REGION` | AWS region for Bedrock (real mode) | `us-east-1` |
| `NOVA_MODEL_ID_LITE` | Bedrock inference profile ID for Nova 2 Lite (optional) | `us.amazon.nova-2-lite-v1:0` |
| `NOVA_2_LITE_API_KEY` | Nova 2 Lite API key (real mode) | — |
| `NOVA_2_LITE_REGION` | Nova 2 Lite region | `us-east-1` |
| `NOVA_2_LITE_ENDPOINT` | Nova 2 Lite endpoint override | — |
| `NOVA_ACT_API_KEY` | Nova Act API key (real mode) | — |
| `NOVA_ACT_REGION` | Nova Act region | `us-east-1` |
| `NOVA_ACT_ENDPOINT` | Nova Act endpoint override | — |
| `LOG_LEVEL` | Log level | `INFO` |
| `CORS_ALLOW_ORIGINS` | Comma-separated origins for CORS (e.g. CloudFront URL). If unset, localhost + dev origins only. | — |

For **real** inference (`NOVA_MODE=real`), the backend uses **Amazon Bedrock** (Nova 2 Lite). Configure AWS credentials (e.g. `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, or an IAM role); no separate API key is required for Bedrock.

| `VITE_API_BASE` (frontend) | Origin when not using proxy (e.g. `http://localhost:8000`). Leave **unset** for local dev so app uses `/api` and Vite proxy. | — |
| `DEMO_BASE_URL` (demo script) | API base including `/api` for `demo_flow.py` (e.g. `http://localhost:8000/api`). | `http://localhost:8000/api` |

## Run (quickstart)

All backend routes are under **`/api`** (including health). Start backend then frontend; no env vars required for local dev.

**Terminal 1 – Backend:**
```bash
cd backend
.venv\Scripts\activate   # Windows PowerShell
# source .venv/bin/activate   # macOS / Linux
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 – Frontend:**
```bash
cd frontend
npm run dev
```

**Exact URLs:**

| What | URL |
|------|-----|
| Dashboard (app) | http://localhost:5173 |
| API docs (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/api/health |

**Frontend API:** Leave `VITE_API_BASE` unset; the app uses `/api` and Vite proxies it to `http://localhost:8000`. No manual config needed for local demo.

**Verify:** `curl http://localhost:8000/api/health` → `{"status":"ok","service":"shadow-ops-expense"}`

## Quick Demo (Mock Mode)

With the backend running, from the **project root**:

```bash
python backend/scripts/demo_flow.py
```

The script:

0. Calls **GET /api/health** (retries 3× with 1s delay if backend not ready)
1. Posts `demo/sample_logs.json` to **POST /api/capture/sessions**
2. Calls **POST /api/infer/{session_id}**
3. Calls **POST /api/workflows/{session_id}/approve**
4. Calls **POST /api/agents/{session_id}/generate**
5. Calls **POST /api/agents/{session_id}/run** with sample parameters
6. Prints **confirmation_id** and **run_id**

**Env (optional):** `DEMO_BASE_URL` – API base including `/api` (default `http://localhost:8000/api`). Example: `DEMO_BASE_URL=http://localhost:8000/api python backend/scripts/demo_flow.py`

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

## Deploy on AWS (App Runner + S3/CloudFront)

For a **Terraform-defined** stack (ECR, App Runner, S3, CloudFront), see **[infra/README.md](infra/README.md)** for:

- `terraform init` / `plan` / `apply`
- Docker build, ECR login, tag, and push for the backend
- Frontend build with `VITE_API_BASE` set to the App Runner URL (frontend appends `/api` if needed)
- S3 upload of `frontend/dist` and CloudFront invalidation

**Acceptance:** Backend container runs locally with Docker and `/api/health` works; frontend build with `VITE_API_BASE` works against the deployed backend.

## Documentation

- [Architecture](docs/architecture.md) – mermaid diagrams, components, and configuration.
- [Demo script (3 min)](docs/demo-script.md) – narration for judges.
- [Judges notes](docs/judges-notes.md) – Nova services, mocked vs real, how to run demo.
- [Backend README](backend/README.md) – backend-specific setup and endpoints.

## License

See [LICENSE](LICENSE).
