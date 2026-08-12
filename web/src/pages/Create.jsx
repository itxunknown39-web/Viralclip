import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import VideoInput from '../components/VideoInput.jsx'
import AnalysisProgress from '../components/AnalysisProgress.jsx'
import ErrorAlert from '../components/ErrorAlert.jsx'
import { useAnalysis } from '../hooks/useAnalysis.js'
import { useProgress } from '../hooks/useProgress.js'

export default function Create() {
  const navigate = useNavigate()
  const { state, start, reset } = useAnalysis()
  const [jobId, setJobId] = useState(null)
  const progress = useProgress(jobId)

  async function handleAnalyze(payload) {
    reset()
    try {
      const jid = await start({
        url: payload.url,
        clip_count: payload.clip_count,
        min_duration: payload.min_duration,
        max_duration: payload.max_duration,
      })
      setJobId(jid)
    } catch {
      /* handled by state */
    }
  }

  const analyzing = state.status === 'analyzing' && jobId
  const failed = progress.status === 'failed'
  const done = progress.status === 'completed'

  if (done && jobId) {
    navigate(`/results/${jobId}`, { replace: true })
  }

  return (
    <div className="page narrow">
      {!analyzing && (
        <VideoInput onAnalyze={handleAnalyze} busy={state.status === 'submitting'} />
      )}

      <ErrorAlert
        error={state.status === 'error' ? state.error : failed ? progress.error : null}
        onDismiss={failed || state.status === 'error' ? () => { reset(); setJobId(null) } : undefined}
      />

      {analyzing && <AnalysisProgress {...progress} />}
    </div>
  )
}