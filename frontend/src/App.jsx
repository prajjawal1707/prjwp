import { useState, useEffect } from 'react'
import { getCompare, getMetrics } from './api'
import KpiCards from './components/KpiCards'
import CompareChart from './components/CompareChart'
import './App.css'

export default function App() {
  const [from, setFrom] = useState('2026-01-01')
  const [to, setTo] = useState('2026-01-07')
  const [cutoff, setCutoff] = useState('09:00')
  const [data, setData] = useState([])
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    Promise.all([getCompare(from, to, cutoff), getMetrics(from, to, cutoff)])
      .then(([d, m]) => { setData(d); setMetrics(m) })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [from, to, cutoff])

  return (
    <div className="app">
      <h1>UK Wind Forecast Monitor</h1>
      <p className="note">
        Forecast shown = latest WINDFOR forecast published before {cutoff} on the
        day before delivery (day-ahead decision time).
      </p>

      <div className="controls">
        <label>From <input type="date" value={from} min="2026-01-01" max="2026-01-31"
                           onChange={(e) => setFrom(e.target.value)} /></label>
        <label>To <input type="date" value={to} min="2026-01-01" max="2026-01-31"
                         onChange={(e) => setTo(e.target.value)} /></label>
        <label>Decision cutoff <input type="time" value={cutoff}
                                      onChange={(e) => setCutoff(e.target.value)} /></label>
      </div>

      {loading && <p>Loading…</p>}
      {error && <p className="error">{error}</p>}
      <KpiCards m={metrics} />
      <CompareChart data={data} />
    </div>
  )
}