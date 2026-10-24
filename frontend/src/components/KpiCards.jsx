export default function KpiCards({ m }) {
  if (!m) return null
  const items = [
    ['MAE (MW)', m.mae.toFixed(0)],
    ['RMSE (MW)', m.rmse.toFixed(0)],
    ['Bias (MW)', m.bias.toFixed(0)],
    ['P90 abs error (MW)', m.p90_abs_error.toFixed(0)],
    ['nMAE (%)', m.nmae_pct.toFixed(1)],
  ]
  return (
    <div className="kpis">
      {items.map(([label, value]) => (
        <div className="kpi" key={label}>
          <div className="kpi-value">{value}</div>
          <div className="kpi-label">{label}</div>
        </div>
      ))}
    </div>
  )
}