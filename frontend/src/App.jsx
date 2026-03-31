import React, { useState, useEffect, useCallback, useRef } from 'react'
import WardGrid from './components/WardGrid'
import AlertFeed from './components/AlertFeed'
import WardDetailModal from './components/WardDetailModal'
import AnomalyBanner from './components/AnomalyBanner'

// Demo data for standalone mode (when API is not running)
const DEMO_WARDS = [
  { ward_id:'W-001', ward_name:'ICU East', occupied_beds:16, total_beds:20, occupancy_percent:80.0, status:'elevated', trend:'rising' },
  { ward_id:'W-002', ward_name:'ICU West', occupied_beds:18, total_beds:20, occupancy_percent:90.0, status:'warning', trend:'rising' },
  { ward_id:'W-003', ward_name:'General A', occupied_beds:24, total_beds:40, occupancy_percent:60.0, status:'normal', trend:'stable' },
  { ward_id:'W-004', ward_name:'General B', occupied_beds:30, total_beds:40, occupancy_percent:75.0, status:'elevated', trend:'rising' },
  { ward_id:'W-005', ward_name:'Pediatrics', occupied_beds:10, total_beds:25, occupancy_percent:40.0, status:'normal', trend:'falling' },
  { ward_id:'W-006', ward_name:'Emergency', occupied_beds:28, total_beds:30, occupancy_percent:93.3, status:'critical', trend:'rising' },
  { ward_id:'W-007', ward_name:'Oncology', occupied_beds:9, total_beds:15, occupancy_percent:60.0, status:'normal', trend:'stable' },
]

const DEMO_ALERTS = [
  { id:1, alert_type:'sla_breach', ward_id:'W-006', ward_name:'Emergency', severity:'critical',
    occupancy_percent:93.3, message:'Emergency at 93.3% for 3h', created_at: new Date().toISOString(),
    llm_explanation:'Emergency ward admission rate is 2.4x the 7-day baseline. This appears consistent with a local multi-vehicle accident bringing 8 trauma cases simultaneously. Based on historical discharge patterns, expect resolution within 3-4 hours. Confidence: high.' },
  { id:2, alert_type:'sla_breach', ward_id:'W-002', ward_name:'ICU West', severity:'warning',
    occupancy_percent:90.0, message:'ICU West at 90% for 2h', created_at: new Date(Date.now()-3600000).toISOString(),
    llm_explanation:'ICU West occupancy has risen gradually over 6 hours, primarily from post-surgical admissions. This is 12% above the typical Tuesday baseline. Expected to normalize within 2-4 hours as scheduled discharges proceed. Confidence: medium.' },
]

const DEMO_ANOMALIES = [
  { ward_id:'W-006', ward_name:'Emergency', z_score:3.2, is_anomaly:true, baseline_mean:4.5, current_count:11 },
]

const API_BASE = 'http://localhost:8000'

export default function App() {
  const [wards, setWards] = useState(DEMO_WARDS)
  const [alerts, setAlerts] = useState(DEMO_ALERTS)
  const [anomalies, setAnomalies] = useState(DEMO_ANOMALIES)
  const [selectedWard, setSelectedWard] = useState(null)
  const [wsConnected, setWsConnected] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(new Date())
  const [isLive, setIsLive] = useState(false)
  const wsRef = useRef(null)

  // Fetch data from API
  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/dashboard/summary`)
      if (!res.ok) throw new Error('API unavailable')
      const data = await res.json()
      if (data.wards?.length) setWards(data.wards)
      if (data.active_breaches?.length) {
        setAlerts(data.active_breaches.map(b => ({
          ...b, alert_type: 'sla_breach',
          severity: b.current_occupancy_percent >= 95 ? 'critical' : 'warning',
          occupancy_percent: b.current_occupancy_percent,
          message: `${b.ward_name}: ${b.consecutive_hours}h above 85%`,
          created_at: b.breach_start_time,
        })))
      }
      if (data.anomalies?.length) setAnomalies(data.anomalies)
      setLastUpdated(new Date())
      setIsLive(true)
    } catch {
      setIsLive(false)
      // Simulate live updates with demo data
      simulateUpdates()
    }
  }, [])

  // Simulate live updates for demo mode
  const simulateUpdates = useCallback(() => {
    setWards(prev => prev.map(w => {
      const delta = (Math.random() - 0.48) * 3
      const newOcc = Math.max(5, Math.min(100, w.occupancy_percent + delta))
      const newBeds = Math.round((newOcc / 100) * w.total_beds)
      const status = newOcc >= 95 ? 'critical' : newOcc >= 85 ? 'warning' : newOcc >= 70 ? 'elevated' : 'normal'
      const trend = delta > 0.5 ? 'rising' : delta < -0.5 ? 'falling' : 'stable'
      return { ...w, occupancy_percent: Math.round(newOcc * 10) / 10, occupied_beds: newBeds, status, trend }
    }))
    setLastUpdated(new Date())
  }, [])

  // Connect WebSocket
  useEffect(() => {
    const connectWs = () => {
      try {
        const ws = new WebSocket('ws://localhost:8000/ws/alerts')
        ws.onopen = () => { setWsConnected(true) }
        ws.onmessage = (e) => {
          const msg = JSON.parse(e.data)
          if (msg.type === 'alert') {
            setAlerts(prev => [msg.data, ...prev].slice(0, 50))
          }
        }
        ws.onclose = () => { setWsConnected(false); setTimeout(connectWs, 5000) }
        ws.onerror = () => { setWsConnected(false) }
        wsRef.current = ws
      } catch { setWsConnected(false) }
    }
    connectWs()
    return () => { wsRef.current?.close() }
  }, [])

  // Poll data
  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [fetchData])

  const activeAnomalies = anomalies.filter(a => a.is_anomaly)
  const wardsInBreach = wards.filter(w => w.status === 'warning' || w.status === 'critical')

  return (
    <div className="app">
      <nav className="navbar">
        <div className="navbar-brand">
          <div className="logo">H</div>
          <div>
            <h1>Hospital Bed Occupancy Monitor</h1>
          </div>
        </div>
        <div className="navbar-status">
          <span>
            <span className={`connection-dot ${wsConnected || !isLive ? 'connected' : 'disconnected'}`} />
            {isLive ? 'Live' : 'Demo Mode'}
          </span>
          <span>Updated: {lastUpdated.toLocaleTimeString()}</span>
        </div>
      </nav>

      {activeAnomalies.length > 0 && <AnomalyBanner anomalies={activeAnomalies} />}

      <div style={{ padding: '24px 32px 0' }}>
        <div className="summary-bar">
          <div className="summary-card">
            <div className="icon-box blue">🏥</div>
            <div className="info">
              <div className="label">Total Wards</div>
              <div className="value">{wards.length}</div>
            </div>
          </div>
          <div className="summary-card">
            <div className="icon-box green">🛏️</div>
            <div className="info">
              <div className="label">Overall Occupancy</div>
              <div className="value">
                {Math.round(wards.reduce((s, w) => s + w.occupied_beds, 0) / wards.reduce((s, w) => s + w.total_beds, 0) * 100)}%
              </div>
            </div>
          </div>
          <div className="summary-card">
            <div className="icon-box orange">⚠️</div>
            <div className="info">
              <div className="label">Wards in Breach</div>
              <div className="value">{wardsInBreach.length}</div>
            </div>
          </div>
          <div className="summary-card">
            <div className="icon-box red">🔍</div>
            <div className="info">
              <div className="label">Anomalies</div>
              <div className="value">{activeAnomalies.length}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="main-content">
        <div>
          <div className="section-header">
            <h2>🏥 Ward Occupancy</h2>
          </div>
          <WardGrid wards={wards} onSelectWard={setSelectedWard} />
        </div>
        <AlertFeed alerts={alerts} />
      </div>

      {selectedWard && (
        <WardDetailModal
          ward={selectedWard}
          onClose={() => setSelectedWard(null)}
          apiBase={API_BASE}
        />
      )}
    </div>
  )
}
