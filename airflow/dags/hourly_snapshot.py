"""
Airflow DAG 1: Hourly Snapshot
Runs every hour at minute 5. Checks Gold data, writes snapshot, checks SLA.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.sensors.filesystem import FileSensor
import os, sys, sqlite3, json, logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

default_args = {
    'owner': 'hospital_pipeline',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2024, 1, 1),
}

def run_gold_aggregation(**ctx):
    from spark.gold_aggregation import get_spark, run_gold
    spark = get_spark("AirflowGold")
    run_gold(spark)
    spark.stop()

def write_hourly_snapshot(**ctx):
    db = os.path.join(BASE_DIR, "data", "hospital.db")
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT ward_id, ward_name, occupancy_percent FROM ward_occupancy_current")
    rows = cur.fetchall()
    now = datetime.now().isoformat()
    for r in rows:
        cur.execute("""INSERT OR REPLACE INTO ward_occupancy_hourly
            (ward_id, ward_name, snapshot_hour, occupied_beds, total_beds, occupancy_percent)
            SELECT ward_id, ward_name, ?, occupied_beds, total_beds, occupancy_percent
            FROM ward_occupancy_current WHERE ward_id = ?""", (now, r[0]))
    conn.commit(); conn.close()
    return [{'ward_id': r[0], 'ward_name': r[1], 'pct': r[2]} for r in rows]

def check_sla_breaches(**ctx):
    db = os.path.join(BASE_DIR, "data", "hospital.db")
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT ward_id, ward_name, occupancy_percent FROM ward_occupancy_current WHERE occupancy_percent >= 85")
    breaches = cur.fetchall()
    conn.close()
    if breaches:
        for b in breaches:
            logging.warning(f"⚠️ SLA BREACH: {b[1]} at {b[2]}%")
        return 'publish_alerts'
    return 'no_breach'

def publish_sla_alerts(**ctx):
    db = os.path.join(BASE_DIR, "data", "hospital.db")
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT ward_id, ward_name, occupancy_percent FROM ward_occupancy_current WHERE occupancy_percent >= 85")
    for r in cur.fetchall():
        cur.execute("""INSERT INTO alert_history (alert_type, ward_id, ward_name, severity, occupancy_percent, message)
            VALUES (?,?,?,?,?,?)""",
            ('sla_breach', r[0], r[1], 'critical' if r[2]>=95 else 'warning',
             r[2], f"{r[1]} at {r[2]}% occupancy"))
    conn.commit(); conn.close()

def no_breach(**ctx):
    logging.info("✅ All wards within SLA")

with DAG('hourly_snapshot', default_args=default_args,
         schedule_interval='5 * * * *', catchup=False,
         tags=['hospital','hourly']) as dag:

    t1 = PythonOperator(task_id='run_gold_aggregation', python_callable=run_gold_aggregation)
    t2 = PythonOperator(task_id='write_snapshot', python_callable=write_hourly_snapshot)
    t3 = BranchPythonOperator(task_id='check_sla', python_callable=check_sla_breaches)
    t4 = PythonOperator(task_id='publish_alerts', python_callable=publish_sla_alerts)
    t5 = PythonOperator(task_id='no_breach', python_callable=no_breach)

    t1 >> t2 >> t3 >> [t4, t5]
