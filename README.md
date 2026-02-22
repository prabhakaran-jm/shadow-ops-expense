# Shadow Ops – Expense Report Shadow

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Node 18+](https://img.shields.io/badge/Node-18+-339933?logo=node.js&logoColor=white)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![AWS Nova](https://img.shields.io/badge/AWS-Nova%202%20Lite%20%2B%20Act-FF9900?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)

AI-powered expense automation that combines **Amazon Nova 2 Lite** (multimodal receipt OCR + workflow inference via Bedrock) with **Amazon Nova Act** (cloud browser automation) to turn a receipt photo into a fully automated expense submission.

## Features by category

| Category | Features |
|----------|----------|
| **Agentic AI** | Workflow inference from receipt images; human-in-the-loop approval gate; agent generation from approved workflow; parameterized execution with run log and confirmation ID; self-healing UI-change adaptation (failure → detection → retry). |
| **UI Automation** | Nova Act cloud browser fills real expense forms: types amounts, sets dates, selects categories, clicks Submit, clicks Confirm. Instruction enhancement adapts generic inferred steps to specific page layout. Async execution with live polling. |
| **Multimodal** | Nova 2 Lite multimodal extracts amount, merchant, date, category, currency from receipt photos. Same model infers structured workflows from extracted data. |

## Screenshots

| # | Description | Filename |
|---|-------------|----------|
| 1 | Dashboard – workflow list and selection | `docs/screenshots/01-dashboard-workflow-list.png` |
| 2 | Workflow detail – parameters and steps | `docs/screenshots/02-workflow-detail.png` |
| 3 | Run Agent modal – parameter form | `docs/screenshots/03-run-agent-modal.png` |
| 4 | Run result – confirmation and run log | `docs/screenshots/04-run-result.png` |

## Project structure

```
shadow-ops-expense/
├── backend/       # FastAPI – workflow inference & agent execution APIs
│   └── prompts/   # AI prompt templates (inference, receipt extraction)
├── frontend/      # React (Vite) – dashboard, approval, execution trigger
├── demo/          # Demo assets and sample payloads
├── docs/          # Architecture and documentation
└── README.md      # This file
```

## Prerequisites

- **Python 3.12+** (backend)
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
| `NOVA_MODE` | Inference mode: `mock` or `real` (Nova 2 Lite via Bedrock) | `mock` |
| `AWS_REGION` | AWS region for Bedrock and Nova Act | `us-east-1` |
| `NOVA_MODEL_ID_LITE` | Bedrock model ID for Nova 2 Lite | `us.amazon.nova-2-lite-v1:0` |
| `NOVA_ACT_MODE` | Agent mode: `mock` or `real` (Nova Act SDK) | `mock` |
| `NOVA_ACT_STARTING_PAGE` | URL Nova Act opens in cloud browser | — |
| `NOVA_ACT_HEADLESS` | Run cloud browser headless | `true` |
| `LOG_LEVEL` | Log level | `INFO` |
| `API_KEY` | Optional. When set, all `/api/*` requests require `X-API-Key` header; 401 if missing or wrong. Unset = no check. | — |
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
| GET    | `/api/health` | Health check |
| POST   | `/api/capture/sessions` | Store capture session (input for inference) |
| POST   | `/api/capture/receipt` | Upload receipt image; extract fields, create session, infer workflow (Nova 2 Lite multimodal or mock) |
| POST   | `/api/infer/{session_id}` | Infer workflow from session (Nova 2 Lite when NOVA_MODE=real) |
| GET    | `/api/workflows` | List workflows |
| GET    | `/api/workflows/{session_id}` | Get workflow detail |
| POST   | `/api/workflows/{session_id}/approve` | Approve workflow |
| POST   | `/api/agents/{session_id}/generate` | Generate agent from workflow |
| POST   | `/api/agents/{session_id}/run` | Run agent with parameters (mock or real Nova Act cloud browser) |
| GET    | `/api/agents/{session_id}/run/{run_id}` | Poll async agent run status (real Nova Act mode) |

## Deploy on AWS (App Runner + S3/CloudFront)

For a **Terraform-defined** stack (ECR, App Runner, S3, CloudFront), see **[infra/README.md](infra/README.md)** for:

- `terraform init` / `plan` / `apply`
- Docker build, ECR login, tag, and push for the backend
- Frontend build with `VITE_API_BASE` set to the App Runner URL (frontend appends `/api` if needed)
- S3 upload of `frontend/dist` and CloudFront invalidation

**Acceptance:** Backend container runs locally with Docker and `/api/health` works; frontend build with `VITE_API_BASE` works against the deployed backend.

## Blog post

- **Blog:** [AWS Builder Experience](https://builder.aws.com/content/3A2YmIl1jbE97deeHGDSWYxdHEX/building-shadow-ops-automating-expense-reports-with-amazon-nova-2-lite-and-nova-act)

## Documentation

- [Architecture](docs/architecture.md) – mermaid diagrams, components, and configuration.
- [Judges notes](docs/judges-notes.md) – Nova services, mocked vs real, how to run demo.
- [Screenshots guide](docs/screenshots/README.md) – which screenshots to capture for submission.
- [Backend README](backend/README.md) – backend-specific setup and endpoints.

## License

See [LICENSE](LICENSE).
