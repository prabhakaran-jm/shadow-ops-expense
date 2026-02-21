import { useState, useCallback, useEffect } from 'react'
import type { ExecutionResult, WorkflowDetail, WorkflowListItem } from '../api/types'
import {
  getWorkflows,
  getWorkflow,
  approveWorkflow,
  generateAgent,
  getHealth,
} from '../api/client'
import ReceiptUpload from '../components/ReceiptUpload'
import RunAgentModal from '../components/RunAgentModal'
import styles from './Dashboard.module.css'

export default function Dashboard() {
  const [list, setList] = useState<WorkflowListItem[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [detail, setDetail] = useState<WorkflowDetail | null>(null)
  const [listLoading, setListLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [approvingId, setApprovingId] = useState<string | null>(null)
  const [approvedIds, setApprovedIds] = useState<Set<string>>(new Set())
  const [generatedIds, setGeneratedIds] = useState<Set<string>>(new Set())
  const [generatingId, setGeneratingId] = useState<string | null>(null)
  const [runModalSessionId, setRunModalSessionId] = useState<string | null>(null)
  const [latestRunBySession, setLatestRunBySession] = useState<Record<string, ExecutionResult>>({})
  const [error, setError] = useState<string | null>(null)
  const [healthInfo, setHealthInfo] = useState<{ mode: string; version: string } | null>(null)
  const [copyHint, setCopyHint] = useState<string | null>(null)

  useEffect(() => {
    getHealth()
      .then((h) =>
        setHealthInfo({
          mode: h.mode ?? 'unknown',
          version: h.version ?? '—',
        })
      )
      .catch(() => setHealthInfo(null))
  }, [])

  const demoFlowCommand = 'python backend/scripts/demo_flow.py'
  const handleCopyDemoCommand = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(demoFlowCommand)
      setCopyHint('Copied!')
      setTimeout(() => setCopyHint(null), 2000)
    } catch {
      setCopyHint('Copy failed')
    }
  }, [])

  const loadList = useCallback(async () => {
    setError(null)
    setListLoading(true)
    try {
      const data = await getWorkflows()
      setList(data)
      if (data.length > 0 && !selectedId) setSelectedId(data[0].session_id)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load workflows')
    } finally {
      setListLoading(false)
    }
  }, [selectedId])

  useEffect(() => {
    loadList()
  }, [loadList])

  useEffect(() => {
    if (!selectedId) {
      setDetail(null)
      return
    }
    setError(null)
    setDetailLoading(true)
    setDetail(null)
    getWorkflow(selectedId)
      .then(setDetail)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load workflow'))
      .finally(() => setDetailLoading(false))
  }, [selectedId])

  const handleApprove = useCallback(async (sessionId: string) => {
    setError(null)
    setApprovingId(sessionId)
    try {
      await approveWorkflow(sessionId)
      setApprovedIds((prev) => new Set(prev).add(sessionId))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Approval failed')
    } finally {
      setApprovingId(null)
    }
  }, [])

  const handleGenerateAgent = useCallback(async (sessionId: string) => {
    setError(null)
    setGeneratingId(sessionId)
    try {
      await generateAgent(sessionId)
      setGeneratedIds((prev) => new Set(prev).add(sessionId))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Generate agent failed')
    } finally {
      setGeneratingId(null)
    }
  }, [])

  const handleRunSuccess = useCallback((sessionId: string, result: ExecutionResult) => {
    setLatestRunBySession((prev) => ({ ...prev, [sessionId]: result }))
  }, [])

  return (
    <div className={styles.dashboard}>
      {healthInfo !== null && (
        <div className={styles.demoBanner}>
          <span>
            Demo Mode: <span className={healthInfo.mode === 'real' ? styles.modeReal : styles.modeMock}>●</span> NOVA_MODE={healthInfo.mode} | v{healthInfo.version}
          </span>
          <div className={styles.demoBannerActions}>
            <button
              type="button"
              className={styles.copyButton}
              onClick={handleCopyDemoCommand}
              title="Copy demo_flow command"
            >
              {copyHint ?? 'Copy demo_flow command'}
            </button>
          </div>
        </div>
      )}

      <header className={styles.header}>
        <h1 className={styles.title}>Workflow review</h1>
        <p className={styles.subtitle}>
          Select a workflow to view details and approve for execution.
        </p>
      </header>

      <ReceiptUpload
        onWorkflowCreated={(sessionId) => {
          loadList()
          setSelectedId(sessionId)
        }}
      />

      {error && (
        <div className={styles.errorBanner} role="alert">
          {error}
        </div>
      )}

      <div className={styles.layout}>
        <aside className={styles.sidebar}>
          <h2 className={styles.sidebarTitle}>Workflows</h2>
          {listLoading ? (
            <p className={styles.muted}>Loading…</p>
          ) : list.length === 0 ? (
            <p className={styles.muted}>No workflows yet.</p>
          ) : (
            <ul className={styles.workflowList}>
              {list.map((w) => (
                <li key={w.session_id}>
                  <button
                    type="button"
                    className={
                      selectedId === w.session_id
                        ? styles.workflowItemActive
                        : styles.workflowItem
                    }
                    onClick={() => setSelectedId(w.session_id)}
                  >
                    <span className={styles.workflowItemTitle}>{w.title || w.session_id}</span>
                    <span className={styles.workflowItemMeta}>
                      {w.risk_level} · {w.time_saved_minutes} min saved
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>

        <main className={styles.main}>
          {!selectedId ? (
            <div className={styles.placeholder}>Select a workflow</div>
          ) : detailLoading ? (
            <div className={styles.placeholder}>Loading…</div>
          ) : detail ? (
            <>
              <div className={styles.detailHeader}>
                <h2 className={styles.detailTitle}>{detail.title}</h2>
                <div className={styles.badges}>
                  <span className={styles.badgeRisk}>{detail.risk_level}</span>
                  <span className={styles.badgeTime}>
                    {detail.time_saved_minutes} min saved
                  </span>
                </div>
              </div>
              {detail.description && (
                <p className={styles.description}>{detail.description}</p>
              )}

              {detail.parameters && detail.parameters.length > 0 && (
                <section className={styles.section}>
                  <h3 className={styles.sectionTitle}>Parameters</h3>
                  <div className={styles.tableWrap}>
                    <table className={styles.table}>
                      <thead>
                        <tr>
                          <th>Name</th>
                          <th>Type</th>
                          <th>Required</th>
                          <th>Example</th>
                        </tr>
                      </thead>
                      <tbody>
                        {detail.parameters.map((p) => (
                          <tr key={p.name}>
                            <td className={styles.cellName}>{p.name}</td>
                            <td>{p.type}</td>
                            <td>{p.required ? 'Yes' : 'No'}</td>
                            <td className={styles.cellMono}>
                              {p.example ?? '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              )}

              {detail.steps && detail.steps.length > 0 && (
                <section className={styles.section}>
                  <h3 className={styles.sectionTitle}>Steps</h3>
                  <ol className={styles.stepsList}>
                    {detail.steps
                      .slice()
                      .sort((a, b) => a.order - b.order)
                      .map((step) => (
                        <li key={step.order} className={styles.stepItem}>
                          <span className={styles.stepOrder}>{step.order}</span>
                          <div className={styles.stepBody}>
                            <span className={styles.stepIntent}>{step.intent}</span>
                            <p className={styles.stepInstruction}>{step.instruction}</p>
                            {step.uses_parameters.length > 0 && (
                              <span className={styles.stepParams}>
                                Uses: {step.uses_parameters.join(', ')}
                              </span>
                            )}
                          </div>
                        </li>
                      ))}
                  </ol>
                </section>
              )}

              <div className={styles.actions}>
                {approvedIds.has(detail.session_id) ? (
                  <span className={styles.approvedLabel}>Approved</span>
                ) : (
                  <button
                    type="button"
                    className={styles.buttonPrimary}
                    onClick={() => handleApprove(detail.session_id)}
                    disabled={approvingId === detail.session_id}
                  >
                    {approvingId === detail.session_id ? 'Approving…' : 'Approve'}
                  </button>
                )}
                {approvedIds.has(detail.session_id) && (
                  <>
                    {generatedIds.has(detail.session_id) ? (
                      <button
                        type="button"
                        className={styles.buttonPrimary}
                        onClick={() => setRunModalSessionId(detail.session_id)}
                      >
                        Run Agent
                      </button>
                    ) : (
                      <button
                        type="button"
                        className={styles.buttonSecondary}
                        onClick={() => handleGenerateAgent(detail.session_id)}
                        disabled={generatingId === detail.session_id}
                      >
                        {generatingId === detail.session_id ? 'Generating…' : 'Generate Agent'}
                      </button>
                    )}
                  </>
                )}
              </div>

              {latestRunBySession[detail.session_id] && (
                <section className={styles.resultsSection}>
                  <h3 className={styles.sectionTitle}>Latest run</h3>
                  <RunResultPanel result={latestRunBySession[detail.session_id]} />
                </section>
              )}
            </>
          ) : null}
        </main>
      </div>

      {runModalSessionId && (
        <RunAgentModal
          sessionId={runModalSessionId}
          onClose={() => setRunModalSessionId(null)}
          onSuccess={(result) => {
            handleRunSuccess(runModalSessionId, result)
            setRunModalSessionId(null)
          }}
        />
      )}
    </div>
  )
}

function RunResultPanel({ result }: { result: ExecutionResult }) {
  return (
    <div className={styles.resultPanel}>
      <div className={styles.resultMeta}>
        <span className={styles.resultStatus}>{result.status}</span>
        {result.confirmation_id && (
          <span className={styles.resultConfirmation}>
            Confirmation: {result.confirmation_id}
          </span>
        )}
      </div>
      <ul className={styles.runLog}>
        {result.run_log.map((msg, i) => {
          const isAdaptation =
            msg.includes('UI changed') ||
            msg.includes('retry') ||
            msg.includes('adapted') ||
            msg.includes('retrying')
          return (
            <li
              key={i}
              className={
                isAdaptation
                  ? `${styles.runLogItem} ${styles.runLogItemAdaptation}`
                  : styles.runLogItem
              }
            >
              {msg}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
