import { useNavigate } from 'react-router-dom'

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

export default function CandidateTable({ candidates }) {
  const nav = useNavigate()

  if (!candidates.length) {
    return <div className="empty">No candidates yet. Upload a resume to get started.</div>
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Email</th>
          <th>Company</th>
          <th>Status</th>
          <th>Uploaded</th>
        </tr>
      </thead>
      <tbody>
        {candidates.map((c) => (
          <tr key={c.id} className="clickable" onClick={() => nav(`/candidates/${c.id}`)}>
            <td>{c.name || <span className="muted">—</span>}</td>
            <td>{c.email || <span className="muted">—</span>}</td>
            <td>{c.company || <span className="muted">—</span>}</td>
            <td><span className={`badge ${c.extraction_status}`}>{c.extraction_status}</span></td>
            <td className="muted">{formatDate(c.created_at)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
