# Databricks notebook source
# MAGIC %md
# MAGIC # 🏥 Introduction to Databricks — Healthcare Patient Flow Monitor
# MAGIC 
# MAGIC This notebook introduces the Databricks workspace and demonstrates core features
# MAGIC using the **Hospital Bed Occupancy Monitoring** project.
# MAGIC 
# MAGIC **Learning Objectives:**
# MAGIC - Navigate the Databricks workspace
# MAGIC - Understand cluster configuration
# MAGIC - Run basic Spark operations
# MAGIC - Use magic commands (`%sql`, `%md`, `%python`)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Cluster Configuration
# MAGIC 
# MAGIC Recommended cluster setup for this project:
# MAGIC | Setting | Value |
# MAGIC |---------|-------|
# MAGIC | Runtime | 14.3 LTS (Spark 3.5) |
# MAGIC | Node Type | Standard_DS3_v2 (or Community Edition default) |
# MAGIC | Workers | 1-2 (or single node for dev) |
# MAGIC | Autoscaling | Enabled |

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Workspace Basics — Magic Commands

# COMMAND ----------

# MAGIC %sql
# MAGIC -- SQL magic command: query directly
# MAGIC SELECT 'Healthcare Patient Flow Monitor' AS project_name,
# MAGIC        current_timestamp() AS run_time,
# MAGIC        spark_version() AS spark_version

# COMMAND ----------

# Python is the default language
print("🏥 Hospital Bed Occupancy Monitor — Databricks Edition")
print(f"Spark Version: {spark.version}")
print(f"Cluster: {spark.conf.get('spark.databricks.clusterUsageTags.clusterName', 'local')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Project Overview — Medallion Architecture
# MAGIC 
# MAGIC ```
# MAGIC ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌───────────┐
# MAGIC │  BRONZE  │───▶│  SILVER  │───▶│   GOLD   │───▶│ ANALYTICS │
# MAGIC │ Raw HL7  │    │ Cleaned  │    │ Occupancy│    │ Anomalies │
# MAGIC │ Events   │    │ Validated│    │ Metrics  │    │ Dashboard │
# MAGIC └──────────┘    └──────────┘    └──────────┘    └───────────┘
# MAGIC ```
# MAGIC 
# MAGIC **Data Sources:** HL7 ADT Messages (Admit/Discharge/Transfer)
# MAGIC - `ADT_A01` — Patient Admission
# MAGIC - `ADT_A02` — Patient Transfer
# MAGIC - `ADT_A03` — Patient Discharge

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Basic Spark Operations — Hospital Data

# COMMAND ----------

from pyspark.sql.types import *
from pyspark.sql.functions import *

# Define the HL7 event schema
event_schema = StructType([
    StructField("message_id", StringType(), False),
    StructField("event_type", StringType(), False),
    StructField("patient_id", StringType(), False),
    StructField("ward_id", StringType(), False),
    StructField("ward_name", StringType(), True),
    StructField("bed_id", StringType(), False),
    StructField("timestamp", StringType(), False),
    StructField("diagnosis_category", StringType(), True),
    StructField("age_group", StringType(), True),
    StructField("priority", StringType(), True),
    StructField("transfer_from_ward", StringType(), True),
    StructField("transfer_from_bed", StringType(), True),
])

print("✅ Schema defined for HL7 ADT events")
print(f"   Fields: {len(event_schema.fields)}")
for f in event_schema.fields:
    print(f"   - {f.name}: {f.dataType.simpleString()} (nullable={f.nullable})")

# COMMAND ----------

# Create sample hospital data
from datetime import datetime, timedelta
import random

random.seed(42)
wards = [
    ("W-001", "ICU East", 20), ("W-002", "ICU West", 20),
    ("W-003", "General A", 40), ("W-004", "General B", 40),
    ("W-005", "Pediatrics", 25), ("W-006", "Emergency", 30),
    ("W-007", "Oncology", 15)
]

rows = []
for i in range(500):
    w = random.choice(wards)
    evt = random.choice(["ADT_A01", "ADT_A02", "ADT_A03"])
    ts = datetime.now() - timedelta(hours=random.randint(0, 168))
    rows.append((
        f"msg-{i:05d}", evt, f"P-{i:06d}", w[0], w[1],
        f"B-{w[0][-3:]}-{random.randint(1, w[2]):03d}",
        ts.isoformat(),
        random.choice(["cardiac", "respiratory", "trauma", "neurological"]),
        random.choice(["adult", "pediatric", "geriatric"]),
        random.choice(["emergency", "elective", "transfer"]),
        None, None
    ))

sample_df = spark.createDataFrame(rows, event_schema)
print(f"✅ Created {sample_df.count()} sample HL7 events")

# COMMAND ----------

# Basic DataFrame operations
display(sample_df.limit(10))

# COMMAND ----------

# Aggregation: events per ward
ward_summary = (sample_df
    .groupBy("ward_id", "ward_name")
    .agg(
        count("*").alias("total_events"),
        count(when(col("event_type") == "ADT_A01", True)).alias("admissions"),
        count(when(col("event_type") == "ADT_A03", True)).alias("discharges"),
        count(when(col("event_type") == "ADT_A02", True)).alias("transfers")
    )
    .orderBy("ward_id"))

display(ward_summary)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Working with Temporary Views

# COMMAND ----------

sample_df.createOrReplaceTempView("hospital_events")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Query the temp view using SQL
# MAGIC SELECT ward_name,
# MAGIC        event_type,
# MAGIC        COUNT(*) AS event_count,
# MAGIC        COUNT(DISTINCT patient_id) AS unique_patients
# MAGIC FROM hospital_events
# MAGIC GROUP BY ward_name, event_type
# MAGIC ORDER BY ward_name, event_type

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Databricks Utilities (dbutils)

# COMMAND ----------

# List available dbutils
# dbutils.fs.ls("/")  # List DBFS root
# dbutils.notebook.exit("Success")  # Exit notebook with value
# dbutils.secrets.list("hospital-scope")  # List secrets

print("📋 Key dbutils commands:")
print("  dbutils.fs.ls('/')          — List files in DBFS")
print("  dbutils.fs.mkdirs('/path')  — Create directory")
print("  dbutils.fs.cp(src, dst)     — Copy files")
print("  dbutils.notebook.run(path)  — Run another notebook")
print("  dbutils.secrets.get(scope, key) — Get secret value")
print("  dbutils.widgets.text(name, default) — Create widget")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Summary
# MAGIC 
# MAGIC In this notebook we covered:
# MAGIC 1. Cluster configuration for the hospital monitoring project
# MAGIC 2. Magic commands (`%sql`, `%md`, `%python`)
# MAGIC 3. HL7 ADT event schema definition
# MAGIC 4. Basic Spark DataFrame operations
# MAGIC 5. Temporary views and SQL queries
# MAGIC 6. Databricks utilities overview
# MAGIC 
# MAGIC **Next →** `02_Working_with_DataFrames.py`
