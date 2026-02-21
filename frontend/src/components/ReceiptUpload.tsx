import { useState, useRef } from 'react'
import type { ReceiptExtractionResult } from '../api/types'
import { uploadReceipt } from '../api/client'
import styles from './ReceiptUpload.module.css'

type Props = {
  onWorkflowCreated: (sessionId: string) => void
}

const ACCEPT = 'image/jpeg,image/png,image/gif,image/webp'

export default function ReceiptUpload({ onWorkflowCreated }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ReceiptExtractionResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const f = e.dataTransfer.files[0]
    if (f && ACCEPT.split(',').some((t) => t.trim() === f.type)) {
      setFile(f)
      setResult(null)
      setError(null)
      if (previewUrl) URL.revokeObjectURL(previewUrl)
      setPreviewUrl(URL.createObjectURL(f))
    }
  }

  const handleDragOver = (e: React.DragEvent) => e.preventDefault()

  const handleSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f && ACCEPT.split(',').some((t) => t.trim() === f.type)) {
      setFile(f)
      setResult(null)
      setError(null)
      if (previewUrl) URL.revokeObjectURL(previewUrl)
      setPreviewUrl(URL.createObjectURL(f))
    }
    e.target.value = ''
  }

  const handleUpload = async () => {
    if (!file) return
    setError(null)
    setLoading(true)
    try {
      const res = await uploadReceipt(file)
      setResult(res)
      onWorkflowCreated(res.session_id)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  const handleTryAgain = () => {
    setFile(null)
    setResult(null)
    setError(null)
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
      setPreviewUrl(null)
    }
    inputRef.current?.click()
  }

  return (
    <section className={styles.section}>
      <h3 className={styles.sectionTitle}>Upload receipt</h3>
      <div
        className={styles.dropZone}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          onChange={handleSelect}
          className={styles.hiddenInput}
          aria-label="Select receipt image"
        />
        {!file ? (
          <>
            <p className={styles.dropText}>Drop a receipt image here</p>
            <p className={styles.dropSub}>or</p>
            <button
              type="button"
              className={styles.browseButton}
              onClick={() => inputRef.current?.click()}
            >
              Browse
            </button>
          </>
        ) : (
          <div className={styles.previewRow}>
            {previewUrl && (
              <img
                src={previewUrl}
                alt="Receipt preview"
                className={styles.thumbnail}
              />
            )}
            <div className={styles.previewInfo}>
              <p className={styles.fileName}>{file.name}</p>
              {loading ? (
                <p className={styles.processing}>Processing…</p>
              ) : result ? (
                <>
                  <div className={styles.extracted}>
                    <span><strong>Amount:</strong> {result.extracted.amount ?? '—'}</span>
                    <span><strong>Merchant:</strong> {result.extracted.merchant ?? '—'}</span>
                    <span><strong>Date:</strong> {result.extracted.date ?? '—'}</span>
                    <span><strong>Category:</strong> {result.extracted.category ?? '—'}</span>
                    <span><strong>Confidence:</strong> {Math.round((result.extracted.confidence ?? 0) * 100)}%</span>
                  </div>
                  <div className={styles.badgeRow}>
                    <span className={styles.badgeGreen}>Workflow created</span>
                    <span className={styles.sessionId}>{result.session_id}</span>
                  </div>
                </>
              ) : (
                <button
                  type="button"
                  className={styles.uploadButton}
                  onClick={handleUpload}
                >
                  Process receipt
                </button>
              )}
            </div>
          </div>
        )}
      </div>
      {error && (
        <div className={styles.errorRow}>
          <span className={styles.errorText}>{error}</span>
          <button type="button" className={styles.tryAgain} onClick={handleTryAgain}>
            Try again
          </button>
        </div>
      )}
    </section>
  )
}
