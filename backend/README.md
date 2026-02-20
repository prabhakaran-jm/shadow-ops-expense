# Shadow Ops – Backend

FastAPI backend for workflow inference (Nova 2 Lite) and agent execution (Nova Act).

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys (optional for placeholder mode)
```

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/docs  
- Health: http://localhost:8000/api/health  

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/workflow/infer` | Infer workflow from prompt/context (Nova 2 Lite) |
| POST | `/api/agent/execute` | Execute approved workflow (Nova Act) |
| GET | `/api/health` | Health check |

## Environment

See `.env.example`. Without API keys, the app runs in placeholder mode with mock responses.
