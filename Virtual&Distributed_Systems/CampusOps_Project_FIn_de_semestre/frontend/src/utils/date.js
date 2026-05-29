export function formatDate(raw) {
  if (!raw) return '—'
  const normalized = raw.endsWith('Z') ? raw : raw + 'Z'
  const d = new Date(normalized)
  if (isNaN(d.getTime())) return '—'
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

export function formatTime(raw) {
  if (!raw) return '—'
  return raw.slice(0, 5)
}
