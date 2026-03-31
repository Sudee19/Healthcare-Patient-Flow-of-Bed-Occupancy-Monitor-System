"""
Z-Score Anomaly Detection
Detects outbreak-level spikes using rolling mean/std over 7-day window.
Flags wards where current admission rate deviates by > 2.5 std deviations.
"""
import os, json, sqlite3, logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

logger = logging.getLogger("spark.anomaly")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLD_OCC_PATH = os.path.join(BASE_DIR, "data", "gold", "occupancy_hourly")
DB_PATH = os.path.join(BASE_DIR, "data", "hospital.db")
WARD_CFG = os.path.join(BASE_DIR, "config", "wards.json")

DEFAULT_THRESHOLD = 2.5
BASELINE_DAYS = 7

def load_hourly_data():
    """Load Gold hourly occupancy data."""
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.appName("AnomalyDetection").master("local[*]").getOrCreate()
        df = spark.read.parquet(GOLD_OCC_PATH)
        pdf = df.toPandas()
        spark.stop()
        return pdf
    except Exception:
        # Fallback: read from SQLite
        conn = sqlite3.connect(DB_PATH)
        pdf = pd.read_sql("SELECT * FROM ward_occupancy_hourly", conn)
        conn.close()
        return pdf

def compute_zscore_anomalies(df: pd.DataFrame, threshold: float = DEFAULT_THRESHOLD):
    """
    For each ward, compute z-score of current hour's admission count
    against the rolling 7-day mean/std for that hour-of-day.
    """
    results = []
    df['snapshot_hour'] = pd.to_datetime(df['snapshot_hour'])
    df['hour_of_day'] = df['snapshot_hour'].dt.hour
    df['date'] = df['snapshot_hour'].dt.date

    for ward_id in df['ward_id'].unique():
        ward_df = df[df['ward_id'] == ward_id].sort_values('snapshot_hour')
        ward_name = ward_df['ward_name'].iloc[0] if len(ward_df) > 0 else ward_id

        for hod in range(24):
            hour_data = ward_df[ward_df['hour_of_day'] == hod].copy()
            if len(hour_data) < 3:
                continue

            # Rolling 7-day window statistics
            hour_data = hour_data.sort_values('snapshot_hour')
            hour_data['rolling_mean'] = hour_data['admits_count'].rolling(
                window=BASELINE_DAYS, min_periods=2).mean()
            hour_data['rolling_std'] = hour_data['admits_count'].rolling(
                window=BASELINE_DAYS, min_periods=2).std()

            # Compute z-scores
            for idx, row in hour_data.iterrows():
                if pd.isna(row['rolling_mean']) or pd.isna(row['rolling_std']):
                    continue
                if row['rolling_std'] == 0:
                    z_score = 0.0
                else:
                    z_score = (row['admits_count'] - row['rolling_mean']) / row['rolling_std']

                is_anomaly = abs(z_score) > threshold

                results.append({
                    'ward_id': ward_id,
                    'ward_name': ward_name,
                    'detection_time': row['snapshot_hour'],
                    'hour_of_day': hod,
                    'z_score': round(z_score, 3),
                    'is_anomaly': is_anomaly,
                    'baseline_mean': round(row['rolling_mean'], 2),
                    'baseline_std': round(row['rolling_std'], 2),
                    'current_count': int(row['admits_count']),
                    'threshold_used': threshold,
                })

    return pd.DataFrame(results)

def save_anomalies(anomalies_df: pd.DataFrame):
    """Save anomaly flags to SQLite."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    # Create table if not exists
    conn.execute("""CREATE TABLE IF NOT EXISTS anomaly_flags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ward_id TEXT, ward_name TEXT, detection_time TIMESTAMP,
        hour_of_day INTEGER, z_score REAL, is_anomaly BOOLEAN,
        baseline_mean REAL, baseline_std REAL, current_count INTEGER,
        threshold_used REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    anomalies_df.to_sql('anomaly_flags', conn, if_exists='append', index=False)
    conn.close()

    anomaly_count = anomalies_df[anomalies_df['is_anomaly']].shape[0]
    logger.info(f"✅ Saved {len(anomalies_df)} z-score records ({anomaly_count} anomalies)")

def run_anomaly_detection(threshold: float = DEFAULT_THRESHOLD):
    """Main anomaly detection pipeline."""
    logger.info("="*60+"\n🔍 Z-Score Anomaly Detection\n"+"="*60)
    df = load_hourly_data()
    if len(df) == 0:
        logger.warning("No hourly data. Skipping."); return

    anomalies = compute_zscore_anomalies(df, threshold)
    if len(anomalies) == 0:
        logger.info("No anomaly data computed."); return

    save_anomalies(anomalies)

    # Print flagged anomalies
    flagged = anomalies[anomalies['is_anomaly']]
    if len(flagged) > 0:
        logger.warning(f"\n⚠️ ANOMALIES DETECTED ({len(flagged)}):")
        for _, a in flagged.iterrows():
            logger.warning(
                f"  🔴 {a['ward_name']} @ hour {a['hour_of_day']:02d}: "
                f"z={a['z_score']:.2f} (count={a['current_count']} vs "
                f"baseline={a['baseline_mean']:.1f}±{a['baseline_std']:.1f})")
    else:
        logger.info("✅ No anomalies detected")

    return anomalies

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)
    p = argparse.ArgumentParser()
    p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    a = p.parse_args()
    run_anomaly_detection(a.threshold)
