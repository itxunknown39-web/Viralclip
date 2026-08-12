export function formatTime(seconds) {
  if (seconds == null || Number.isNaN(Number(seconds))) return '--:--'
  const s = Math.max(0, Math.floor(Number(seconds)))
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  if (h > 0) return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
}

export function formatDuration(seconds) {
  if (seconds == null) return ''
  const s = Math.round(Number(seconds))
  if (s >= 3600) {
    const h = Math.floor(s / 3600)
    const m = Math.round((s % 3600) / 60)
    return `${h}h ${m}m`
  }
  if (s >= 60) {
    const m = Math.floor(s / 60)
    const sec = s % 60
    return `${m}m ${sec}s`
  }
  return `${s}s`
}