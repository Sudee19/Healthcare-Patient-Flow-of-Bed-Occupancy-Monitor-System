import React, { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Area, ComposedChart } from 'recharts'

export default function WardDetailModal({ ward, onClose, apiBase }) {
  const [history, setHistory] = useState([])
  const [baseline, setBaseline] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const [histRes, baseRes] = await Promise.all([
          fetch(`${apiBase}/wards/${ward.ward_id}/history?hours=24`),
          fetch(`${apiBase}/wards/${ward.ward_id}/baseline`),
        ])
        if (histRes.ok) {
          const h = await histRes.json()
          setHistory(h.map(r => ({
            ...r,
            hour: new Date(r.snapshot_hour).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            pct: r.occupancy_percent,
          })))
        }
        if (baseRes.ok) {
          const b = await baseRes.json()
          setBaseline(b)
        }
      } catch {
        // Generate demo data
        generateDemoData()
      }
      setLoading(false)
    }

    const generateDemoData = () => {
      const now = new Date()
      const data = []
      for (let i = 23; i >= 0; i--) {
        const t = new Date(now - i * 3600000)
        const hour = t.getHours()
        const baseOcc = 55 + Math.sin(hour / 24 * Math.PI * 2) * 20
        const noise = (Math.random() - 0.5) * 15
        const pct = Math.max(10, Math.min(100, baseOcc + noise +
          (ward.ward_id === 'W-006' ? 20 : 0) +
          (ward.ward_id === 'W-002' ? 15 : 0)))
        data.push({
          hour: t.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          pct: Math.round(pct * 10) / 10,
          baseline: Math.round(baseOcc * 10) / 10,
          baselineUpper: Math.round((baseOcc + 10) * 10) / 10,
          baselineLower: Math.round((baseOcc - 10) * 10) / 10,
        })
      }
      setHistory(data)
    }

    fetchDetails()
  }, [ward, apiBase])

  const statusColor = {
    normal: '#10b981', elevated: '#f59e0b',
    warning: '#f97316', critical: '#ef4444'
  }[ward.status] || '#10b981'

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null
    return (
      <div style={{
        background: '#1a2236', border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: '8px', padding: '10px 14px', fontSize: '12px',
      }}>
        <div style={{ color: '#8892a8', marginBottom: '4px' }}>{label}</div>
        {payload.map((p, i) => (
          <div key={i} style={{ color: p.color, fontWeight: 600 }}>
            {p.name}: {p.value}%
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>
            <span style={{ color: statusColor, marginRight: '8px' }}>●</span>
            {ward.ward_name}
            <span style={{ fontSize: '14px', color: '#8892a8', marginLeft: '12px', fontWeight: 400 }}>
              {ward.ward_id}
            </span>
          </h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {/* Stats Grid */}
          <div className="modal-stats">
            <div className="modal-stat-card">
              <div className="label">Occupancy</div>
              <div className="value" style={{ color: statusColor }}>
                {Math.round(ward.occupancy_percent)}%
              </div>
            </div>
            <div className="modal-stat-card">
              <div className="label">Beds Used</div>
              <div className="value">{ward.occupied_beds}/{ward.total_beds}</div>
            </div>
            <div className="modal-stat-card">
              <div className="label">Available</div>
              <div className="value" style={{ color: '#10b981' }}>
                {ward.total_beds - ward.occupied_beds}
              </div>
            </div>
            <div className="modal-stat-card">
              <div className="label">Trend</div>
              <div className="value">
                {ward.trend === 'rising' ? '📈' : ward.trend === 'falling' ? '📉' : '➡️'}
                {' '}{ward.trend}
              </div>
            </div>
          </div>

          {/* 24-Hour Trend Chart */}
          <div className="chart-container">
            <h3>24-Hour Occupancy Trend</h3>
            {loading ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#8892a8' }}>
                Loading chart data...
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={history} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="occupancyGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={statusColor} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={statusColor} stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="baselineGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.1} />
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="hour" tick={{ fill: '#5a6478', fontSize: 11 }}
                    axisLine={{ stroke: 'rgba(255,255,255,0.06)' }} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fill: '#5a6478', fontSize: 11 }}
                    axisLine={{ stroke: 'rgba(255,255,255,0.06)' }} tickLine={false}
                    tickFormatter={v => `${v}%`} />
                  <Tooltip content={<CustomTooltip />} />

                  {/* SLA Threshold Line */}
                  <ReferenceLine y={85} stroke="#ef4444" strokeDasharray="8 4"
                    strokeWidth={1.5} label={{
                      value: 'SLA 85%', position: 'right',
                      style: { fill: '#ef4444', fontSize: 10 }
                    }} />

                  {/* Baseline band */}
                  {history[0]?.baselineUpper && (
                    <Area type="monotone" dataKey="baselineUpper" stackId="baseline"
                      fill="url(#baselineGrad)" stroke="none" />
                  )}

                  {/* Baseline line */}
                  {history[0]?.baseline && (
                    <Line type="monotone" dataKey="baseline" name="7-Day Baseline"
                      stroke="#8b5cf6" strokeWidth={1.5} strokeDasharray="5 5"
                      dot={false} />
                  )}

                  {/* Occupancy area + line */}
                  <Area type="monotone" dataKey="pct" name="Occupancy"
                    fill="url(#occupancyGrad)" stroke={statusColor}
                    strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
                </ComposedChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
