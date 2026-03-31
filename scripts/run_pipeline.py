"""
Full Medallion Pipeline Runner (Pandas-based for Java 25 compatibility)
Bronze -> Silver -> Gold -> Anomaly Detection

NOTE: PySpark 3.5.x requires Java 8/11/17. Since this system has Java 25,
we use Pandas for local execution while keeping the same medallion logic.
The PySpark scripts (spark/*.py) are production-ready for Databricks/EMR/HDInsight
where Java 11/17 is standard.
"""
import os, sys, time, json, logging, io
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(stream=sys.stdout)]
)
logger = logging.getLogger("pipeline")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

INPUT_FILE = os.path.join(BASE_DIR, "data", "test_events.json")
DB_PATH = os.path.join(BASE_DIR, "data", "hospital.db")
WARD_CFG = os.path.join(BASE_DIR, "config", "wards.json")

# Load ward config
with open(WARD_CFG) as f:
    ward_cfg = json.load(f)
WARD_BEDS = {w["ward_id"]: w["total_beds"] for w in ward_cfg["wards"]}
WARD_NAMES = {w["ward_id"]: w["ward_name"] for w in ward_cfg["wards"]}

print("\n" + "=" * 70)
print("  HEALTHCARE PATIENT FLOW -- MEDALLION PIPELINE")
print("  Bronze -> Silver -> Gold -> Anomaly Detection")
print("  (Pandas-based local execution)")
print("=" * 70 + "\n")

# =====================================================================
# STAGE 1: BRONZE INGESTION
# =====================================================================
print("-" * 70)
print("  [STAGE 1] BRONZE LAYER -- Raw Event Ingestion")
print("-" * 70)

start = time.time()

# Load raw JSON events
with open(INPUT_FILE) as f:
    raw_events = json.load(f)

bronze_df = pd.DataFrame(raw_events)
bronze_df['ingestion_timestamp'] = datetime.now().isoformat()
bronze_df['event_date'] = pd.to_datetime(bronze_df['timestamp']).dt.date

bronze_count = len(bronze_df)
bronze_time = time.time() - start

print(f"\n  [OK] Bronze Complete: {bronze_count} records ingested in {bronze_time:.1f}s")
print(f"\n  Bronze Schema:")
print(f"    Columns: {list(bronze_df.columns)}")
print(f"    Shape: {bronze_df.shape}")

# Check for nulls
print(f"\n  Data Quality Check (Bronze):")
for field in ["message_id", "patient_id", "event_type", "ward_id", "timestamp", "bed_id"]:
    null_count = bronze_df[field].isna().sum()
    status = "[OK]" if null_count == 0 else f"[WARN] {null_count} nulls"
    print(f"    {field}: {status}")

print(f"\n  Event type distribution:")
print(bronze_df['event_type'].value_counts().to_string())

print(f"\n  Ward distribution:")
print(bronze_df.groupby(['ward_id','ward_name']).size().reset_index(name='count').to_string(index=False))

print(f"\n  Bronze Sample (5 records):")
print(bronze_df[['message_id','event_type','patient_id','ward_id','ward_name','timestamp']].head(5).to_string(index=False))

# =====================================================================
# STAGE 2: SILVER CLEANING
# =====================================================================
print("\n" + "-" * 70)
print("  [STAGE 2] SILVER LAYER -- Data Quality & Cleaning")
print("-" * 70)

start = time.time()

VALID_EVENT_TYPES = ["ADT_A01", "ADT_A02", "ADT_A03"]

initial_count = len(bronze_df)
silver_df = bronze_df.copy()
rejected = []

# Rule 1: Reject null patient_id
mask_null_pid = silver_df['patient_id'].isna()
rejected_1 = silver_df[mask_null_pid].copy()
if len(rejected_1) > 0:
    rejected_1['rejection_reason'] = 'null_patient_id'
    rejected.append(rejected_1)
    print(f"  Rule 1: Rejected {len(rejected_1)} records (null patient_id)")
else:
    print(f"  Rule 1: [OK] No null patient_ids")
silver_df = silver_df[~mask_null_pid]

# Rule 2: Invalid event type
mask_invalid_type = ~silver_df['event_type'].isin(VALID_EVENT_TYPES)
rejected_2 = silver_df[mask_invalid_type].copy()
if len(rejected_2) > 0:
    rejected_2['rejection_reason'] = 'invalid_event_type'
    rejected.append(rejected_2)
    print(f"  Rule 2: Rejected {len(rejected_2)} records (invalid event_type)")
else:
    print(f"  Rule 2: [OK] All event types valid")
silver_df = silver_df[~mask_invalid_type]

# Rule 3: Flag late arrivals
silver_df['timestamp_dt'] = pd.to_datetime(silver_df['timestamp'])
now = datetime.now()
silver_df['is_late_arrival'] = (now - silver_df['timestamp_dt']).dt.total_seconds() > (24 * 3600)
late_count = silver_df['is_late_arrival'].sum()
if late_count > 0:
    print(f"  Rule 3: Flagged {late_count} late arrivals (>24h old)")
else:
    print(f"  Rule 3: [OK] No late arrivals")

# Rule 4: Standardize ward names
WARD_MAP = {
    "ICU EAST": "ICU East", "ICU WEST": "ICU West",
    "GENERAL A": "General A", "GENERAL B": "General B",
    "PEDIATRICS": "Pediatrics", "EMERGENCY": "Emergency", "ONCOLOGY": "Oncology"
}
silver_df['ward_name'] = silver_df['ward_name'].str.strip().str.upper().map(WARD_MAP).fillna(silver_df['ward_name'])
print(f"  Rule 4: [OK] Ward names standardized")

# Rule 5: Deduplicate (keep latest admission per patient)
admits = silver_df[silver_df['event_type'] == 'ADT_A01'].copy()
non_admits = silver_df[silver_df['event_type'] != 'ADT_A01'].copy()
admits_sorted = admits.sort_values('timestamp', ascending=False)
admits_deduped = admits_sorted.drop_duplicates(subset='patient_id', keep='first')
dup_count = len(admits) - len(admits_deduped)
if dup_count > 0:
    print(f"  Rule 5: Removed {dup_count} duplicate admissions")
else:
    print(f"  Rule 5: [OK] No duplicate admissions")
silver_df = pd.concat([admits_deduped, non_admits], ignore_index=True)

# Add Silver metadata
silver_df['processed_at'] = datetime.now().isoformat()
silver_df['event_hour'] = silver_df['timestamp_dt'].dt.hour

silver_count = len(silver_df)
silver_time = time.time() - start

print(f"\n  Silver Layer Summary:")
print(f"    Input (Bronze):  {initial_count}")
print(f"    Output (Silver): {silver_count}")
print(f"    Rejected:        {initial_count - silver_count}")
print(f"    Pass rate:       {(silver_count / initial_count * 100):.1f}%")

print(f"\n  [OK] Silver Complete: {silver_count} records in {silver_time:.1f}s")

print(f"\n  Silver Sample (5 records):")
print(silver_df[['message_id','event_type','patient_id','ward_id','ward_name','timestamp','is_late_arrival']].head(5).to_string(index=False))

# =====================================================================
# STAGE 3: GOLD AGGREGATION
# =====================================================================
print("\n" + "-" * 70)
print("  [STAGE 3] GOLD LAYER -- Occupancy Aggregation")
print("-" * 70)

start = time.time()

# Current Occupancy
print("\n  Computing current occupancy per ward...")
occ = silver_df.groupby(['ward_id','ward_name']).agg(
    total_admits=('event_type', lambda x: (x == 'ADT_A01').sum()),
    total_discharges=('event_type', lambda x: (x == 'ADT_A03').sum()),
).reset_index()
occ['total_beds'] = occ['ward_id'].map(WARD_BEDS)
occ['occupied_beds'] = (occ['total_admits'] - occ['total_discharges']).clip(0)
occ['occupied_beds'] = occ[['occupied_beds','total_beds']].min(axis=1)
occ['occupancy_percent'] = (occ['occupied_beds'] / occ['total_beds'] * 100).round(1)
occ['status'] = occ['occupancy_percent'].apply(
    lambda x: 'critical' if x >= 95 else 'warning' if x >= 85 else 'elevated' if x >= 70 else 'normal')

print(f"\n  Current Ward Occupancy:")
print(occ[['ward_id','ward_name','occupied_beds','total_beds','occupancy_percent','status']].to_string(index=False))

# Write to SQLite
conn = sqlite3.connect(DB_PATH)
now_str = datetime.now().isoformat()
for _, r in occ.iterrows():
    conn.execute("""INSERT OR REPLACE INTO ward_occupancy_current
        (ward_id,ward_name,occupied_beds,total_beds,occupancy_percent,status,updated_at)
        VALUES(?,?,?,?,?,?,?)""",
        (r['ward_id'],r['ward_name'],int(r['occupied_beds']),
         int(r['total_beds']),float(r['occupancy_percent']),r['status'],now_str))
conn.commit()

# Hourly snapshots
print("\n  Computing hourly occupancy snapshots...")
silver_df['snapshot_hour'] = silver_df['timestamp_dt'].dt.floor('H')
hourly = silver_df.groupby(['ward_id','ward_name','snapshot_hour']).agg(
    admits_count=('event_type', lambda x: (x == 'ADT_A01').sum()),
    discharges_count=('event_type', lambda x: (x == 'ADT_A03').sum()),
    transfers_count=('event_type', lambda x: (x == 'ADT_A02').sum()),
).reset_index()

# Compute cumulative occupancy
hourly = hourly.sort_values(['ward_id','snapshot_hour'])
hourly['cum_admits'] = hourly.groupby('ward_id')['admits_count'].cumsum()
hourly['cum_discharges'] = hourly.groupby('ward_id')['discharges_count'].cumsum()
hourly['net'] = hourly['cum_admits'] - hourly['cum_discharges']
hourly['total_beds'] = hourly['ward_id'].map(WARD_BEDS)
hourly['occupied_beds'] = hourly['net'].clip(0).clip(upper=hourly['total_beds'])
hourly['occupancy_percent'] = (hourly['occupied_beds'] / hourly['total_beds'] * 100).round(1)

print(f"  Hourly snapshots: {len(hourly)} records")
print(f"\n  Hourly Occupancy Sample (10 records):")
print(hourly[['ward_id','ward_name','snapshot_hour','occupied_beds','total_beds','occupancy_percent']].head(10).to_string(index=False))

# Write to SQLite
hourly_sql = hourly[['ward_id','ward_name','snapshot_hour','occupied_beds','total_beds','occupancy_percent','admits_count','discharges_count']].copy()
hourly_sql.to_sql('ward_occupancy_hourly', conn, if_exists='replace', index=False)

# 7-day baseline
print("\n  Computing 7-day baseline averages...")
hourly['hour_of_day'] = pd.to_datetime(hourly['snapshot_hour']).dt.hour
baseline = hourly.groupby(['ward_id','ward_name','hour_of_day']).agg(
    baseline_avg_occupancy=('occupancy_percent', 'mean'),
    baseline_std_occupancy=('occupancy_percent', 'std'),
    sample_count=('occupancy_percent', 'count')
).reset_index()
baseline['baseline_avg_occupancy'] = baseline['baseline_avg_occupancy'].round(1)
baseline['baseline_std_occupancy'] = baseline['baseline_std_occupancy'].fillna(0).round(2)
baseline.to_sql('ward_baseline', conn, if_exists='replace', index=False)
print(f"  Baseline records: {len(baseline)}")

# Daily summary
print("\n  Computing daily summaries...")
hourly['report_date'] = pd.to_datetime(hourly['snapshot_hour']).dt.date
daily = hourly.groupby(['ward_id','ward_name','report_date']).agg(
    avg_occ=('occupancy_percent', 'mean'),
    peak_occ=('occupancy_percent', 'max'),
    min_occ=('occupancy_percent', 'min'),
    total_admits=('admits_count', 'sum'),
    total_discharges=('discharges_count', 'sum'),
    sla_breach_hours=('occupancy_percent', lambda x: (x >= 85).sum())
).reset_index()
daily.columns = ['ward_id','ward_name','report_date','avg_occupancy_percent','peak_occupancy_percent',
                 'min_occupancy_percent','total_admits','total_discharges','sla_breach_hours']
daily.to_sql('ward_occupancy_daily', conn, if_exists='replace', index=False)

print(f"\n  Daily Summary (10 records):")
print(daily.head(10).to_string(index=False))

conn.commit()
gold_time = time.time() - start
print(f"\n  [OK] Gold Complete in {gold_time:.1f}s")

# =====================================================================
# STAGE 4: ANOMALY DETECTION
# =====================================================================
print("\n" + "-" * 70)
print("  [STAGE 4] ANOMALY DETECTION -- Z-Score Analysis")
print("-" * 70)

start = time.time()

THRESHOLD = 2.5
BASELINE_DAYS = 7

results = []
hourly['snapshot_hour_dt'] = pd.to_datetime(hourly['snapshot_hour'])
hourly['hour_of_day'] = hourly['snapshot_hour_dt'].dt.hour

for ward_id in hourly['ward_id'].unique():
    ward_df = hourly[hourly['ward_id'] == ward_id].sort_values('snapshot_hour')
    ward_name = ward_df['ward_name'].iloc[0]
    
    for hod in range(24):
        hour_data = ward_df[ward_df['hour_of_day'] == hod].copy()
        if len(hour_data) < 3:
            continue
        
        hour_data = hour_data.sort_values('snapshot_hour')
        hour_data['rolling_mean'] = hour_data['admits_count'].rolling(window=BASELINE_DAYS, min_periods=2).mean()
        hour_data['rolling_std'] = hour_data['admits_count'].rolling(window=BASELINE_DAYS, min_periods=2).std()
        
        for _, row in hour_data.iterrows():
            if pd.isna(row['rolling_mean']) or pd.isna(row['rolling_std']):
                continue
            z_score = 0.0 if row['rolling_std'] == 0 else (row['admits_count'] - row['rolling_mean']) / row['rolling_std']
            is_anomaly = abs(z_score) > THRESHOLD
            
            results.append({
                'ward_id': ward_id, 'ward_name': ward_name,
                'detection_time': row['snapshot_hour'],
                'hour_of_day': hod,
                'z_score': round(z_score, 3), 'is_anomaly': is_anomaly,
                'baseline_mean': round(row['rolling_mean'], 2),
                'baseline_std': round(row['rolling_std'], 2),
                'current_count': int(row['admits_count']),
                'threshold_used': THRESHOLD
            })

anomalies_df = pd.DataFrame(results)
anomaly_time = time.time() - start

if len(anomalies_df) > 0:
    # Save to SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS anomaly_flags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ward_id TEXT, ward_name TEXT, detection_time TIMESTAMP,
        hour_of_day INTEGER, z_score REAL, is_anomaly BOOLEAN,
        baseline_mean REAL, baseline_std REAL, current_count INTEGER,
        threshold_used REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    anomalies_df.to_sql('anomaly_flags', conn, if_exists='replace', index=False)
    conn.close()
    
    flagged = anomalies_df[anomalies_df['is_anomaly']]
    print(f"\n  Total z-score records computed: {len(anomalies_df)}")
    print(f"  Anomalies detected (|z| > {THRESHOLD}): {len(flagged)}")
    
    if len(flagged) > 0:
        print(f"\n  ANOMALIES DETECTED:")
        for _, a in flagged.head(20).iterrows():
            direction = "HIGH" if a['z_score'] > 0 else "LOW"
            print(f"    [{direction}] {a['ward_name']:12s} @ hour {int(a['hour_of_day']):02d}: "
                  f"z={a['z_score']:+.2f}  (count={int(a['current_count'])} vs "
                  f"baseline={a['baseline_mean']:.1f} +/- {a['baseline_std']:.1f})")
    else:
        print("\n  [OK] No anomalies detected -- all wards within normal ranges")
else:
    print(f"\n  [OK] No data for anomaly computation")

print(f"\n  [OK] Anomaly Detection Complete in {anomaly_time:.1f}s")

# =====================================================================
# SUMMARY
# =====================================================================
total_time = bronze_time + silver_time + gold_time + anomaly_time
print("\n" + "=" * 70)
print("  PIPELINE SUMMARY")
print("=" * 70)
print(f"  Bronze:   {bronze_count:>6} records  ({bronze_time:.1f}s)")
print(f"  Silver:   {silver_count:>6} records  ({silver_time:.1f}s)")
print(f"  Gold:     {len(hourly):>6} hourly + {len(daily)} daily records  ({gold_time:.1f}s)")
print(f"  Anomaly:  {len(anomalies_df):>6} z-scores computed  ({anomaly_time:.1f}s)")
print(f"  Total:    {total_time:.1f}s")
print("=" * 70)
print("  All pipeline stages completed successfully!")
print("=" * 70 + "\n")

# Verify SQLite tables
conn = sqlite3.connect(DB_PATH)
tables = ["ward_occupancy_current","ward_occupancy_hourly","ward_baseline",
          "sla_breaches","anomaly_flags","ward_occupancy_daily"]
print("  SQLite Database Summary:")
for t in tables:
    try:
        count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"    [{t}]: {count} rows")
    except Exception as e:
        print(f"    [{t}]: Error - {e}")
conn.close()

print("\n  Pipeline execution complete!\n")
