import React from 'react'
import OccupancyGauge from './OccupancyGauge'

export default function WardCard({ ward, onClick }) {
  const { ward_id, ward_name, occupied_beds, total_beds, occupancy_percent, status, trend } = ward

  const trendArrow = trend === 'rising' ? '↑' : trend === 'falling' ? '↓' : '→'
  const trendClass = trend === 'rising' ? 'up' : trend === 'falling' ? 'down' : 'stable'

  const statusColor = {
    normal: '#10b981', elevated: '#f59e0b',
    warning: '#f97316', critical: '#ef4444'
  }[status] || '#10b981'

  return (
    <div className={`ward-card status-${status}`} onClick={onClick} id={`ward-${ward_id}`}>
      <div className="ward-card-header">
        <div>
          <h3>{ward_name}</h3>
          <div className="ward-id">{ward_id}</div>
        </div>
        <span className={`status-badge ${status}`}>{status}</span>
      </div>

      <div className="gauge-container">
        <OccupancyGauge percent={occupancy_percent} color={statusColor} />
        <div className="gauge-percent">
          {Math.round(occupancy_percent)}<span className="unit">%</span>
          <span className={`trend-arrow ${trendClass}`}>{trendArrow}</span>
        </div>
      </div>

      <div className="ward-stats">
        <div className="ward-stat">
          <span className="label">Beds</span>
          <span className="value">{occupied_beds}/{total_beds}</span>
        </div>
        <div className="ward-stat">
          <span className="label">Available</span>
          <span className="value">{total_beds - occupied_beds}</span>
        </div>
      </div>

      {(status === 'warning' || status === 'critical') && (
        <div className="breach-timer">
          🚨 SLA Breach Active — Above 85% threshold
        </div>
      )}
    </div>
  )
}
