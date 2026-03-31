import React from 'react'
import WardCard from './WardCard'

export default function WardGrid({ wards, onSelectWard }) {
  return (
    <div className="ward-grid">
      {wards.map(ward => (
        <WardCard
          key={ward.ward_id}
          ward={ward}
          onClick={() => onSelectWard(ward)}
        />
      ))}
    </div>
  )
}
