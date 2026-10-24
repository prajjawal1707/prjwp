import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid,
         ResponsiveContainer } from 'recharts'

export default function CompareChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={380}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="startTime" tickFormatter={(t) => t.slice(5, 16).replace('T', ' ')}
               minTickGap={60} />
        <YAxis unit=" MW" width={80} />
        <Tooltip />
        <Legend />
        <Line dataKey="actual" stroke="#1f77b4" dot={false} name="Actual" />
        <Line dataKey="forecast" stroke="#ff7f0e" dot={false} name="Forecast (at cutoff)" />
      </LineChart>
    </ResponsiveContainer>
  )
}