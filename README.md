# Shadow Ops – Expense Report Shadow

AI-powered web application that infers expense submission workflows from user behavior (or prompts) and runs them via **Amazon Nova 2 Lite** (inference) and **Nova Act** (agent execution).

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

- Backend: copy `backend/.env.example` to `backend/.env`. Set `NOVA_2_LITE_*` and `NOVA_ACT_*` when integrating real APIs; otherwise the app runs in placeholder mode.

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

- [Architecture](docs/architecture.md) – components, flow, and configuration.
- [Backend README](backend/README.md) – backend-specific setup and endpoints.

## License

See [LICENSE](LICENSE).
