import type {
  AgentRunRequest,
  ExecuteRequest,
  ExecutionResult,
  HealthResponse,
  InferRequest,
  InferredWorkflow,
  ReceiptExtractionResult,
  WorkflowDetail,
  WorkflowListItem,
} from './types'

import { getApiBase } from './apiBase'

const API_BASE = getApiBase(import.meta.env.VITE_API_BASE)

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

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}

export async function uploadReceipt(file: File): Promise<ReceiptExtractionResult> {
  const url = `${API_BASE}/capture/receipt`
  if (import.meta.env.DEV) console.log('[uploadReceipt] POST', url)
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(url, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const text = await res.text()
    let message = text || `HTTP ${res.status}`
    try {
      const json = JSON.parse(text) as { detail?: string }
      if (typeof json.detail === 'string') message = json.detail
    } catch {
      /* use message as-is */
    }
    throw new Error(message)
  }
  return res.json() as Promise<ReceiptExtractionResult>
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
