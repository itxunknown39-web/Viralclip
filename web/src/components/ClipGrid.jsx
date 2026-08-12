import ClipCard from './ClipCard.jsx'

export default function ClipGrid({ clips, sourceUrl, jobId }) {
  if (!clips || clips.length === 0) {
    return <p className="empty">No clips yet. Run an analysis first.</p>
  }
  return (
    <div className="clip-grid">
      {clips.map((clip) => (
        <ClipCard key={clip.candidate_id} clip={clip} sourceUrl={sourceUrl} jobId={jobId} />
      ))}
    </div>
  )
}