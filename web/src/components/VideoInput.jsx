import { useState } from 'react'
import { fetchMetadata } from '../api/client.js'
import { formatDuration } from '../utils/formatTime.js'

const ASPECTS = ['9:16', '16:9']
const DURATIONS = [
  { label: '20–60 sec', min: 20, max: 60 },
  { label: '15–30 sec', min: 15, max: 30 },
  { label: '30–45 sec', min: 30, max: 45 },
  { label: '45–90 sec', min: 45, max: 90 },
]

export default function VideoInput({ onAnalyze, busy }) {
  const [url, setUrl] = useState('')
  const [clipCount, setClipCount] = useState(5)
  const [duration, setDuration] = useState(DURATIONS[0])
  const [aspect, setAspect] = useState('9:16')
  const [meta, setMeta] = useState(null)
  const [metaError, setMetaError] = useState(null)
  const [checking, setChecking] = useState(false)

  async function handleCheck() {
    const trimmed = url.trim()
    if (!trimmed) return
    setChecking(true)
    setMetaError(null)
    setMeta(null)
    try {
      const info = await fetchMetadata(trimmed)
      setMeta(info)
    } catch (err) {
      setMetaError(err.message)
    } finally {
      setChecking(false)
    }
  }

  function handleAnalyze() {
    if (!url.trim() || busy) return
    onAnalyze({
      url: url.trim(),
      clip_count: clipCount,
      min_duration: duration.min,
      max_duration: duration.max,
      options: { aspect_ratio: aspect, captions: true, effects: false },
    })
  }

  return (
    <div className="card input-card">
      <h2 className="card-title">Find Your Viral Moments</h2>
      <p className="card-sub">Paste a YouTube or video URL. AI finds the clips worth Shorts.</p>

      <div className="url-row">
        <input
          type="text"
          className="input"
          placeholder="Paste YouTube or video URL…"
          value={url}
          disabled={busy}
          onChange={(e) => {
            setUrl(e.target.value)
            setMeta(null)
            setMetaError(null)
          }}
          onKeyDown={(e) => e.key === 'Enter' && (meta ? handleAnalyze() : handleCheck())}
        />
        <button className="btn ghost" onClick={handleCheck} disabled={busy || checking || !url.trim()}>
          {checking ? 'Checking…' : 'Validate'}
        </button>
      </div>

      {metaError && <p className="text-error">{metaError}</p>}

      {meta && (
        <div className="video-meta">
          {meta.thumbnail && <img src={meta.thumbnail} alt="" className="meta-thumb" />}
          <div className="meta-info">
            <div className="meta-title">{meta.title || 'Untitled video'}</div>
            <div className="meta-sub">
              {meta.channel ? `By ${meta.channel} · ` : ''}
              {formatDuration(meta.duration)}
              {meta.width ? ` · ${meta.width}×${meta.height}` : ''}
            </div>
          </div>
        </div>
      )}

      <div className="options-grid">
        <label className="field">
          <span>Number of Clips</span>
          <select
            className="input"
            value={clipCount}
            disabled={busy}
            onChange={(e) => setClipCount(Number(e.target.value))}
          >
            {[3, 5, 10, 20].map((n) => (
              <option key={n} value={n}>
                Top {n}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Clip Duration</span>
          <select
            className="input"
            value={duration.label}
            disabled={busy}
            onChange={(e) => setDuration(DURATIONS.find((d) => d.label === e.target.value))}
          >
            {DURATIONS.map((d) => (
              <option key={d.label} value={d.label}>
                {d.label}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Aspect Ratio</span>
          <select
            className="input"
            value={aspect}
            disabled={busy}
            onChange={(e) => setAspect(e.target.value)}
          >
            {ASPECTS.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </label>
      </div>

      <button className="btn primary btn-block" onClick={handleAnalyze} disabled={busy || !url.trim()}>
        {busy ? 'Analyzing…' : 'Analyze Video'}
      </button>
    </div>
  )
}