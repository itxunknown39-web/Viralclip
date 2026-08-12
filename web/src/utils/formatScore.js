export function scoreColor(score) {
  if (score >= 90) return 'green'
  if (score >= 75) return 'amber'
  return 'gray'
}

export function formatScore(score) {
  return Math.round(Number(score) || 0)
}