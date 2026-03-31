"""
Airflow DAG 3: SLA Monitoring
Runs every 15 minutes. Detects consecutive breaches and tracks resolutions.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import os, sys, sqlite3, json, logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

default_args = {
    'owner': 'hospital_pipeline',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
    'start_date': datetime(2024, 1, 1),
}

def check_consecutive_breaches(**ctx):
    """Check for wards above 85% for 2+ consecutive hours."""
    db = os.path.join(BASE_DIR, "data", "hospital.db")
    conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
    cutoff = (datetime.now() - timedelta(hours=2)).isoformat()

    # Get recent hourly snapshots
    rows = conn.execute("""
        SELECT ward_id, ward_name, snapshot_hour, occupancy_percent
        FROM ward_occupancy_hourly
        WHERE snapshot_hour >= ?
        ORDER BY ward_id, snapshot_hour
    """, (cutoff,)).fetchall()

    # Group by ward
    ward_data = {}
    for r in rows:
        wid = r['ward_id']
        if wid not in ward_data: ward_data[wid] = []
        ward_data[wid].append(dict(r))

    breaches = []
    for wid, snapshots in ward_data.items():
        consecutive = 0
        peak = 0
        for s in snapshots:
            if s['occupancy_percent'] >= 85:
                consecutive += 1
                peak = max(peak, s['occupancy_percent'])
            else:
                consecutive = 0; peak = 0
        if consecutive >= 2:
            breaches.append({
                'ward_id': wid,
                'ward_name': snapshots[0]['ward_name'],
                'consecutive_hours': consecutive,
                'peak_occupancy': peak,
                'current_occupancy': snapshots[-1]['occupancy_percent'],
            })

    conn.close()
    ctx['ti'].xcom_push(key='breaches', value=breaches)
    return breaches

def write_breach_records(**ctx):
    """Write or update SLA breach records."""
    breaches = ctx['ti'].xcom_pull(key='breaches', task_ids='check_breaches')
    if not breaches: return

    db = os.path.join(BASE_DIR, "data", "hospital.db")
    conn = sqlite3.connect(db)
    now = datetime.now().isoformat()

    for b in breaches:
        # Check if active breach exists
        existing = conn.execute(
            "SELECT id FROM sla_breaches WHERE ward_id=? AND status='active'",
            (b['ward_id'],)).fetchone()
        if existing:
            conn.execute("""UPDATE sla_breaches SET
                consecutive_hours=?, peak_occupancy_percent=?,
                current_occupancy_percent=? WHERE id=?""",
                (b['consecutive_hours'], b['peak_occupancy'],
                 b['current_occupancy'], existing[0]))
        else:
            conn.execute("""INSERT INTO sla_breaches
                (ward_id, ward_name, breach_start_time, consecutive_hours,
                 peak_occupancy_percent, current_occupancy_percent, status)
                VALUES (?,?,?,?,?,?,'active')""",
                (b['ward_id'], b['ward_name'], now,
                 b['consecutive_hours'], b['peak_occupancy'], b['current_occupancy']))
            logging.warning(f"🚨 NEW BREACH: {b['ward_name']} ({b['current_occupancy']}%)")

    conn.commit(); conn.close()

def check_resolutions(**ctx):
    """Resolve breaches when ward drops below 80%."""
    db = os.path.join(BASE_DIR, "data", "hospital.db")
    conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
    now = datetime.now().isoformat()

    active = conn.execute(
        "SELECT id, ward_id, ward_name FROM sla_breaches WHERE status='active'").fetchall()

    for breach in active:
        current = conn.execute(
            "SELECT occupancy_percent FROM ward_occupancy_current WHERE ward_id=?",
            (breach['ward_id'],)).fetchone()
        if current and current['occupancy_percent'] < 80:
            conn.execute("""UPDATE sla_breaches SET
                status='resolved', resolved_at=?,
                resolution_note='Occupancy dropped below 80%' WHERE id=?""",
                (now, breach['id']))
            logging.info(f"✅ RESOLVED: {breach['ward_name']}")

    conn.commit(); conn.close()

def publish_breach_alerts(**ctx):
    """Publish active breaches to alert history."""
    breaches = ctx['ti'].xcom_pull(key='breaches', task_ids='check_breaches')
    if not breaches: return

    db = os.path.join(BASE_DIR, "data", "hospital.db")
    conn = sqlite3.connect(db)
    for b in breaches:
        severity = 'critical' if b['current_occupancy'] >= 95 else 'warning'
        conn.execute("""INSERT INTO alert_history
            (alert_type, ward_id, ward_name, severity, occupancy_percent, message)
            VALUES (?,?,?,?,?,?)""",
            ('sla_breach', b['ward_id'], b['ward_name'], severity,
             b['current_occupancy'],
             f"{b['ward_name']}: {b['consecutive_hours']}h above 85% (peak {b['peak_occupancy']}%)"))
    conn.commit(); conn.close()

with DAG('sla_monitoring', default_args=default_args,
         schedule_interval='*/15 * * * *', catchup=False,
         tags=['hospital','sla','critical']) as dag:

    t1 = PythonOperator(task_id='check_breaches', python_callable=check_consecutive_breaches)
    t2 = PythonOperator(task_id='write_breaches', python_callable=write_breach_records)
    t3 = PythonOperator(task_id='check_resolutions', python_callable=check_resolutions)
    t4 = PythonOperator(task_id='publish_alerts', python_callable=publish_breach_alerts)

    t1 >> t2 >> t3 >> t4
