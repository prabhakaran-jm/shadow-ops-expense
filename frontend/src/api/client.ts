import type { InferRequest, ExecuteRequest, InferredWorkflow } from './types'

const API_BASE = '/api'

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
