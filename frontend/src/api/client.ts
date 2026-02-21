import type {
  AgentRunRequest,
  ExecuteRequest,
  ExecutionResult,
  InferRequest,
  InferredWorkflow,
  WorkflowDetail,
  WorkflowListItem,
} from './types'

const base = typeof import.meta.env.VITE_API_BASE === 'string' ? import.meta.env.VITE_API_BASE : ''
const API_BASE = base ? `${base.replace(/\/$/, '')}/api` : '/api'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export async function inferWorkflow(body: InferRequest): Promise<InferredWorkflow> {
  return request<InferredWorkflow>('/workflow/infer', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function executeAgent(body: ExecuteRequest): Promise<{ run_id: string; status: string }> {
  return request('/agent/execute', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function getWorkflows(): Promise<WorkflowListItem[]> {
  return request<WorkflowListItem[]>('/workflows')
}

export async function getWorkflow(sessionId: string): Promise<WorkflowDetail> {
  return request<WorkflowDetail>(`/workflows/${sessionId}`)
}

export async function approveWorkflow(sessionId: string): Promise<{ approved: boolean }> {
  return request<{ approved: boolean }>(`/workflows/${sessionId}/approve`, {
    method: 'POST',
  })
}

export async function generateAgent(sessionId: string): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>(`/agents/${sessionId}/generate`, {
    method: 'POST',
  })
}

export async function runAgent(
  sessionId: string,
  body: AgentRunRequest
): Promise<ExecutionResult> {
  return request<ExecutionResult>(`/agents/${sessionId}/run`, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}
