"""
LLM Context Assembler
Builds structured context JSON from Gold layer data for LLM prompts.
"""
import os, sqlite3, json, logging
from datetime import datetime, timedelta

logger = logging.getLogger("llm.context")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "hospital.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def assemble_breach_context(ward_id: str, breach_id: int = None) -> dict:
    """Assemble full context for LLM explanation of a breach."""
    conn = get_conn()
    context = {}

    # Current occupancy
    row = conn.execute(
        "SELECT * FROM ward_occupancy_current WHERE ward_id=?", (ward_id,)).fetchone()
    if row:
        context['current'] = {
            'ward_name': row['ward_name'],
            'occupied_beds': row['occupied_beds'],
            'total_beds': row['total_beds'],
            'occupancy_percent': row['occupancy_percent'],
            'status': row['status'],
            'trend': row['trend'],
        }

    # Breach info
    if breach_id:
        br = conn.execute("SELECT * FROM sla_breaches WHERE id=?", (breach_id,)).fetchone()
        if br:
            context['breach'] = {
                'start_time': br['breach_start_time'],
                'consecutive_hours': br['consecutive_hours'],
                'peak_occupancy': br['peak_occupancy_percent'],
            }

    # Baseline (same hour of day)
    hod = datetime.now().hour
    bl = conn.execute(
        "SELECT * FROM ward_baseline WHERE ward_id=? AND hour_of_day=?",
        (ward_id, hod)).fetchone()
    if bl:
        context['baseline'] = {
            'hour_of_day': hod,
            'avg_occupancy': bl['baseline_avg_occupancy'],
            'std_occupancy': bl['baseline_std_occupancy'],
            'sample_count': bl['sample_count'],
        }

    # Anomaly status
    anom = conn.execute("""
        SELECT * FROM anomaly_flags WHERE ward_id=?
        ORDER BY detection_time DESC LIMIT 1""", (ward_id,)).fetchone()
    if anom:
        context['anomaly'] = {
            'z_score': anom['z_score'],
            'is_anomaly': bool(anom['is_anomaly']),
            'baseline_mean': anom['baseline_mean'],
            'current_count': anom['current_count'],
        }

    # Recent 6-hour trend
    cutoff = (datetime.now() - timedelta(hours=6)).isoformat()
    trend_rows = conn.execute("""
        SELECT snapshot_hour, occupancy_percent FROM ward_occupancy_hourly
        WHERE ward_id=? AND snapshot_hour>=? ORDER BY snapshot_hour""",
        (ward_id, cutoff)).fetchall()
    context['recent_trend'] = [
        {'hour': r['snapshot_hour'], 'pct': r['occupancy_percent']}
        for r in trend_rows
    ]

    # Admission breakdown (recent)
    admits = conn.execute("""
        SELECT COUNT(*) as total FROM ward_occupancy_hourly
        WHERE ward_id=? AND snapshot_hour>=?""", (ward_id, cutoff)).fetchone()
    context['recent_admits'] = admits['total'] if admits else 0

    conn.close()
    context['assembled_at'] = datetime.now().isoformat()
    context['ward_id'] = ward_id
    return context
