import { Link } from 'react-router-dom'
import { formatScore, scoreColor } from '../utils/formatScore.js'

export default function HistoryList({ projects }) {
  if (!projects || projects.length === 0) {
    return <p className="empty">No projects yet. Analyze your first video.</p>
  }
  return (
    <div className="history-list">
      {projects.map((p) => (
        <div className="card history-row" key={p.job_id}>
          <div className="history-main">
            <div className="history-title">{p.source_title || 'Untitled video'}</div>
            <div className="history-sub">
              {p.created_at} · {p.clip_count} clips · {p.generated_clips} generated
            </div>
          </div>
          {p.best_score > 0 && (
            <span className={`virality ${scoreColor(p.best_score)}`}>
              {formatScore(p.best_score)}
            </span>
          )}
          <div className="history-actions">
            {p.status === 'completed' ? (
              <Link className="btn ghost" to={`/results/${p.job_id}`}>
                Open
              </Link>
            ) : (
              <span className="badge amber">{p.status}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}