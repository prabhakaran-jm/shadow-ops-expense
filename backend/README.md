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
| GET | `/api/schemas` | Example JSON for CaptureSession and InferredWorkflow |
| POST | `/api/workflow/infer` | Infer workflow from prompt/context (Nova 2 Lite) |
| POST | `/api/agent/execute` | Execute approved workflow (Nova Act) |
| GET | `/api/health` | Health check |

## Example payloads (GET /api/schemas)

`GET /api/schemas` returns example JSON for the core data contracts. Below is the same structure for reference.

### CaptureSession

Input shape for workflow inference (recorded user session).

```json
{
  "CaptureSession": {
    "session_id": "cap_20250220_001",
    "steps": [
      {
        "step_index": 0,
        "url": "https://expense.example.com/new",
        "action": "click",
        "element_text": "New expense",
        "field_label": null,
        "value_redacted": null,
        "screenshot_path": "/captures/cap_001_step_0.png",
        "timestamp": "2025-02-20T10:00:00Z"
      },
      {
        "step_index": 1,
        "url": "https://expense.example.com/new",
        "action": "type",
        "element_text": "",
        "field_label": "Amount",
        "value_redacted": "***",
        "screenshot_path": "/captures/cap_001_step_1.png",
        "timestamp": "2025-02-20T10:00:15Z"
      },
      {
        "step_index": 2,
        "url": "https://expense.example.com/new",
        "action": "click",
        "element_text": "Submit",
        "field_label": null,
        "value_redacted": null,
        "screenshot_path": "/captures/cap_001_step_2.png",
        "timestamp": "2025-02-20T10:00:45Z"
      }
    ],
    "metadata": {
      "app_version": "2.1",
      "tenant_id": "acme"
    }
  }
}
```

### InferredWorkflow

Output shape from workflow inference (title, parameters, steps, risk, time saved).

```json
{
  "InferredWorkflow": {
    "session_id": "cap_20250220_001",
    "title": "Submit travel expense",
    "description": "Creates a new travel expense, fills amount and category, attaches receipt, and submits for approval.",
    "parameters": [
      {
        "name": "expense_amount",
        "type": "number",
        "required": true,
        "example": "125.50"
      },
      {
        "name": "category",
        "type": "string",
        "required": true,
        "example": "Travel"
      }
    ],
    "steps": [
      {
        "order": 1,
        "intent": "navigate",
        "instruction": "Open the new expense form",
        "selector_hint": "a[href='/new']",
        "uses_parameters": []
      },
      {
        "order": 2,
        "intent": "fill_field",
        "instruction": "Enter the expense amount in the Amount field",
        "selector_hint": "input[name='amount']",
        "uses_parameters": ["expense_amount"]
      },
      {
        "order": 3,
        "intent": "fill_field",
        "instruction": "Select the expense category",
        "selector_hint": "select[name='category']",
        "uses_parameters": ["category"]
      },
      {
        "order": 4,
        "intent": "submit_form",
        "instruction": "Click Submit to send the expense for approval",
        "selector_hint": "button[type='submit']",
        "uses_parameters": []
      }
    ],
    "risk_level": "low",
    "time_saved_minutes": 5
  }
}
```

## Environment

See `.env.example`. Without API keys, the app runs in placeholder mode with mock responses.
