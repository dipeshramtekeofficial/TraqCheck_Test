import { useState } from 'react'
import { submitDocuments, deleteDocument } from '../api'

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

export default function DocumentSection({ candidate, onUpdated }) {
  const [pan, setPan] = useState(null)
  const [aadhaar, setAadhaar] = useState(null)
  const [busy, setBusy] = useState(false)
  const [deletingId, setDeletingId] = useState(null)
  const [error, setError] = useState(null)

  async function handleSubmit() {
    if (!pan && !aadhaar) {
      setError('Select at least one document to upload')
      return
    }
    setError(null)
    setBusy(true)
    try {
      await submitDocuments(candidate.id, { pan, aadhaar })
      setPan(null); setAadhaar(null)
      onUpdated?.()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleDelete(doc) {
    const label = doc.original_filename || doc.doc_type.toUpperCase()
    if (!window.confirm(`Delete ${label}? This can't be undone.`)) return
    setError(null)
    setDeletingId(doc.id)
    try {
      await deleteDocument(candidate.id, doc.id)
      onUpdated?.()
    } catch (e) {
      setError(e.message)
    } finally {
      setDeletingId(null)
    }
  }

  const docs = candidate.documents || []

  return (
    <div className="card">
      <h2 className="section-title">Submitted documents</h2>

      {docs.length === 0
        ? <div className="empty" style={{ padding: 16 }}>No documents uploaded yet.</div>
        : (
          <table>
            <thead>
              <tr><th>Type</th><th>File</th><th>Uploaded</th><th style={{ width: 140 }}></th></tr>
            </thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.id}>
                  <td style={{ textTransform: 'uppercase' }}>{d.doc_type}</td>
                  <td>{d.original_filename || '—'}</td>
                  <td className="muted">{formatDate(d.uploaded_at)}</td>
                  <td style={{ whiteSpace: 'nowrap' }}>
                    <a href={`/candidates/${candidate.id}/documents/${d.id}`} target="_blank" rel="noreferrer">View</a>
                    <button
                      onClick={() => handleDelete(d)}
                      disabled={deletingId === d.id}
                      style={{
                        marginLeft: 12,
                        padding: '2px 10px',
                        fontSize: 12,
                        color: 'var(--bad)',
                        borderColor: '#fecaca',
                      }}
                    >
                      {deletingId === d.id ? 'Deleting…' : 'Delete'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )
      }

      <div style={{ marginTop: 16 }}>
        <p className="muted" style={{ marginTop: 0 }}>Upload PAN and/or Aadhaar on behalf of the candidate:</p>
        <div className="doc-uploader">
          <div>
            <label>PAN</label>
            <input type="file" accept=".pdf,.png,.jpg,.jpeg,.webp" onChange={(e) => setPan(e.target.files?.[0] || null)} />
          </div>
          <div>
            <label>Aadhaar</label>
            <input type="file" accept=".pdf,.png,.jpg,.jpeg,.webp" onChange={(e) => setAadhaar(e.target.files?.[0] || null)} />
          </div>
        </div>
        <div className="actions">
          <button className="primary" onClick={handleSubmit} disabled={busy || (!pan && !aadhaar)}>
            {busy ? 'Uploading…' : 'Upload documents'}
          </button>
        </div>
        {error && <div className="error" style={{ marginTop: 12 }}>{error}</div>}
      </div>
    </div>
  )
}
