import { useState } from 'react'
import { analyzeVideo, getResults } from '../api/client.js'

export function useAnalysis() {
  const [jobId, setJobId] = useState(null)
  const [state, setState] = useState({
    status: 'idle', // idle | submitting | analyzing | done | error
    error: null,
  })

  async function start(payload) {
    setState({ status: 'submitting', error: null })
    try {
      const { job_id } = await analyzeVideo(payload)
      setJobId(job_id)
      setState({ status: 'analyzing', error: null })
      return job_id
    } catch (err) {
      setState({ status: 'error', error: err.message })
      throw err
    }
  }

  async function loadResults(jid) {
    const data = await getResults(jid)
    setState({ status: 'done', error: null })
    return data
  }

  function reset() {
    setJobId(null)
    setState({ status: 'idle', error: null })
  }

  return { jobId, state, start, loadResults, reset }
}