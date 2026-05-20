// Thin wrapper around fetch. We rely on Vite's dev proxy in development.
const BASE = import.meta.env.VITE_API_BASE || ''

async function handle(res) {
  if (!res.ok) {
    let detail
    try {
      const body = await res.json()
      detail = body.detail || JSON.stringify(body)
    } catch {
      detail = await res.text()
    }
    throw new Error(detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

export async function listCandidates() {
  return handle(await fetch(`${BASE}/candidates`))
}

export async function getCandidate(id) {
  return handle(await fetch(`${BASE}/candidates/${id}`))
}

// Wraps an XHR so the caller can subscribe to progress updates.
export function uploadResume(file, onProgress) {
  return new Promise((resolve, reject) => {
    const form = new FormData()
    form.append('file', file)

    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${BASE}/candidates/upload`)
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    }
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try { resolve(JSON.parse(xhr.responseText)) } catch { resolve(null) }
      } else {
        let msg = `Upload failed (${xhr.status})`
        try { msg = JSON.parse(xhr.responseText).detail || msg } catch { /* keep default */ }
        reject(new Error(msg))
      }
    }
    xhr.onerror = () => reject(new Error('Network error during upload'))
    xhr.send(form)
  })
}

export async function requestDocuments(id) {
  const res = await fetch(`${BASE}/candidates/${id}/request-documents`, {
    method: 'POST',
  })
  return handle(res)
}

export async function submitDocuments(id, { pan, aadhaar }) {
  const form = new FormData()
  if (pan) form.append('pan', pan)
  if (aadhaar) form.append('aadhaar', aadhaar)
  const res = await fetch(`${BASE}/candidates/${id}/submit-documents`, {
    method: 'POST',
    body: form,
  })
  return handle(res)
}

export async function deleteDocument(candidateId, docId) {
  const res = await fetch(`${BASE}/candidates/${candidateId}/documents/${docId}`, {
    method: 'DELETE',
  })
  if (!res.ok && res.status !== 204) {
    let detail
    try { detail = (await res.json()).detail } catch { detail = await res.text() }
    throw new Error(detail || `Delete failed: ${res.status}`)
  }
}
