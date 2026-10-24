import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid,
         ResponsiveContainer, ReferenceLine } from 'recharts'
import { getCompare, getMetrics, getByHour, getByHorizon, getByDay } from '../api'
import { MIN_DAY, MAX_DAY, validDay } from '../config'
import KpiCards from './KpiCards'
import CompareChart from './CompareChart'

function Bars({ title, data, xKey, note }) {
  return (
    <div className="card">
      <h3>{title}</h3>
      {note && <p className="note">{note}</p>}
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xKey} />
          <YAxis unit=" MW" width={80} />
          <Tooltip formatter={(v) => `${Math.round(v)} MW`} />
          <Legend />
          <ReferenceLine y={0} stroke="#888" />
          <Bar dataKey="mae" name="MAE" fill="#1f77b4" />
          <Bar dataKey="p90_abs_error" name="P90 abs error" fill="#9ecae1" />
          <Bar dataKey="bias" name="Bias (+ = over-forecast)" fill="#ff7f0e" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default function AccuracyView({ cutoff }) {
  const [from, setFrom] = useState('2026-01-02')
  const [to, setTo] = useState('2026-01-08')
  const [d, setD] = useState({ cmp: [], m: null, hour: [], hz: [], day: [] })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!validDay(from) || !validDay(to) || from > to) {
      setError(`Choose dates between ${MIN_DAY} and ${MAX_DAY}, with From on or before To.`)
      setD({ cmp: [], m: null, hour: [], hz: [], day: [] })
      return
    }
    setLoading(true); setError(null)
    Promise.all([getCompare(from, to, cutoff), getMetrics(from, to, cutoff),
                 getByHour(from, to, cutoff), getByHorizon(from, to, cutoff),
                 getByDay(from, to, cutoff)])
      .then(([cmp, m, hour, hz, day]) => setD({ cmp, m, hour, hz, day }))
      .catch((e) => { setError(e.message); setD({ cmp: [], m: null, hour: [], hz: [], day: [] }) })
      .finally(() => setLoading(false))
  }, [from, to, cutoff])

  return (
    <div>
      <div className="controls">
        <label>From (delivery day){' '}
          <input type="date" value={from} min={MIN_DAY} max={MAX_DAY}
                 onChange={(e) => setFrom(e.target.value)} /></label>
        <label>To{' '}
          <input type="date" value={to} min={MIN_DAY} max={MAX_DAY}
                 onChange={(e) => setTo(e.target.value)} /></label>
      </div>
      <p className="note">
        Each delivery day is judged on the forecast that was available at {cutoff} on the
        previous day, compared with what was actually generated. Error = forecast − actual.
      </p>

      {loading && <p>Loading… (the server may take up to a minute to wake up)</p>}
      {error && <p className="error">{error}</p>}

      <KpiCards m={d.m} />
      {d.cmp.length > 0 && <CompareChart data={d.cmp} />}
      {d.hour.length > 0 && (
        <>
          <Bars title="Error by hour of day" data={d.hour} xKey="key"
                note="When in the day is the forecast least reliable?" />
          <Bars title="Error by forecast lead time (hours before delivery)" data={d.hz} xKey="key"
                note="Longer lead time = older forecast." />
          <Bars title="Error by delivery day" data={d.day} xKey="key" />
        </>
      )}
    </div>
  )
}