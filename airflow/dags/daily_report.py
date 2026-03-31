"""
Airflow DAG 2: Daily Report
Runs daily at 6 AM. Aggregates yesterday's data, runs anomaly detection.
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
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2024, 1, 1),
}

def aggregate_daily_summary(**ctx):
    """Aggregate yesterday's hourly snapshots into daily summary."""
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    db = os.path.join(BASE_DIR, "data", "hospital.db")
    conn = sqlite3.connect(db)
    conn.execute(f"""
        INSERT OR REPLACE INTO ward_occupancy_daily
        (ward_id, ward_name, report_date, avg_occupancy_percent,
         peak_occupancy_percent, min_occupancy_percent,
         total_admits, total_discharges, sla_breach_hours)
        SELECT ward_id, ward_name, date(snapshot_hour),
            ROUND(AVG(occupancy_percent),1),
            ROUND(MAX(occupancy_percent),1),
            ROUND(MIN(occupancy_percent),1),
            SUM(admits_count), SUM(discharges_count),
            SUM(CASE WHEN occupancy_percent >= 85 THEN 1 ELSE 0 END)
        FROM ward_occupancy_hourly
        WHERE date(snapshot_hour) = '{yesterday}'
        GROUP BY ward_id, ward_name, date(snapshot_hour)
    """)
    conn.commit(); conn.close()
    logging.info(f"✅ Daily summary for {yesterday}")

def run_anomaly_detection(**ctx):
    from spark.anomaly_detection import run_anomaly_detection
    run_anomaly_detection()

def generate_summary_json(**ctx):
    """Generate summary JSON for LLM consumption."""
    db = os.path.join(BASE_DIR, "data", "hospital.db")
    conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    daily = [dict(r) for r in conn.execute(
        "SELECT * FROM ward_occupancy_daily WHERE report_date=?", (yesterday,)).fetchall()]
    anomalies = [dict(r) for r in conn.execute(
        "SELECT * FROM anomaly_flags WHERE date(detection_time)=? AND is_anomaly=1",
        (yesterday,)).fetchall()]
    conn.close()

    summary = {
        'report_date': yesterday,
        'generated_at': datetime.now().isoformat(),
        'daily_summaries': daily,
        'anomalies_detected': anomalies,
        'total_anomalies': len(anomalies),
    }
    out = os.path.join(BASE_DIR, "data", "reports", f"daily_{yesterday}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w') as f: json.dump(summary, f, indent=2, default=str)
    logging.info(f"✅ Summary JSON: {out}")

def archive_old_bronze(**ctx):
    """Archive Bronze data older than 30 days."""
    import shutil
    bronze = os.path.join(BASE_DIR, "data", "bronze")
    archive = os.path.join(BASE_DIR, "data", "archive", "bronze")
    cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not os.path.exists(bronze): return
    for d in os.listdir(bronze):
        if d.startswith("event_date=") and d.split("=")[1] < cutoff:
            src = os.path.join(bronze, d)
            dst = os.path.join(archive, d)
            os.makedirs(archive, exist_ok=True)
            shutil.move(src, dst)
            logging.info(f"📦 Archived {d}")

with DAG('daily_report', default_args=default_args,
         schedule_interval='0 6 * * *', catchup=False,
         tags=['hospital','daily']) as dag:

    t1 = PythonOperator(task_id='aggregate_daily', python_callable=aggregate_daily_summary)
    t2 = PythonOperator(task_id='anomaly_detection', python_callable=run_anomaly_detection)
    t3 = PythonOperator(task_id='generate_summary', python_callable=generate_summary_json)
    t4 = PythonOperator(task_id='archive_bronze', python_callable=archive_old_bronze)

    t1 >> t2 >> t3 >> t4
