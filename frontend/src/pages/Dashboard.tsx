import { useState, useCallback } from 'react'
import type { InferredWorkflow } from '../api/types'
import { inferWorkflow, executeAgent } from '../api/client'
import WorkflowCard from '../components/WorkflowCard'
import styles from './Dashboard.module.css'

export default function Dashboard() {
  const [workflows, setWorkflows] = useState<InferredWorkflow[]>([])
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [executingId, setExecutingId] = useState<string | null>(null)

  const handleInfer = useCallback(async () => {
    setError(null)
    setLoading(true)
    try {
      const result = await inferWorkflow({ prompt: prompt || undefined, context: {} })
      setWorkflows((prev) => [
        ...prev,
        {
          ...result,
          approved: false,
        },
      ])
      setPrompt('')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Inference failed')
    } finally {
      setLoading(false)
    }
  }, [prompt])

  const handleApprove = useCallback((workflowId: string) => {
    setWorkflows((prev) =>
      prev.map((w) => (w.workflow_id === workflowId ? { ...w, approved: true } : w))
    )
  }, [])

  const handleExecute = useCallback(async (workflow: InferredWorkflow) => {
    if (!workflow.approved) return
    setExecutingId(workflow.workflow_id)
    setError(null)
    try {
      await executeAgent({
        workflow_id: workflow.workflow_id,
        workflow: {
          workflow_id: workflow.workflow_id,
          status: workflow.status,
          label: workflow.label,
          steps: workflow.steps,
          source: workflow.source,
          metadata: workflow.metadata,
        },
        options: {},
      })
      setWorkflows((prev) =>
        prev.map((w) =>
          w.workflow_id === workflow.workflow_id ? { ...w, executed: true } : w
        )
      )
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Execution failed')
    } finally {
      setExecutingId(null)
    }
  }, [])

  return (
    <div className={styles.dashboard}>
      <header className={styles.header}>
        <h1 className={styles.title}>Inferred Workflows</h1>
        <p className={styles.subtitle}>Review and approve expense workflows, then trigger execution.</p>
      </header>

      <section className={styles.inferSection}>
        <div className={styles.inferCard}>
          <label className={styles.label} htmlFor="prompt">Infer new workflow</label>
          <div className={styles.inferRow}>
            <input
              id="prompt"
              type="text"
              className={styles.input}
              placeholder="e.g. Submit travel expense with receipts"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleInfer()}
            />
            <button
              type="button"
              className={styles.buttonPrimary}
              onClick={handleInfer}
              disabled={loading}
            >
              {loading ? 'Inferring…' : 'Infer'}
            </button>
          </div>
        </div>
      </section>

      {error && (
        <div className={styles.errorBanner} role="alert">
          {error}
        </div>
      )}

      <section className={styles.workflows}>
        <h2 className={styles.sectionTitle}>Workflows</h2>
        {workflows.length === 0 ? (
          <div className={styles.empty}>
            <p>No workflows yet. Use the field above to infer one from a prompt.</p>
          </div>
        ) : (
          <ul className={styles.list}>
            {workflows.map((w) => (
              <li key={w.workflow_id}>
                <WorkflowCard
                  workflow={w}
                  onApprove={() => handleApprove(w.workflow_id)}
                  onExecute={() => handleExecute(w)}
                  isExecuting={executingId === w.workflow_id}
                />
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
