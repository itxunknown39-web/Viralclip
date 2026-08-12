import { useEffect, useMemo, useState } from 'react'
import { generateClip } from '../api/client.js'
import { useProgress } from '../hooks/useProgress.js'
import { clipDownloadUrl } from '../api/client.js'

export default function GeneratePanel({ candidateId, jobId, onJobReady }) {
  const [aspect, setAspect] = useState('9:16')
  const [captions, setCaptions] = useState(true)
  const [captionStyle, setCaptionStyle] = useState('hormozi_green')
  const [effects, setEffects] = useState(false)
  const [genJobId, setGenJobId] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const progress = useProgress(genJobId)
  const done = progress.status === 'completed'
  const failed = progress.status === 'failed'

  useEffect(() => {
    if (done && genJobId) {
      onJobReady?.(genJobId)
    }
  }, [done, genJobId, onJobReady])

  async function handleGenerate() {
    setBusy(true)
    setError(null)
    try {
      const payload = {
        aspect_ratio: aspect,
        width: aspect === '9:16' ? 1080 : 1920,
        height: aspect === '9:16' ? 1920 : 1080,
        caption_style: captionStyle,
        captions,
        effects,
      }
      const res = await generateClip(candidateId, jobId, payload)
      setGenJobId(res.job_id)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (done) {
    return (
      <div className="generate-panel done">
        <span className="badge green">Clip Ready</span>
        <a className="btn primary" href={clipDownloadUrl(genJobId)}>
          Download MP4
        </a>
      </div>
    )
  }

  return (
    <div className="generate-panel">
      <div className="generate-grid">
        <label className="field">
          <span>Aspect</span>
          <select className="input" value={aspect} onChange={(e) => setAspect(e.target.value)} disabled={busy || genJobId}>
            <option value="9:16">9:16 (1080×1920)</option>
            <option value="16:9">16:9 (1920×1080)</option>
          </select>
        </label>
        <label className="field">
          <span>Captions</span>
          <select className="input" value={captions ? 'on' : 'off'} onChange={(e) => setCaptions(e.target.value === 'on')} disabled={busy || genJobId}>
            <option value="on">On</option>
            <option value="off">Off</option>
          </select>
        </label>
        <label className="field">
          <span>Style</span>
          <select className="input" value={captionStyle} onChange={(e) => setCaptionStyle(e.target.value)} disabled={busy || genJobId || !captions}>
            <option value="hormozi_green">Hormozi Green</option>
            <option value="hormozi_yellow">Hormozi Yellow</option>
            <option value="bold_white">Bold White</option>
            <option value="beast_pop">Beast Pop</option>
            <option value="one_word_punch">One Word Punch</option>
            <option value="word_reveal">Word Reveal</option>
            <option value="boxed_tiktok">Boxed TikTok</option>
            <option value="comic_punch">Comic Punch</option>
            <option value="serif_elegant">Serif Elegant</option>
          </select>
        </label>
        <label className="field">
          <span>Effects</span>
          <select className="input" value={effects ? 'on' : 'off'} onChange={(e) => setEffects(e.target.value === 'on')} disabled={busy || genJobId}>
            <option value="off">Off</option>
            <option value="on">Subtle Zoom</option>
          </select>
        </label>
      </div>

      {genJobId && (
        <div className="gen-progress">
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${progress.progress || 0}%` }} />
          </div>
          <div className="progress-row">
            <span className="progress-message">
              {failed ? (progress.error || 'Rendering failed') : progress.message || 'Generating…'}
            </span>
            <span className="progress-pct">{Math.round(progress.progress || 0)}%</span>
          </div>
        </div>
      )}

      {error && <p className="text-error">{error}</p>}

      {!genJobId && (
        <button className="btn primary btn-block" onClick={handleGenerate} disabled={busy}>
          {busy ? 'Starting…' : 'Generate Clip'}
        </button>
      )}
    </div>
  )
}