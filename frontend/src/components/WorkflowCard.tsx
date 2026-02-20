import type { InferredWorkflow } from '../api/types'
import styles from './WorkflowCard.module.css'

type Props = {
  workflow: InferredWorkflow
  onApprove: () => void
  onExecute: () => void
  isExecuting: boolean
}

export default function WorkflowCard({ workflow, onApprove, onExecute, isExecuting }: Props) {
  const canExecute = workflow.approved && !workflow.executed

  return (
    <article className={styles.card}>
      <div className={styles.header}>
        <span className={styles.label}>{workflow.label}</span>
        <span className={styles.id}>{workflow.workflow_id}</span>
        {workflow.approved && (
          <span className={styles.badgeApproved}>Approved</span>
        )}
        {workflow.executed && (
          <span className={styles.badgeExecuted}>Executed</span>
        )}
      </div>
      <ul className={styles.steps}>
        {workflow.steps?.map((step) => (
          <li key={step.id} className={styles.step}>
            <span className={styles.stepId}>{step.id}</span>
            <span className={styles.stepAction}>{step.action}</span>
            {step.parameters && Object.keys(step.parameters).length > 0 && (
              <code className={styles.stepParams}>
                {JSON.stringify(step.parameters)}
              </code>
            )}
          </li>
        ))}
      </ul>
      <div className={styles.actions}>
        {!workflow.approved && (
          <button
            type="button"
            className={styles.buttonApprove}
            onClick={onApprove}
          >
            Approve
          </button>
        )}
        <button
          type="button"
          className={styles.buttonExecute}
          onClick={onExecute}
          disabled={!canExecute || isExecuting}
        >
          {isExecuting ? 'Executing…' : 'Execute'}
        </button>
      </div>
    </article>
  )
}
