import { useEffect, useRef, useState } from 'react'
import { subscribeToProgress } from '../api/client.js'

export function useProgress(jobId) {
  const [state, setState] = useState({
    stage: 'queued',
    progress: 0,
    message: 'Queued',
    status: 'queued',
  })
  const sourceRef = useRef(null)

  useEffect(() => {
    if (!jobId) return undefined
    const source = subscribeToProgress(jobId, (event) => {
      setState(event)
      if (event.status === 'completed' || event.status === 'failed') {
        source.close()
      }
    })
    sourceRef.current = source
    return () => source.close()
  }, [jobId])

  return state
}