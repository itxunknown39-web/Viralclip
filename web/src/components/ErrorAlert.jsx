export default function ErrorAlert({ error, onRetry, onDismiss }) {
  if (!error) return null
  return (
    <div className="alert error">
      <div className="alert-content">
        <strong>Something went wrong</strong>
        <p>{error}</p>
      </div>
      <div className="alert-actions">
        {onRetry && (
          <button className="btn ghost" onClick={onRetry}>
            Retry
          </button>
        )}
        {onDismiss && (
          <button className="btn ghost" onClick={onDismiss}>
            Dismiss
          </button>
        )}
      </div>
    </div>
  )
}