import { useRef, useState } from 'react'
import { useVideoPreview } from '../hooks/useVideoPreview.js'

export default function VideoPreview({ src, start, end, active = true }) {
  const [playing, setPlaying] = useState(false)
  const [muted, setMuted] = useState(true)
  const { videoRef } = useVideoPreview({
    start,
    end,
    active,
    onEnded: () => setPlaying(false),
  })

  function togglePlay() {
    const video = videoRef.current
    if (!video) return
    if (video.paused) {
      if (video.currentTime < start || video.currentTime >= end) {
        video.currentTime = start
      }
      video.play()
      setPlaying(true)
    } else {
      video.pause()
      setPlaying(false)
    }
  }

  function handleTimeUpdate() {
    const video = videoRef.current
    if (video && video.currentTime >= end && !video.paused) {
      video.pause()
      setPlaying(false)
    }
  }

  return (
    <div className="preview-player">
      <video
        ref={videoRef}
        src={src}
        muted={muted}
        playsInline
        preload="auto"
        onTimeUpdate={handleTimeUpdate}
        onClick={togglePlay}
      />
      <div className="preview-controls">
        <button className="btn small" onClick={togglePlay}>
          {playing ? '❚❚ Pause' : '▶ Preview'}
        </button>
        <button
          className="btn small ghost"
          onClick={() => setMuted((m) => !m)}
        >
          {muted ? '🔇 Muted' : '🔊 Sound'}
        </button>
      </div>
    </div>
  )
}