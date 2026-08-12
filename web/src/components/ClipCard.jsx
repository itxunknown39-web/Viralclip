import { useMemo, useState } from 'react'
import VideoPreview from './VideoPreview.jsx'
import ScoreBreakdown from './ScoreBreakdown.jsx'
import GeneratePanel from './GeneratePanel.jsx'
import { formatTime } from '../utils/formatTime.js'
import { formatScore, scoreColor } from '../utils/formatScore.js'
import { clipDownloadUrl } from '../api/client.js'

export default function ClipCard({ clip, sourceUrl, jobId }) {
  const [genId, setGenId] = useState(null)
  const color = scoreColor(clip.viral_score)
  const previewSrc = sourceUrl

  return (
    <article className="card clip-card">
      <div className="clip-head">
        <span className="clip-rank">#{clip.rank}</span>
        <span className={`virality ${color}`}>VIRAL {formatScore(clip.viral_score)}</span>
      </div>

      <VideoPreview src={previewSrc} start={clip.start} end={clip.end} />

      <div className="clip-body">
        <h3 className="clip-title">{clip.title || `Viral moment ${clip.rank}`}</h3>
        <div className="clip-time">
          {formatTime(clip.start)} — {formatTime(clip.end)} · {Math.round(clip.duration)}s
        </div>
        {clip.hook && <p className="clip-hook">“{clip.hook}”</p>}
        {clip.reason && <p className="clip-reason">{clip.reason}</p>}
        <ScoreBreakdown scores={clip.scores} />
      </div>

      <GeneratePanel
        candidateId={clip.candidate_id}
        jobId={jobId}
        onJobReady={(id) => setGenId(id)}
      />

      {genId && (
        <div className="clip-download">
          <a className="btn primary" href={clipDownloadUrl(genId)}>
            Download MP4
          </a>
        </div>
      )}
    </article>
  )
}