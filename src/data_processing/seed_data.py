"""
Quick seed script - generates test data and populates SQLite
without requiring Kafka or Spark. Useful for testing API + Dashboard.
"""
import os, sys, json, sqlite3, random
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from db import init_database

DB_PATH = os.path.join(BASE_DIR, "data", "hospital.db")
WARD_CFG = os.path.join(BASE_DIR, "config", "wards.json")

def seed():
    print("[SEED] Seeding database...")
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    init_database(DB_PATH)

    with open(WARD_CFG) as f:
        cfg = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    now = datetime.now()

    # Seed current occupancy
    for w in cfg["wards"]:
        occ = random.randint(int(w["total_beds"]*0.3), int(w["total_beds"]*0.95))
        pct = round((occ / w["total_beds"]) * 100, 1)
        status = "critical" if pct>=95 else "warning" if pct>=85 else "elevated" if pct>=70 else "normal"
        trend = random.choice(["rising","stable","falling"])
        conn.execute("""INSERT OR REPLACE INTO ward_occupancy_current
            (ward_id,ward_name,occupied_beds,total_beds,occupancy_percent,status,trend,updated_at)
            VALUES(?,?,?,?,?,?,?,?)""",
            (w["ward_id"],w["ward_name"],occ,w["total_beds"],pct,status,trend,now.isoformat()))

    # Seed 7 days of hourly snapshots
    for w in cfg["wards"]:
        base_occ = random.uniform(40, 70)
        for h in range(168):  # 7 days
            t = now - timedelta(hours=168-h)
            hour_mult = [0.3,0.2,0.15,0.15,0.2,0.3,0.5,0.7,1.2,1.4,1.3,1.1,
                        0.9,0.8,0.8,0.9,1.0,1.1,1.3,1.4,1.2,1.0,0.7,0.4][t.hour]
            occ_pct = max(5, min(100, base_occ * hour_mult + random.gauss(0, 8)))
            occ_beds = int(occ_pct / 100 * w["total_beds"])
            admits = random.randint(0, 6)
            discharges = random.randint(0, 5)
            conn.execute("""INSERT OR IGNORE INTO ward_occupancy_hourly
                (ward_id,ward_name,snapshot_hour,occupied_beds,total_beds,
                 occupancy_percent,admits_count,discharges_count)
                VALUES(?,?,?,?,?,?,?,?)""",
                (w["ward_id"],w["ward_name"],t.isoformat(),
                 occ_beds,w["total_beds"],round(occ_pct,1),admits,discharges))

    # Seed baselines
    for w in cfg["wards"]:
        for hod in range(24):
            avg = random.uniform(40, 75)
            conn.execute("""INSERT OR REPLACE INTO ward_baseline
                (ward_id,ward_name,hour_of_day,baseline_avg_occupancy,
                 baseline_std_occupancy,sample_count)
                VALUES(?,?,?,?,?,?)""",
                (w["ward_id"],w["ward_name"],hod,round(avg,1),round(random.uniform(3,12),2),7))

    # Seed some breaches
    breach_wards = random.sample([w for w in cfg["wards"]], 2)
    for w in breach_wards:
        conn.execute("""INSERT INTO sla_breaches
            (ward_id,ward_name,breach_start_time,consecutive_hours,
             peak_occupancy_percent,current_occupancy_percent,status,
             llm_explanation,llm_confidence)
            VALUES(?,?,?,?,?,?,?,?,?)""",
            (w["ward_id"],w["ward_name"],
             (now-timedelta(hours=random.randint(1,4))).isoformat(),
             random.randint(2,5), random.uniform(87,98), random.uniform(85,95),
             "active",
             f"{w['ward_name']} admission rate is elevated due to higher-than-normal patient volume. "
             f"Based on 7-day patterns, occupancy should normalize within 2-4 hours as scheduled discharges proceed.",
             random.choice(["high","medium"])))

    # Seed anomaly flags
    for w in cfg["wards"]:
        z = random.gauss(0, 1.5)
        conn.execute("""INSERT INTO anomaly_flags
            (ward_id,ward_name,detection_time,hour_of_day,z_score,
             is_anomaly,baseline_mean,baseline_std,current_count,threshold_used)
            VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (w["ward_id"],w["ward_name"],now.isoformat(),now.hour,
             round(z,3), abs(z)>2.5, round(random.uniform(3,6),2),
             round(random.uniform(1,3),2), random.randint(1,12), 2.5))

    # Seed alerts
    conn.execute("""INSERT INTO alert_history
        (alert_type,ward_id,ward_name,severity,occupancy_percent,message)
        VALUES(?,?,?,?,?,?)""",
        ("sla_breach", breach_wards[0]["ward_id"], breach_wards[0]["ward_name"],
         "warning", 89.5, f"{breach_wards[0]['ward_name']} above 85% for 2 hours"))

    # Seed daily summaries
    for w in cfg["wards"]:
        for d in range(7):
            dt = (now - timedelta(days=d)).strftime('%Y-%m-%d')
            conn.execute("""INSERT OR IGNORE INTO ward_occupancy_daily
                (ward_id,ward_name,report_date,avg_occupancy_percent,
                 peak_occupancy_percent,min_occupancy_percent,
                 total_admits,total_discharges,sla_breach_hours)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (w["ward_id"],w["ward_name"],dt,
                 round(random.uniform(45,75),1),round(random.uniform(70,95),1),
                 round(random.uniform(20,50),1),
                 random.randint(15,60),random.randint(12,55),random.randint(0,5)))

    conn.commit()
    conn.close()

    # Verify
    conn = sqlite3.connect(DB_PATH)
    tables = ["ward_occupancy_current","ward_occupancy_hourly","ward_baseline",
              "sla_breaches","anomaly_flags","alert_history","ward_occupancy_daily"]
    print("")
    print("[OK] Database seeded:")
    for t in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  [+] {t}: {count} rows")
    conn.close()
    print("")
    print("[DONE] Ready! Run the API with: python -m api.main")

if __name__ == "__main__":
    seed()
