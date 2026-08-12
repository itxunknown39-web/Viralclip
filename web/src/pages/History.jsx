import { useEffect, useState } from 'react'
import { getHistory } from '../api/client.js'
import HistoryList from '../components/HistoryList.jsx'

export default function History() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getHistory()
      .then((d) => setProjects(d.projects || []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="page">
      <div className="page-head">
        <h1>History</h1>
      </div>
      {error && <p className="text-error">{error}</p>}
      {loading ? <p className="empty">Loading…</p> : <HistoryList projects={projects} />}
    </div>
  )
}