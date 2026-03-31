# Databricks notebook source
# MAGIC %md
# MAGIC # 🏗️ Databricks Lakehouse — Delta Lake for Hospital Data
# MAGIC 
# MAGIC Implements the Lakehouse architecture using Delta Lake for the hospital
# MAGIC bed occupancy monitoring system.
# MAGIC 
# MAGIC **Learning Objectives:**
# MAGIC - Create and manage Delta tables
# MAGIC - Understand ACID transactions in a Lakehouse
# MAGIC - Use Schema Enforcement and Evolution
# MAGIC - Implement the Medallion Architecture (Bronze → Silver → Gold)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Setting Up the Hospital Lakehouse

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Create the hospital database
# MAGIC CREATE DATABASE IF NOT EXISTS hospital_lakehouse
# MAGIC COMMENT 'Healthcare Patient Flow & Bed Occupancy Monitor';
# MAGIC 
# MAGIC USE hospital_lakehouse;

# COMMAND ----------

from pyspark.sql.types import *
from pyspark.sql.functions import *
from datetime import datetime, timedelta
import random

random.seed(42)

# Hospital ward configuration
ward_config = [
    ("W-001", "ICU East", 20, "critical_care", 95),
    ("W-002", "ICU West", 20, "critical_care", 95),
    ("W-003", "General A", 40, "general", 85),
    ("W-004", "General B", 40, "general", 85),
    ("W-005", "Pediatrics", 25, "specialty", 90),
    ("W-006", "Emergency", 30, "emergency", 80),
    ("W-007", "Oncology", 15, "specialty", 90),
]

wards_df = spark.createDataFrame(ward_config,
    ["ward_id", "ward_name", "total_beds", "ward_type", "sla_threshold"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Creating Delta Tables — Bronze Layer

# COMMAND ----------

# Generate realistic hospital events
rows = []
for i in range(5000):
    w = random.choice(ward_config)
    evt = random.choices(["ADT_A01", "ADT_A02", "ADT_A03"], weights=[45, 15, 40])[0]
    ts = datetime.now() - timedelta(hours=random.randint(0, 336))
    rows.append((
        f"msg-{i:05d}", evt, f"P-{random.randint(1, 800):06d}",
        w[0], w[1], f"B-{w[0][-3:]}-{random.randint(1, w[2]):03d}",
        ts.isoformat(),
        random.choice(["cardiac", "respiratory", "trauma", "neurological"]),
        random.choice(["adult", "pediatric", "geriatric"]),
        random.choice(["emergency", "elective", "transfer"]),
        None, None
    ))

event_schema = StructType([
    StructField("message_id", StringType()), StructField("event_type", StringType()),
    StructField("patient_id", StringType()), StructField("ward_id", StringType()),
    StructField("ward_name", StringType()), StructField("bed_id", StringType()),
    StructField("timestamp", StringType()), StructField("diagnosis_category", StringType()),
    StructField("age_group", StringType()), StructField("priority", StringType()),
    StructField("transfer_from_ward", StringType()), StructField("transfer_from_bed", StringType()),
])

events_df = spark.createDataFrame(rows, event_schema)

# COMMAND ----------

# Write Bronze Delta table with metadata
bronze_df = (events_df
    .withColumn("ingestion_timestamp", current_timestamp())
    .withColumn("event_date", to_date(col("timestamp")))
    .withColumn("source_system", lit("HL7_ADT"))
    .withColumn("source_file", lit("simulated_batch")))

bronze_df.write.format("delta") \
    .mode("overwrite") \
    .partitionBy("event_date", "ward_id") \
    .saveAsTable("hospital_lakehouse.bronze_events")

print(f"✅ Bronze Delta table created: {bronze_df.count()} records")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Verify the Bronze table
# MAGIC DESCRIBE EXTENDED hospital_lakehouse.bronze_events

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. ACID Transactions — Delta Lake Guarantees

# COMMAND ----------

# MAGIC %sql
# MAGIC -- View transaction history
# MAGIC DESCRIBE HISTORY hospital_lakehouse.bronze_events

# COMMAND ----------

# Demonstrate atomic write — insert new batch
new_events = []
for i in range(100):
    w = random.choice(ward_config)
    ts = datetime.now() - timedelta(minutes=random.randint(0, 60))
    new_events.append((
        f"msg-new-{i:05d}", "ADT_A01", f"P-{random.randint(800, 999):06d}",
        w[0], w[1], f"B-{w[0][-3:]}-{random.randint(1, w[2]):03d}",
        ts.isoformat(), "cardiac", "adult", "emergency", None, None
    ))

new_df = spark.createDataFrame(new_events, event_schema)
new_bronze = (new_df
    .withColumn("ingestion_timestamp", current_timestamp())
    .withColumn("event_date", to_date(col("timestamp")))
    .withColumn("source_system", lit("HL7_ADT"))
    .withColumn("source_file", lit("realtime_batch_001")))

new_bronze.write.format("delta").mode("append").saveAsTable("hospital_lakehouse.bronze_events")
print(f"✅ Appended {new_bronze.count()} new events atomically")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- See the new version in history
# MAGIC DESCRIBE HISTORY hospital_lakehouse.bronze_events

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Time Travel — Query Historical States

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Query version 0 (original data)
# MAGIC SELECT COUNT(*) AS record_count, 'version_0' AS version
# MAGIC FROM hospital_lakehouse.bronze_events VERSION AS OF 0
# MAGIC UNION ALL
# MAGIC SELECT COUNT(*) AS record_count, 'current' AS version
# MAGIC FROM hospital_lakehouse.bronze_events

# COMMAND ----------

# Python API for time travel
v0_df = spark.read.format("delta").option("versionAsOf", 0).table("hospital_lakehouse.bronze_events")
current_df = spark.read.format("delta").table("hospital_lakehouse.bronze_events")

print(f"Version 0 records: {v0_df.count()}")
print(f"Current records:   {current_df.count()}")
print(f"New records added:  {current_df.count() - v0_df.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Schema Enforcement & Evolution

# COMMAND ----------

# Schema enforcement: Delta rejects mismatched schemas
try:
    bad_data = spark.createDataFrame([("test", 123)], ["message_id", "bad_column"])
    bad_data.write.format("delta").mode("append").saveAsTable("hospital_lakehouse.bronze_events")
except Exception as e:
    print(f"❌ Schema enforcement caught error:\n   {str(e)[:200]}")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Schema evolution: add new columns safely
# MAGIC ALTER TABLE hospital_lakehouse.bronze_events
# MAGIC SET TBLPROPERTIES ('delta.columnMapping.mode' = 'name');

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Delta Lake Optimization

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Optimize file layout with Z-ORDER for fast queries
# MAGIC OPTIMIZE hospital_lakehouse.bronze_events
# MAGIC ZORDER BY (ward_id, timestamp)

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Vacuum old files (keep 7 days of history)
# MAGIC -- VACUUM hospital_lakehouse.bronze_events RETAIN 168 HOURS

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Wards Reference Table

# COMMAND ----------

wards_df.write.format("delta").mode("overwrite").saveAsTable("hospital_lakehouse.wards")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM hospital_lakehouse.wards ORDER BY ward_id

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Lakehouse Metadata Queries

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Show all tables in the hospital lakehouse
# MAGIC SHOW TABLES IN hospital_lakehouse

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Table statistics
# MAGIC DESCRIBE DETAIL hospital_lakehouse.bronze_events

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Summary
# MAGIC 
# MAGIC In this notebook we demonstrated:
# MAGIC 1. **Delta Lake tables** with ACID transactions
# MAGIC 2. **Partitioning** by event_date and ward_id
# MAGIC 3. **Time Travel** — query any historical version
# MAGIC 4. **Schema Enforcement** — reject bad data automatically
# MAGIC 5. **OPTIMIZE + ZORDER** — fast query performance
# MAGIC 6. **Transaction History** — full audit trail
# MAGIC 
# MAGIC **Next →** `02_Delta_Lake_Deep_Dive.py`
