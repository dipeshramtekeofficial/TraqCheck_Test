import { useState } from 'react'
import { requestDocuments } from '../api'

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

function statusLabel(s) {
  if (s === 'sent') return 'sent ✓'
  if (s === 'send_failed') return 'send failed'
  return s
}

function RequestEntry({ req }) {
  return (
    <div className="request-card">
      <div className="meta">
        <span>to {req.recipient}</span>
        <span style={{ color: req.status === 'send_failed' ? 'var(--bad)' : undefined }}>
          {statusLabel(req.status)}
        </span>
        <span>{formatDate(req.created_at)}</span>
      </div>
      {req.subject && <div style={{ marginBottom: 6, fontWeight: 600 }}>{req.subject}</div>}
      <pre>{req.message}</pre>
      {req.error && (
        <div className="error" style={{ marginTop: 10 }}>
          Delivery error: {req.error}
        </div>
      )}
    </div>
  )
}

export default function RequestPanel({ candidate, onCreated }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const canRequest = candidate.extraction_status === 'done' && !!candidate.email

  async function trigger() {
    setError(null)
    setBusy(true)
    try {
      await requestDocuments(candidate.id)
      onCreated?.()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const reqs = candidate.requests || []

  return (
    <div className="card">
      <h2 className="section-title">Document request</h2>
      <p className="muted" style={{ marginTop: 0 }}>
        Trigger the AI agent to compose and send a personalized email request for PAN &amp; Aadhaar.
      </p>

      <div className="actions">
        <button className="primary" onClick={trigger} disabled={!canRequest || busy}>
          {busy ? 'Working…' : 'Request documents'}
        </button>
      </div>

      {!canRequest && candidate.extraction_status !== 'done' && (
        <p className="muted" style={{ marginTop: 10 }}>Waiting for extraction to finish.</p>
      )}
      {!canRequest && candidate.extraction_status === 'done' && (
        <p className="muted" style={{ marginTop: 10 }}>No email address available for this candidate.</p>
      )}
      {error && <div className="error" style={{ marginTop: 12 }}>{error}</div>}

      {reqs.length > 0 && (
        <div style={{ marginTop: 18 }}>
          <h3 style={{ fontSize: 13, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em', margin: '0 0 6px' }}>
            History
          </h3>
          {reqs.map((r) => <RequestEntry key={r.id} req={r} />)}
        </div>
      )}
    </div>
  )
}
