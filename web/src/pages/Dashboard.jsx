import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getHistory } from '../api/client.js'
import HistoryList from '../components/HistoryList.jsx'
import { formatScore } from '../utils/formatScore.js'

export default function Dashboard() {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getHistory()
      .then((d) => setHistory(d.projects || []))
      .catch(() => setHistory([]))
      .finally(() => setLoading(false))
  }, [])

  const videos = history.length
  const clipsFound = history.reduce((n, p) => n + (p.clip_count || 0), 0)
  const clipsGenerated = history.reduce((n, p) => n + (p.generated_clips || 0), 0)
  const best = Math.max(0, ...history.map((p) => Number(p.best_score) || 0))
  const recent = history.slice(0, 5)

  return (
    <div className="page">
      <div className="page-head">
        <h1>Welcome back</h1>
        <Link to="/create" className="btn primary">
          ＋ New Project
        </Link>
      </div>

      <div className="stats-row">
        <div className="card stat-card">
          <span className="stat-value">{videos}</span>
          <span className="stat-label">Videos Analyzed</span>
        </div>
        <div className="card stat-card">
          <span className="stat-value">{clipsFound}</span>
          <span className="stat-label">Clips Found</span>
        </div>
        <div className="card stat-card">
          <span className="stat-value">{clipsGenerated}</span>
          <span className="stat-label">Clips Generated</span>
        </div>
        <div className="card stat-card">
          <span className="stat-value">{formatScore(best)}</span>
          <span className="stat-label">Best Viral Score</span>
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">Recent Projects</h2>
        {loading ? <p className="empty">Loading…</p> : <HistoryList projects={recent} />}
      </div>
    </div>
  )
}