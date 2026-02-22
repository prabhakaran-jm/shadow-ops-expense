# Judges notes – Shadow Ops – Expense Report Shadow

## Amazon Nova services used

| Service | Role | Integration status |
|--------|------|-------------------|
| **Amazon Nova 2 Lite** (Bedrock) | 1. **Receipt OCR**: Multimodal image+text call extracts amount, merchant, date, category, currency from receipt photos. 2. **Workflow inference**: Text call turns a capture session into a structured workflow (title, parameters, steps, risk, time saved). | **Fully implemented and deployed.** `backend/app/services/nova_client.py` calls Bedrock (`bedrock-runtime`) with model `amazon.nova-2-lite-v1:0`. Works in both text and multimodal modes. Prompts in `backend/prompts/`. |
| **Amazon Nova Act** | Cloud browser automation: opens a headless Chromium session on the target expense form, fills fields, selects dropdowns, clicks Submit, clicks Confirm, and extracts the confirmation ID from the success banner. | **Fully implemented and deployed.** `backend/app/services/act_client.py` uses the `nova-act` SDK with `Workflow` context manager (IAM auth, no API key). Cloud browser runs in App Runner. Step skipping, instruction enhancement, and `act_get()` for result extraction. |

---

## What is real vs mocked

The system supports two modes controlled by environment variables. **Both modes are fully implemented and working.**

### Real mode (`NOVA_MODE=real`, `NOVA_ACT_MODE=real`) — Deployed on AWS

| Feature | Implementation |
|---------|---------------|
| Receipt extraction | Nova 2 Lite multimodal via Bedrock. Extracts amount, merchant, date, category, currency, confidence. |
| Workflow inference | Nova 2 Lite text via Bedrock. Infers title, description, parameters, steps, risk_level, time_saved_minutes from capture session. |
| Workflow approval | Human-in-the-loop approval gate (stored to disk). |
| Agent generation | Builds `ActAgentSpec` from approved workflow (parameter schema + steps). |
| Agent execution | Nova Act SDK with Workflow/IAM auth. Cloud browser navigates to expense form, fills fields, submits, confirms. Background thread + polling (avoids App Runner 120s timeout). |
| Confirmation extraction | `act_get()` reads confirmation ID from the page's success banner. |

### Mock mode (`NOVA_MODE=mock`, `NOVA_ACT_MODE=mock`) — Local development

- Deterministic responses for all services (no AWS calls needed).
- Mock receipt extraction returns fixed fields.
- Mock inference returns a fixed 6-step workflow.
- Mock agent execution returns a step-by-step run log with confirmation ID.
- Optional `simulate_ui_change` flag demonstrates self-healing: step fails at Submit, detects UI changed (Submit renamed to Confirm), retries with adapted instruction.

---

## Deployment architecture

| Component | AWS Service | Details |
|-----------|------------|---------|
| Backend API | **App Runner** | FastAPI container from ECR. 4096 MB memory. Env vars for real Nova mode. |
| Frontend | **S3 + CloudFront** | React SPA with OAC (private bucket). SPA routing via custom error responses. |
| Container registry | **ECR** | Backend Docker image (Python 3.12-slim). |
| Infrastructure | **Terraform** | All resources defined in `infra/`. Two-phase apply (ECR first, then App Runner). |
| IAM | **IAM roles** | App Runner instance role with `bedrock:InvokeModel` + `nova-act:*` permissions. |

---

## How to run the demo

### Option A – Deployed (Real Nova Mode)

The app is deployed and live:
- **Frontend**: S3 + CloudFront
- **Backend**: App Runner (auto-scales, accessed via CloudFront or direct)

Steps:
1. Open the frontend URL.
2. Upload a receipt image (any expense receipt photo).
3. Nova 2 Lite extracts fields and infers a workflow (~8 seconds total).
4. Click **Approve** to approve the workflow.
5. Click **Generate Agent** to create the agent spec.
6. Click **Run Agent**, fill in the parameters, click **Run**.
7. Nova Act opens a cloud browser, fills the expense form, submits it, and returns a confirmation ID (~2-4 minutes).
8. The run log shows each step with timing and sub-step counts.

### Option B – Local (Mock Mode)

1. **Start backend**: `cd backend && .venv\Scripts\activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. **Start frontend**: `cd frontend && npm run dev`
3. **Seed data**: `python backend/scripts/demo_flow.py`
4. Open http://localhost:5173 and follow the same flow as above (instant mock responses).

### Option C – CLI demo

```bash
python backend/scripts/demo_flow.py
```

---

## Key technical highlights for judges

1. **Dual Nova integration**: Uses BOTH Nova 2 Lite (multimodal OCR + workflow inference) AND Nova Act (cloud browser automation) — the full Nova ecosystem.

2. **Receipt-to-automation pipeline**: Upload a receipt photo → AI extracts fields → AI infers a workflow → human approves → AI agent fills the actual form in a real browser → confirmation ID extracted. End-to-end automation from a single image.

3. **Self-healing agent**: When a UI element changes (e.g. "Submit" renamed to "Confirm"), the agent detects the failure, adapts its instruction, and retries. Demonstrated in both mock (simulate_ui_change) and real (retry logic in ActClientReal) modes.

4. **Instruction enhancement**: Generic inferred workflow steps are automatically enhanced with page-specific context before execution (e.g. "Fill amount" becomes `Set the "Amount ($)" number input to "125.50"`).

5. **Async execution pattern**: Real Nova Act takes 2-4 minutes. Backend returns immediately with a run_id, frontend polls every 3 seconds with a live timer. Works within App Runner's 120-second request timeout.

6. **Production-grade**: Pydantic v2 models, structlog JSON logging, Terraform IaC, Docker, CORS, API key middleware, health checks, retry logic, graceful fallbacks.

### Suggested talking points

- **Agentic AI**: Human-in-the-loop approval then fully automated agent execution with parameters.
- **UI Automation**: Nova Act fills real forms in a cloud browser — not just mock outputs.
- **Multimodal**: Receipt photo → structured data via Nova 2 Lite multimodal.
- **Self-healing**: Agent adapts when UI elements change (failure → detection → retry).
- **Enterprise impact**: Expense reporting is a universal enterprise pain point; this automates it end-to-end.
