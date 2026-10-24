const BASE = import.meta.env.VITE_API_URL || ''

async function get(path, params) {
  const res = await fetch(`${BASE}${path}?${new URLSearchParams(params)}`)
  if (!res.ok) throw new Error(`API error ${res.status}`)
  return res.json()
}

export const getCompare = (from, to, cutoff) => get('/api/compare', { from, to, cutoff })
export const getMetrics = (from, to, cutoff) => get('/api/metrics', { from, to, cutoff })