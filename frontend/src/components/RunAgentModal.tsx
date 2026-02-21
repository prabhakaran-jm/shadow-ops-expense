import { useState } from 'react'
import type { AgentRunRequest, ExecutionResult } from '../api/types'
import { runAgent } from '../api/client'
import styles from './RunAgentModal.module.css'

type Props = {
  sessionId: string
  onClose: () => void
  onSuccess: (result: ExecutionResult) => void
}

export default function RunAgentModal({ sessionId, onClose, onSuccess }: Props) {
  const [amount, setAmount] = useState('')
  const [date, setDate] = useState('')
  const [category, setCategory] = useState('')
  const [description, setDescription] = useState('')
  const [receiptFile, setReceiptFile] = useState('')
  const [simulateUiChange, setSimulateUiChange] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const body: AgentRunRequest = {
        parameters: {
          amount: amount || undefined,
          date: date || undefined,
          category: category || undefined,
          description: description || undefined,
          receipt_file: receiptFile || undefined,
        },
        simulate_ui_change: simulateUiChange,
      }
      const result = await runAgent(sessionId, body)
      onSuccess(result)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Run failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className={styles.overlay} role="dialog" aria-modal="true" aria-labelledby="run-agent-title">
      <div className={styles.backdrop} onClick={onClose} aria-hidden="true" />
      <div className={styles.modal}>
        <div className={styles.header}>
          <h2 id="run-agent-title" className={styles.title}>Run agent</h2>
          <button type="button" className={styles.closeBtn} onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        <form onSubmit={handleSubmit} className={styles.form}>
          {error && (
            <div className={styles.errorBanner} role="alert">
              {error}
            </div>
          )}
          <div className={styles.field}>
            <label htmlFor="run-amount">Amount</label>
            <input
              id="run-amount"
              type="text"
              placeholder="e.g. 125.50"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className={styles.input}
            />
          </div>
          <div className={styles.field}>
            <label htmlFor="run-date">Date</label>
            <input
              id="run-date"
              type="text"
              placeholder="e.g. 2025-02-20"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className={styles.input}
            />
          </div>
          <div className={styles.field}>
            <label htmlFor="run-category">Category</label>
            <input
              id="run-category"
              type="text"
              placeholder="e.g. Travel"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className={styles.input}
            />
          </div>
          <div className={styles.field}>
            <label htmlFor="run-description">Description</label>
            <input
              id="run-description"
              type="text"
              placeholder="Optional"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className={styles.input}
            />
          </div>
          <div className={styles.field}>
            <label htmlFor="run-receipt">Receipt file</label>
            <input
              id="run-receipt"
              type="text"
              placeholder="e.g. receipt.pdf"
              value={receiptFile}
              onChange={(e) => setReceiptFile(e.target.value)}
              className={styles.input}
            />
          </div>
          <div className={styles.checkboxRow}>
            <input
              id="run-simulate"
              type="checkbox"
              checked={simulateUiChange}
              onChange={(e) => setSimulateUiChange(e.target.checked)}
              className={styles.checkbox}
            />
            <label htmlFor="run-simulate">Simulate UI change (no real actions)</label>
          </div>
          <div className={styles.actions}>
            <button type="button" className={styles.buttonSecondary} onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className={styles.buttonPrimary} disabled={submitting}>
              {submitting ? 'Running…' : 'Run'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
