const STAGES = [
  { key: 'downloading', label: 'Downloading video' },
  { key: 'extracting_audio', label: 'Extracting audio' },
  { key: 'transcribing', label: 'Transcribing with Whisper' },
  { key: 'finding_candidates', label: 'Finding candidate moments' },
  { key: 'ai_analysis', label: 'AI viral analysis' },
  { key: 'ranking', label: 'Ranking clips' },
]

const ORDER = [
  'downloading',
  'extracting_audio',
  'transcribing',
  'finding_candidates',
  'ai_analysis',
  'ranking',
]

export default function AnalysisProgress({ stage, progress, message, status, error }) {
  const currentIdx = ORDER.indexOf(stage)
  const failed = status === 'failed'

  return (
    <div className="card progress-card">
      <h2 className="card-title">Analyzing your video</h2>

      <ul className="stage-list">
        {STAGES.map((s, i) => {
          let state = 'pending'
          if (failed && i === currentIdx) state = 'error'
          else if (i < currentIdx || status === 'completed') state = 'done'
          else if (i === currentIdx) state = 'active'
          return (
            <li key={s.key} className={`stage ${state}`}>
              <span className="stage-icon">{state === 'done' ? '✓' : state === 'active' ? '●' : state === 'error' ? '✕' : '○'}</span>
              {s.label}
            </li>
          )
        })}
      </ul>

      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${Math.min(Math.max(progress || 0, 0), 100)}%` }} />
      </div>
      <div className="progress-row">
        <span className="progress-message">
          {failed ? (error || 'Analysis failed') : message || 'Working…'}
        </span>
        <span className="progress-pct">{Math.round(progress || 0)}%</span>
      </div>
    </div>
  )
}