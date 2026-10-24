import { useEffect, useState } from 'react'
import { ComposedChart, Area, Line, XAxis, YAxis, Tooltip, Legend,
         CartesianGrid, ResponsiveContainer } from 'recharts'
import { getDecision } from '../api'
import { MIN_DAY, MAX_DAY, validDay, hhmm, dayHhmm } from '../config'

const mw = (v) => (v == null ? '-' : Math.round(v).toLocaleString())

export default function DecisionView({ cutoff }) {
  const [day, setDay] = useState('2026-01-15')
  const [hindsight, setHindsight] = useState(false)
  const [res, setRes] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!validDay(day)) {
      setError(`Choose a delivery day between ${MIN_DAY} and ${MAX_DAY}.`)
      setRes(null)
      return
    }
    setLoading(true); setError(null)
    getDecision(day, cutoff)
      .then(setRes)
      .catch((e) => { setError(e.message); setRes(null) })
      .finally(() => setLoading(false))
  }, [day, cutoff])

  const meta = res?.meta
  const p90 = meta?.band?.p90
  const rows = (res?.rows || []).map((r) => ({
    ...r,
    band: p90 != null ? [Math.max(0, r.forecast - p90), r.forecast + p90] : null,
  }))

  return (
    <div>
      <div className="controls">
        <label>Delivery day{' '}
          <input type="date" value={day} min={MIN_DAY} max={MAX_DAY}
                 onChange={(e) => setDay(e.target.value)} />
        </label>
        <label className="check">
          <input type="checkbox" checked={hindsight}
                 onChange={(e) => setHindsight(e.target.checked)} />
          Show hindsight (not known at decision time)
        </label>
      </div>

      {loading && <p>Loading… (the server may take up to a minute to wake up)</p>}
      {error && <p className="error">{error}</p>}

      {meta && (
        <>
          <p className="note">
            To buy power for <b>{meta.deliveryDay}</b>, the decision is made at{' '}
            <b>{meta.decisionTimeLocal}</b>. The forecast shown is the latest WINDFOR
            forecast for each half-hour published at or before that time
            (published between {dayHhmm(meta.firstPublish)} and {dayHhmm(meta.lastPublish)} UTC,
            average lead time {meta.meanHorizonH?.toFixed(0)} h).
          </p>

          {meta.points < meta.expectedPoints && (
            <p className="error">
              Only {meta.points} of {meta.expectedPoints} hourly forecasts are
              available at the decision time.
            </p>
          )}

          <div className="kpis">
            <div className="kpi"><div className="kpi-value">{mw(meta.expectedEnergyMwh)}</div>
              <div className="kpi-label">Expected wind energy (MWh)</div></div>
            <div className="kpi"><div className="kpi-value">{mw(meta.peakMw)}</div>
              <div className="kpi-label">Peak forecast (MW)</div></div>
            <div className="kpi"><div className="kpi-value">{mw(meta.minMw)}</div>
              <div className="kpi-label">Lowest forecast (MW)</div></div>
            <div className="kpi"><div className="kpi-value">{p90 != null ? `± ${mw(p90)}` : 'n/a'}</div>
              <div className="kpi-label">
                {p90 != null
                  ? `P90 error (history to ${meta.band.throughDay})`
                  : 'P90 error (needs ≥1 earlier day)'}
              </div></div>
          </div>

          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart data={rows}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="startTime" tickFormatter={hhmm} minTickGap={40} />
              <YAxis unit=" MW" width={85} />
              <Tooltip labelFormatter={dayHhmm} formatter={(v) => (Array.isArray(v)
                ? `${mw(v[0])} – ${mw(v[1])} MW` : `${mw(v)} MW`)} />
              <Legend />
              {p90 != null && <Area dataKey="band" name="Likely range (± P90 error)"
                                    stroke="none" fill="#ff7f0e" fillOpacity={0.18} />}
              <Line dataKey="forecast" name="Forecast at decision time" stroke="#ff7f0e"
                    strokeWidth={2} dot={false} />
              {hindsight && <Line dataKey="forecast_latest" name="Newest forecast (hindsight)"
                                  stroke="#2ca02c" strokeDasharray="5 4" dot={false} />}
              {hindsight && <Line dataKey="actual" name="Actual (hindsight)"
                                  stroke="#1f77b4" dot={false} />}
            </ComposedChart>
          </ResponsiveContainer>
          <p className="note">
            Times are Europe/London (= UTC in January). The shaded band uses only days whose
            actuals were already known at decision time, so it has no look-ahead.
          </p>
        </>
      )}
    </div>
  )
}