"""
Database initialization and utilities.
Creates SQLite tables for the API layer and manages connections.
"""

import sqlite3
import os
import logging
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger("db.init")

# Default DB path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "hospital.db")


def get_db_path() -> str:
    """Get database path from env or default."""
    return os.environ.get("SQLITE_DB_PATH", DEFAULT_DB_PATH)


@contextmanager
def get_connection(db_path: str = None):
    """Context manager for SQLite connections."""
    path = db_path or get_db_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database(db_path: str = None):
    """Create all required tables."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # ─── Ward Configuration ──────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wards (
                ward_id TEXT PRIMARY KEY,
                ward_name TEXT NOT NULL,
                total_beds INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ─── Current Occupancy (updated every cycle) ────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ward_occupancy_current (
                ward_id TEXT PRIMARY KEY,
                ward_name TEXT NOT NULL,
                occupied_beds INTEGER NOT NULL DEFAULT 0,
                total_beds INTEGER NOT NULL,
                occupancy_percent REAL NOT NULL DEFAULT 0.0,
                status TEXT NOT NULL DEFAULT 'normal',
                trend TEXT DEFAULT 'stable',
                last_hour_occupancy_percent REAL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ward_id) REFERENCES wards(ward_id)
            )
        """)

        # ─── Hourly Occupancy Snapshots ──────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ward_occupancy_hourly (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ward_id TEXT NOT NULL,
                ward_name TEXT NOT NULL,
                snapshot_hour TIMESTAMP NOT NULL,
                occupied_beds INTEGER NOT NULL,
                total_beds INTEGER NOT NULL,
                occupancy_percent REAL NOT NULL,
                admits_count INTEGER DEFAULT 0,
                discharges_count INTEGER DEFAULT 0,
                transfers_in INTEGER DEFAULT 0,
                transfers_out INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ward_id, snapshot_hour)
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_occupancy_hourly_ward_time
            ON ward_occupancy_hourly(ward_id, snapshot_hour)
        """)

        # ─── Daily Summaries ─────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ward_occupancy_daily (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ward_id TEXT NOT NULL,
                ward_name TEXT NOT NULL,
                report_date DATE NOT NULL,
                avg_occupancy_percent REAL,
                peak_occupancy_percent REAL,
                peak_occupancy_hour INTEGER,
                min_occupancy_percent REAL,
                total_admits INTEGER DEFAULT 0,
                total_discharges INTEGER DEFAULT 0,
                sla_breach_hours INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ward_id, report_date)
            )
        """)

        # ─── 7-Day Baseline ─────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ward_baseline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ward_id TEXT NOT NULL,
                ward_name TEXT NOT NULL,
                hour_of_day INTEGER NOT NULL,
                day_of_week INTEGER,
                baseline_avg_occupancy REAL NOT NULL,
                baseline_std_occupancy REAL DEFAULT 0.0,
                sample_count INTEGER DEFAULT 0,
                computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ward_id, hour_of_day, day_of_week)
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_baseline_ward_hour
            ON ward_baseline(ward_id, hour_of_day)
        """)

        # ─── SLA Breaches ────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sla_breaches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ward_id TEXT NOT NULL,
                ward_name TEXT NOT NULL,
                breach_start_time TIMESTAMP NOT NULL,
                breach_end_time TIMESTAMP,
                consecutive_hours REAL DEFAULT 0,
                peak_occupancy_percent REAL,
                current_occupancy_percent REAL,
                status TEXT NOT NULL DEFAULT 'active',
                llm_explanation TEXT,
                llm_confidence TEXT,
                resolution_note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_breaches_ward_status
            ON sla_breaches(ward_id, status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_breaches_status
            ON sla_breaches(status)
        """)

        # ─── Anomaly Flags (Z-Score) ─────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomaly_flags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ward_id TEXT NOT NULL,
                ward_name TEXT NOT NULL,
                detection_time TIMESTAMP NOT NULL,
                hour_of_day INTEGER NOT NULL,
                z_score REAL NOT NULL,
                is_anomaly BOOLEAN NOT NULL DEFAULT 0,
                baseline_mean REAL NOT NULL,
                baseline_std REAL NOT NULL,
                current_count INTEGER NOT NULL,
                threshold_used REAL DEFAULT 2.5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_anomaly_ward_time
            ON anomaly_flags(ward_id, detection_time)
        """)

        # ─── LLM Explanations ───────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_explanations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                breach_id INTEGER,
                ward_id TEXT NOT NULL,
                ward_name TEXT NOT NULL,
                context_json TEXT NOT NULL,
                prompt_used TEXT,
                explanation TEXT NOT NULL,
                confidence TEXT DEFAULT 'medium',
                model_used TEXT DEFAULT 'claude-sonnet',
                is_fallback BOOLEAN DEFAULT 0,
                tokens_used INTEGER DEFAULT 0,
                latency_ms INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (breach_id) REFERENCES sla_breaches(id)
            )
        """)

        # ─── Alert History ───────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                ward_id TEXT NOT NULL,
                ward_name TEXT NOT NULL,
                message TEXT,
                severity TEXT DEFAULT 'warning',
                occupancy_percent REAL,
                metadata_json TEXT,
                acknowledged BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_ward
            ON alert_history(ward_id, created_at)
        """)

        # ─── Seed ward data ─────────────────────────────────────────────
        import json
        wards_config_path = os.path.join(BASE_DIR, "config", "wards.json")
        if os.path.exists(wards_config_path):
            with open(wards_config_path) as f:
                wards_data = json.load(f)
            for ward in wards_data["wards"]:
                cursor.execute("""
                    INSERT OR REPLACE INTO wards (ward_id, ward_name, total_beds)
                    VALUES (?, ?, ?)
                """, (ward["ward_id"], ward["ward_name"], ward["total_beds"]))

                cursor.execute("""
                    INSERT OR IGNORE INTO ward_occupancy_current 
                    (ward_id, ward_name, occupied_beds, total_beds, occupancy_percent, status)
                    VALUES (?, ?, 0, ?, 0.0, 'normal')
                """, (ward["ward_id"], ward["ward_name"], ward["total_beds"]))

        conn.commit()
        logger.info(f"✅ Database initialized at {db_path or get_db_path()}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database()
