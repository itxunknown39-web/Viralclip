import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import ClipGrid from '../components/ClipGrid.jsx'
import AnalysisProgress from '../components/AnalysisProgress.jsx'
import ErrorAlert from '../components/ErrorAlert.jsx'
import { getResults, retryAI } from '../api/client.js'
import { useProgress } from '../hooks/useProgress.js'

export default function Results() {
  const { jobId } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sort, setSort] = useState('score')

  const progress = useProgress(jobId)
  const inProgress = progress.status === 'queued' || progress.status === undefined

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const d = await getResults(jobId)
      setData(d)
      if (d.status === 'failed') {
        setError(d.error || 'Analysis failed')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [jobId])

  useEffect(() => {
    load()
    const interval = setInterval(load, 4000)
    return () => clearInterval(interval)
  }, [load])

  async function handleRetryAI() {
    try {
      await retryAI(jobId)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  const clips = useSortedClips(data?.results, sort)

  if (loading && !data) {
    return (
      <div className="page">
        <AnalysisProgress {...progress} />
      </div>
    )
  }

  const sortable = [...(data?.results || [])]
  const showCount = Math.min(sortable.length, 10)

  return (
    <div className="page">
      <div className="page-head">
        <h1>Viral Moments</h1>
        <span className="muted">{clips.length} clips found</span>
      </div>

      <ErrorAlert error={error} onRetry={handleRetryAI} onDismiss={() => setError(null)} />

      {clips.length > 0 && (
        <div className="results-controls">
          <label className="field inline">
            <span>Sort</span>
            <select className="input" value={sort} onChange={(e) => setSort(e.target.value)}>
              <option value="score">Viral Score</option>
              <option value="duration">Duration</option>
              <option value="timestamp">Timestamp</option>
            </select>
          </label>
          <span className="muted">Showing top {Math.min(clips.length, sortable.length)}</span>
        </div>
      )}

      <ClipGrid
        clips={clips.slice(0, showCount)}
        sourceUrl={data?.source?.url}
        jobId={jobId}
      />
      {data?.status === 'failed' && (
        <div className="card">
          <p>
            {data.error || 'Analysis failed.'} The video and transcript are saved — you can
            retry just the AI step.
          </p>
          <button className="btn primary" onClick={handleRetryAI}>
            Retry AI Analysis
          </button>
        </div>
      )}
    </div>
  )
}

function useSortedClips(clips, sort) {
  if (!clips) return []
  const arr = [...clips]
  if (sort === 'score') arr.sort((a, b) => b.viral_score - a.viral_score)
  if (sort === 'duration') arr.sort((a, b) => b.duration - a.duration)
  if (sort === 'timestamp') arr.sort((a, b) => a.start - b.start)
  return arr
}