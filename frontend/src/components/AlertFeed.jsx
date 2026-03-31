import React from 'react'

export default function AlertFeed({ alerts }) {
  const activeAlerts = alerts.filter(a => a.severity !== 'resolved')
  const resolvedAlerts = alerts.filter(a => a.severity === 'resolved')
  const allAlerts = [...activeAlerts, ...resolvedAlerts]

  const formatTime = (ts) => {
    if (!ts) return ''
    const d = new Date(ts)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const timeAgo = (ts) => {
    if (!ts) return ''
    const mins = Math.round((Date.now() - new Date(ts)) / 60000)
    if (mins < 1) return 'just now'
    if (mins < 60) return `${mins}m ago`
    return `${Math.round(mins / 60)}h ago`
  }

  return (
    <div className="alert-feed">
      <div className="alert-feed-header">
        <h2>
          🔔 Live Alerts
          {activeAlerts.length > 0 && (
            <span className="alert-count">{activeAlerts.length}</span>
          )}
        </h2>
      </div>
      <div className="alert-list">
        {allAlerts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)', fontSize: '14px' }}>
            <div style={{ fontSize: '32px', marginBottom: '12px' }}>✅</div>
            All wards operating normally
          </div>
        ) : (
          allAlerts.map((alert, i) => (
            <div key={alert.id || i}
              className={`alert-card ${alert.severity === 'critical' ? 'critical' : ''} ${alert.severity === 'resolved' ? 'resolved' : ''}`}
              id={`alert-${alert.id || i}`}
            >
              <div className="alert-card-header">
                <span className="ward-name">{alert.ward_name}</span>
                <span className="time">{timeAgo(alert.created_at)}</span>
              </div>
              {alert.occupancy_percent && (
                <div className="occupancy" style={{
                  color: alert.occupancy_percent >= 95 ? '#ef4444' : '#f97316'
                }}>
                  {alert.occupancy_percent}% occupancy
                </div>
              )}
              {alert.llm_explanation && (
                <div className="explanation">{alert.llm_explanation}</div>
              )}
              {alert.message && !alert.llm_explanation && (
                <div className="explanation">{alert.message}</div>
              )}
              {alert.consecutive_hours && (
                <div className="breach-duration">
                  ⏱ Breach duration: {alert.consecutive_hours}h
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
