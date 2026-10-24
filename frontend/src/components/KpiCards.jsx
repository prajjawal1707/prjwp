export default function KpiCards({ m }) {
  if (!m || m.mae == null) return null
  const items = [
    ['MAE (MW)', m.mae.toFixed(0), 'typical size of the miss'],
    ['RMSE (MW)', m.rmse.toFixed(0), 'penalises big misses'],
    ['Bias (MW)', m.bias.toFixed(0), '+ = over-forecast wind'],
    ['P90 abs error (MW)', m.p90_abs_error.toFixed(0), '9 in 10 misses are smaller'],
    ['nMAE (%)', m.nmae_pct.toFixed(1), 'MAE ÷ mean actual'],
  ]
  return (
    <div className="kpis">
      {items.map(([label, value, hint]) => (
        <div className="kpi" key={label} title={hint}>
          <div className="kpi-value">{value}</div>
          <div className="kpi-label">{label}</div>
          <div className="kpi-hint">{hint}</div>
        </div>
      ))}
    </div>
  )
}