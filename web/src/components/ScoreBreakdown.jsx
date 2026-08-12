export default function ScoreBreakdown({ scores }) {
  const ROWS = [
    ['hook', 'Hook'],
    ['curiosity', 'Curiosity'],
    ['emotion', 'Emotion'],
    ['standalone', 'Standalone'],
    ['story', 'Story'],
    ['retention', 'Retention'],
    ['shareability', 'Shareability'],
  ]
  return (
    <div className="score-breakdown">
      {ROWS.map(([key, label]) => {
        const value = Math.round(Number(scores?.[key]) || 0)
        return (
          <div className="score-row" key={key}>
            <span className="score-label">{label}</span>
            <div className="score-track">
              <div
                className={`score-fill${value >= 8 ? ' strong' : ''}`}
                style={{ width: `${value * 10}%` }}
              />
            </div>
            <span className="score-value">{value}</span>
          </div>
        )
      })}
    </div>
  )
}