const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  if (res.status === 204) return null
  return res.json()
}

export function analyzeVideo(data) {
  return request('/api/analyze', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function getResults(jobId) {
  return request(`/api/results/${jobId}`)
}

export function fetchMetadata(url) {
  return request(`/api/metadata?url=${encodeURIComponent(url)}`)
}

export function generateClip(candidateId, analysisJobId, options) {
  return request(
    `/api/clips/${encodeURIComponent(candidateId)}/generate?analysis_job_id=${analysisJobId}`,
    {
      method: 'POST',
      body: JSON.stringify(options),
    },
  )
}

export function getClipStatus(clipId) {
  return request(`/api/clips/${clipId}/status`)
}

export function getHistory() {
  return request('/api/history')
}

export function getDevices() {
  return request('/api/devices')
}

export function getSettings() {
  return request('/api/settings')
}

export function updateSettings(data) {
  return request('/api/settings', { method: 'POST', body: JSON.stringify(data) })
}

export function retryAI(jobId) {
  return request(`/api/jobs/${jobId}/retry-ai`, { method: 'POST' })
}

export function clipDownloadUrl(clipId) {
  return `${API_BASE}/api/clips/${clipId}/download`
}

export function subscribeToProgress(jobId, onEvent) {
  const source = new EventSource(`${API_BASE}/api/progress/${jobId}`)
  source.onmessage = (e) => {
    try {
      onEvent(JSON.parse(e.data))
    } catch {
      /* ignore malformed keepalive */
    }
  }
  source.onerror = () => {
    /* browser may retry automatically; hook closes on terminal event */
  }
  return source
}