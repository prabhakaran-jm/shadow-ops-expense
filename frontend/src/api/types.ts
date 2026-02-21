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

/** List item from GET /workflows */
export type WorkflowListItem = {
  session_id: string
  title: string
  risk_level: string
  time_saved_minutes: number
}

/** Workflow parameter (backend model) */
export type WorkflowParameter = {
  name: string
  type: string
  required: boolean
  example?: string | null
}

/** Step in workflow detail (backend model) */
export type WorkflowStepDetail = {
  order: number
  intent: string
  instruction: string
  selector_hint?: string | null
  uses_parameters: string[]
}

/** Full workflow from GET /workflows/{id} */
export type WorkflowDetail = {
  session_id: string
  title: string
  description: string
  parameters: WorkflowParameter[]
  steps: WorkflowStepDetail[]
  risk_level: string
  time_saved_minutes: number
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

/** Request body for POST /agents/{id}/run */
export type AgentRunRequest = {
  parameters: Record<string, unknown>
  simulate_ui_change: boolean
}

/** Response from POST /agents/{id}/run */
export type ExecutionResult = {
  status: string
  confirmation_id: string | null
  run_id: string
  run_log: string[]
}
