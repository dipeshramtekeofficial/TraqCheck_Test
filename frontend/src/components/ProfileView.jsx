function pct(v) {
  if (v === undefined || v === null) return null
  return `${Math.round(v * 100)}%`
}

function FieldRow({ label, value, confidence }) {
  return (
    <div className="field">
      <div className="label">{label}</div>
      <div className="value">
        {value || <span className="muted">—</span>}
        {value && confidence !== undefined && confidence !== null && (
          <span className="conf">confidence {pct(confidence)}</span>
        )}
      </div>
    </div>
  )
}

export default function ProfileView({ candidate }) {
  const conf = candidate.confidence || {}
  const skills = candidate.skills || []

  return (
    <div className="card">
      <h2 className="section-title">
        Extracted profile{' '}
        <span className={`badge ${candidate.extraction_status}`}>{candidate.extraction_status}</span>
      </h2>

      {candidate.extraction_status === 'failed' && (
        <div className="error" style={{ marginBottom: 12 }}>
          Extraction failed: {candidate.extraction_error || 'unknown error'}
        </div>
      )}
      {candidate.extraction_error && candidate.extraction_status !== 'failed' && (
        <div className="error" style={{ marginBottom: 12, background: '#fffbeb', borderColor: '#fde68a', color: '#92400e' }}>
          Note: {candidate.extraction_error}
        </div>
      )}

      <FieldRow label="Name" value={candidate.name} confidence={conf.name} />
      <FieldRow label="Email" value={candidate.email} confidence={conf.email} />
      <FieldRow label="Phone" value={candidate.phone} confidence={conf.phone} />
      <FieldRow label="Company" value={candidate.company} confidence={conf.company} />
      <FieldRow label="Designation" value={candidate.designation} confidence={conf.designation} />

      <div className="field">
        <div className="label">Skills</div>
        <div className="value">
          {skills.length === 0
            ? <span className="muted">—</span>
            : skills.map((s) => <span key={s} className="chip">{s}</span>)}
        </div>
      </div>
    </div>
  )
}
