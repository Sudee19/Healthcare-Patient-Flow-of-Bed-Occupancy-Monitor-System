import React from 'react'

export default function OccupancyGauge({ percent, color, size = 80 }) {
  const radius = 30
  const cx = size / 2
  const cy = 44
  const circumference = Math.PI * radius // semicircle
  const offset = circumference - (Math.min(percent, 100) / 100) * circumference

  return (
    <svg className="gauge-svg" viewBox={`0 0 ${size} 50`} width={size} height={50}>
      {/* Background track */}
      <path
        d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
        fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" strokeLinecap="round"
      />
      {/* Filled arc */}
      <path
        d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
        fill="none" stroke={color} strokeWidth="8" strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        style={{ transition: 'stroke-dashoffset 1s cubic-bezier(0.4,0,0.2,1)' }}
      />
    </svg>
  )
}
