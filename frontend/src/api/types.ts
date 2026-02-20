export type WorkflowStep = {
  id: string
  action: string
  parameters?: Record<string, unknown>
}

export type InferredWorkflow = {
  workflow_id: string
  status: string
  label: string
  steps: WorkflowStep[]
  source?: string
  metadata?: Record<string, unknown>
  approved?: boolean
  executed?: boolean
}

export type InferRequest = {
  prompt?: string
  context?: Record<string, unknown>
  user_actions_snapshot?: Record<string, unknown>[]
}

export type ExecuteRequest = {
  workflow_id: string
  workflow: Record<string, unknown>
  options?: Record<string, unknown>
}
