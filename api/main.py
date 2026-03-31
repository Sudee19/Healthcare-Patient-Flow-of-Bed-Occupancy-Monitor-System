"""
FastAPI Main Application
REST endpoints + WebSocket for real-time alerts.
"""
import os, sys, sqlite3, json, asyncio, logging
from datetime import datetime, timedelta
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from api.models import WardStatus, WardHourly, WardBaseline, SLABreach, AnomalyFlag, AlertEvent

logger = logging.getLogger("api")
DB_PATH = os.path.join(BASE_DIR, "data", "hospital.db")

# ─── WebSocket Manager ──────────────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)

manager = ConnectionManager()

# ─── Background alert watcher ───────────────────────────────────────────────
async def alert_watcher():
    """Watch for new alerts and broadcast via WebSocket."""
    last_id = 0
    while True:
        try:
            conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM alert_history WHERE id > ? ORDER BY id", (last_id,)
            ).fetchall()
            conn.close()
            for r in rows:
                last_id = r['id']
                await manager.broadcast({
                    'type': 'alert',
                    'data': dict(r),
                })
        except: pass
        await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Init DB
    from db import init_database
    init_database()
    task = asyncio.create_task(alert_watcher())
    yield
    task.cancel()

# ─── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Hospital Bed Occupancy Monitor API",
    description="Real-time ward occupancy, SLA breach tracking, and anomaly detection",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"])

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ─── REST Endpoints ──────────────────────────────────────────────────────────

@app.get("/wards", response_model=List[WardStatus], tags=["Wards"])
def list_wards():
    """List all wards with current occupancy % and status."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM ward_occupancy_current ORDER BY ward_id").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/wards/{ward_id}", response_model=WardStatus, tags=["Wards"])
def get_ward(ward_id: str):
    """Get single ward status."""
    conn = get_db()
    row = conn.execute("SELECT * FROM ward_occupancy_current WHERE ward_id=?", (ward_id,)).fetchone()
    conn.close()
    if not row: raise HTTPException(404, "Ward not found")
    return dict(row)

@app.get("/wards/{ward_id}/history", response_model=List[WardHourly], tags=["Wards"])
def get_ward_history(ward_id: str, hours: int = Query(24, ge=1, le=168)):
    """Hourly occupancy for past N hours."""
    conn = get_db()
    cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
    rows = conn.execute("""SELECT * FROM ward_occupancy_hourly
        WHERE ward_id=? AND snapshot_hour>=? ORDER BY snapshot_hour""",
        (ward_id, cutoff)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/wards/{ward_id}/baseline", response_model=List[WardBaseline], tags=["Wards"])
def get_ward_baseline(ward_id: str):
    """7-day average baseline for a ward."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM ward_baseline WHERE ward_id=? ORDER BY hour_of_day",
        (ward_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/alerts/active", response_model=List[SLABreach], tags=["Alerts"])
def get_active_alerts():
    """All current SLA breaches with LLM explanations."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM sla_breaches WHERE status='active' ORDER BY breach_start_time DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/alerts/history", response_model=List[SLABreach], tags=["Alerts"])
def get_alert_history(days: int = Query(7, ge=1, le=30)):
    """Resolved breaches from past N days."""
    conn = get_db()
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    rows = conn.execute("""SELECT * FROM sla_breaches
        WHERE status='resolved' AND resolved_at>=? ORDER BY resolved_at DESC""",
        (cutoff,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/anomalies", response_model=List[AnomalyFlag], tags=["Anomalies"])
def get_anomalies(active_only: bool = Query(False)):
    """Current z-score flags across all wards."""
    conn = get_db()
    q = "SELECT * FROM anomaly_flags"
    if active_only: q += " WHERE is_anomaly=1"
    q += " ORDER BY detection_time DESC LIMIT 100"
    rows = conn.execute(q).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/dashboard/summary", tags=["Dashboard"])
def dashboard_summary():
    """Combined summary for dashboard."""
    conn = get_db()
    wards = [dict(r) for r in conn.execute(
        "SELECT * FROM ward_occupancy_current ORDER BY ward_id").fetchall()]
    breaches = [dict(r) for r in conn.execute(
        "SELECT * FROM sla_breaches WHERE status='active'").fetchall()]
    anomalies = [dict(r) for r in conn.execute(
        "SELECT * FROM anomaly_flags WHERE is_anomaly=1 ORDER BY detection_time DESC LIMIT 10"
    ).fetchall()]
    recent_alerts = [dict(r) for r in conn.execute(
        "SELECT * FROM alert_history ORDER BY created_at DESC LIMIT 20").fetchall()]
    conn.close()
    return {
        'wards': wards,
        'active_breaches': breaches,
        'anomalies': anomalies,
        'recent_alerts': recent_alerts,
        'timestamp': datetime.now().isoformat(),
        'total_wards': len(wards),
        'wards_in_breach': len(breaches),
    }

# ─── WebSocket ───────────────────────────────────────────────────────────────

@app.websocket("/ws/alerts")
async def websocket_alerts(ws: WebSocket):
    """WebSocket for real-time alert streaming."""
    await manager.connect(ws)
    try:
        while True:
            # Heartbeat every 30 seconds
            await asyncio.sleep(30)
            try:
                await ws.send_json({"type": "heartbeat", "timestamp": datetime.now().isoformat()})
            except:
                break
    except WebSocketDisconnect:
        manager.disconnect(ws)

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
