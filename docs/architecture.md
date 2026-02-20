# Shadow Ops – Architecture

## Overview

**Shadow Ops – Expense Report Shadow** is an AI-powered web application that infers expense submission workflows from user behavior (or prompts) and runs them via agent execution using Amazon Nova 2 Lite and Nova Act.

## Components

| Layer    | Tech           | Role |
|----------|----------------|------|
| Frontend | React (Vite)   | Dashboard: review inferred workflows, approve, trigger execution |
| Backend  | FastAPI        | REST API: workflow inference, agent execution, health |
| Inference| Nova 2 Lite    | Lightweight model to infer workflow steps from prompt/context |
| Execution| Nova Act       | Agent runtime to execute approved workflows |

## Flow

1. **Infer** – User (or system) sends a prompt/context to `POST /api/workflow/infer`. Backend calls Nova 2 Lite (placeholder or real) and returns a structured workflow.
2. **Review** – Dashboard lists inferred workflows; user reviews steps.
3. **Approve** – User clicks **Approve** to mark a workflow ready for execution.
4. **Execute** – User clicks **Execute**; frontend calls `POST /api/agent/execute`. Backend invokes Nova Act (placeholder or real) and returns run status.

## Configuration

- Backend: `.env` in `backend/` (see `backend/.env.example`). Without Nova API keys, the app runs in placeholder mode with mock responses.
- Frontend: dev server proxies `/api` to `http://localhost:8000` (see `frontend/vite.config.ts`).

## Project layout

```
shadow-ops-expense/
├── backend/          # FastAPI app, config, logging, Nova placeholders
├── frontend/         # React app, dashboard, API client
├── prompts/          # Prompt templates for inference/agents
├── demo/             # Demo assets and sample payloads
├── docs/             # Architecture and runbooks
└── README.md         # Setup and run instructions
```
