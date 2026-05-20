import { useRef, useState } from 'react'
import { uploadResume } from '../api'

const ACCEPTED = ['.pdf', '.docx', '.doc']

export default function ResumeUpload({ onUploaded }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [progress, setProgress] = useState(0)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)

  async function handleFile(file) {
    setError(null)
    if (!file) return
    const ext = '.' + (file.name.split('.').pop() || '').toLowerCase()
    if (!ACCEPTED.includes(ext)) {
      setError(`Please upload a PDF or DOCX file (got ${ext || 'unknown'})`)
      return
    }
    setUploading(true)
    setProgress(0)
    try {
      const cand = await uploadResume(file, setProgress)
      onUploaded?.(cand)
    } catch (e) {
      setError(e.message)
    } finally {
      setUploading(false)
      setProgress(0)
    }
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files?.[0]
    handleFile(f)
  }

  return (
    <div className="card">
      <h2 className="section-title">Upload a resume</h2>
      <div
        className={`dropzone ${dragging ? 'dragging' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !uploading && inputRef.current?.click()}
        role="button"
        tabIndex={0}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.doc"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
        <p style={{ fontSize: 15, color: 'var(--text)' }}>
          {dragging ? 'Drop the resume to upload' : 'Drag & drop, or click to choose'}
        </p>
        <p className="hint">PDF or DOCX, max 10 MB</p>

        {uploading && (
          <div className="progress">
            <div style={{ width: `${progress}%` }} />
          </div>
        )}
      </div>

      {error && <div className="error" style={{ marginTop: 12 }}>{error}</div>}
    </div>
  )
}
