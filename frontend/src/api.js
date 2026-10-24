const BASE = import.meta.env.VITE_API_URL || ''

async function get(path, params) {
  const res = await fetch(`${BASE}${path}?${new URLSearchParams(params)}`)
  if (!res.ok) {
    let msg = `API error ${res.status}`
    try { msg = (await res.json()).detail || msg } catch { /* ignore */ }
    throw new Error(msg)
  }
  return res.json()
}

const range = (from, to, cutoff) => ({ from, to, cutoff })
export const getDecision = (day, cutoff) => get('/api/decision', { day, cutoff })
export const getCompare = (f, t, c) => get('/api/compare', range(f, t, c))
export const getMetrics = (f, t, c) => get('/api/metrics', range(f, t, c))
export const getByHour = (f, t, c) => get('/api/metrics/by-hour', range(f, t, c))
export const getByHorizon = (f, t, c) => get('/api/metrics/by-horizon', range(f, t, c))
export const getByDay = (f, t, c) => get('/api/metrics/by-day', range(f, t, c))