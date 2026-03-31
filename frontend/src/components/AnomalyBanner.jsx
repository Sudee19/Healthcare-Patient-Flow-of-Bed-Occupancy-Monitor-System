import React from 'react'

export default function AnomalyBanner({ anomalies }) {
  if (!anomalies || anomalies.length === 0) return null

  return (
    <div className="anomaly-banner" id="anomaly-banner">
      <span className="icon">⚠️</span>
      <strong>ANOMALY DETECTED:</strong>
      {anomalies.map((a, i) => (
        <span key={i}>
          {a.ward_name} (z-score: {a.z_score?.toFixed(1)}, admits: {a.current_count} vs baseline {a.baseline_mean?.toFixed(1)})
          {i < anomalies.length - 1 ? ' | ' : ''}
        </span>
      ))}
    </div>
  )
}
