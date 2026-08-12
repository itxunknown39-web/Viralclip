import { useEffect, useRef } from 'react'

/**
 * Drives an HTML5 <video> to preview a [start, end] window.
 * Returns refs and controls for attaching to a video element.
 */
export function useVideoPreview({ start, end, active, onEnded }) {
  const videoRef = useRef(null)
  const timerRef = useRef(null)

  useEffect(() => {
    if (!active || !videoRef.current) return undefined
    const video = videoRef.current
    video.currentTime = start

    const tick = () => {
      if (video.currentTime >= end) {
        video.pause()
        if (onEnded) onEnded()
      } else {
        timerRef.current = requestAnimationFrame(tick)
      }
    }
    timerRef.current = requestAnimationFrame(tick)
    return () => {
      if (timerRef.current) cancelAnimationFrame(timerRef.current)
    }
  }, [active, start, end, onEnded])

  return { videoRef }
}