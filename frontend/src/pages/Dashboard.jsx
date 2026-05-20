import { useEffect, useState, useCallback } from 'react'
import { listCandidates } from '../api'
import ResumeUpload from '../components/ResumeUpload.jsx'
import CandidateTable from '../components/CandidateTable.jsx'

export default function Dashboard() {
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refresh = useCallback(async () => {
    try {
      const data = await listCandidates()
      setCandidates(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  // Poll while any candidate is still being processed so the table flips to "done" on its own.
  useEffect(() => {
    const anyPending = candidates.some(c => c.extraction_status === 'processing' || c.extraction_status === 'pending')
    if (!anyPending) return
    const t = setInterval(refresh, 2000)
    return () => clearInterval(t)
  }, [candidates, refresh])

  return (
    <>
      <ResumeUpload onUploaded={() => refresh()} />

      <div className="card" style={{ marginTop: 20 }}>
        <h2 className="section-title">Candidates</h2>
        {error && <div className="error">{error}</div>}
        {loading ? <div className="empty">Loading…</div> : <CandidateTable candidates={candidates} />}
      </div>
    </>
  )
}
