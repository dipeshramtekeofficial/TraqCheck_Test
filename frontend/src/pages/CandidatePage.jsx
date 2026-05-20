import { useEffect, useState, useCallback } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getCandidate } from '../api'
import ProfileView from '../components/ProfileView.jsx'
import RequestPanel from '../components/RequestPanel.jsx'
import DocumentSection from '../components/DocumentSection.jsx'

export default function CandidatePage() {
  const { id } = useParams()
  const [candidate, setCandidate] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    try {
      const c = await getCandidate(id)
      setCandidate(c)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { refresh() }, [refresh])

  // Poll while extraction is in flight
  useEffect(() => {
    if (!candidate) return
    if (candidate.extraction_status !== 'processing' && candidate.extraction_status !== 'pending') return
    const t = setInterval(refresh, 1500)
    return () => clearInterval(t)
  }, [candidate, refresh])

  if (loading) return <div className="empty">Loading candidate…</div>
  if (error) return <div className="error">{error}</div>
  if (!candidate) return null

  return (
    <>
      <div style={{ marginBottom: 14 }}>
        <Link to="/">← Back to dashboard</Link>
      </div>

      <ProfileView candidate={candidate} />
      <RequestPanel candidate={candidate} onCreated={refresh} />
      <DocumentSection candidate={candidate} onUpdated={refresh} />
    </>
  )
}
