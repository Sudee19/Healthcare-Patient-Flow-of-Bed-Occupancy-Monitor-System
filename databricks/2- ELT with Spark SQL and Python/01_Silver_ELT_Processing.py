# Databricks notebook source
# MAGIC %md
# MAGIC # 🔄 ELT with Spark SQL and Python — Silver Layer
# MAGIC 
# MAGIC Data cleaning, validation, and deduplication for the Hospital Patient Flow Monitor.
# MAGIC Transforms Bronze (Raw) data into Silver (Cleaned) data.
# MAGIC 
# MAGIC **Learning Objectives:**
# MAGIC - Combine PySpark DataFrame API with Spark SQL
# MAGIC - Apply complex data quality rules
# MAGIC - Use Window functions for deduplication
# MAGIC - Perform conditional updates and MERGE operations

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Setup & Read Bronze Data

# COMMAND ----------

from pyspark.sql.functions import *
from pyspark.sql.window import Window

# Read from Bronze Delta table
try:
    bronze_df = spark.read.table("hospital_lakehouse.bronze_events")
    print(f"Loaded Bronze table: {bronze_df.count()} records")
except:
    print("Run the Bronze Lakehouse notebook first to generate data.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Data Quality Rules using PySpark

# COMMAND ----------

# MAGIC %md
# MAGIC ### Rule 1: Valid Event Types Only & Not Null Rules

# COMMAND ----------

VALID_EVENTS = ["ADT_A01", "ADT_A02", "ADT_A03"]

# Filter invalid event types and ensure patient ID isn't null
silver_step1 = bronze_df.filter(
    col("event_type").isin(VALID_EVENTS) &
    col("patient_id").isNotNull()
)

rejected_r1 = bronze_df.count() - silver_step1.count()
print(f"Rule 1 - Rejected {rejected_r1} invalid records")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Rule 2: Standardize Ward Names (Data Cleaning)

# COMMAND ----------

# Often systems have varied casing
VALID_WARDS = {
    "ICU EAST": "ICU East",
    "ICU WEST": "ICU West",
    "GENERAL A": "General A",
    "GENERAL B": "General B",
    "PEDIATRICS": "Pediatrics",
    "EMERGENCY": "Emergency",
    "ONCOLOGY": "Oncology"
}

# Apply standardizations
silver_step2 = silver_step1
for raw, clean in VALID_WARDS.items():
    silver_step2 = silver_step2.withColumn(
        "ward_name",
        when(upper(trim(col("ward_name"))) == raw, lit(clean))
        .otherwise(col("ward_name"))
    )

print("Rule 2 - Ward names standardized")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Rule 3: Deduplication using Window Functions

# COMMAND ----------

# Business logic: A patient can only be admitted (ADT_A01) once in a sequence.
# We'll take the latest admission record per patient if there's a duplicate.

# Window definition partitioned by patient, ordered by timestamp descending
w = Window.partitionBy("patient_id").orderBy(col("timestamp").desc())

# Separate admits and other events
admits = silver_step2.filter(col("event_type") == "ADT_A01")
non_admits = silver_step2.filter(col("event_type") != "ADT_A01")

# Deduplicate admits: take row 1 for each patient window
admits_deduped = (admits
    .withColumn("rn", row_number().over(w))
    .filter(col("rn") == 1)
    .drop("rn"))

# Recombine
silver_clean = admits_deduped.unionByName(non_admits, allowMissingColumns=True)

dedup_removed = admits.count() - admits_deduped.count()
print(f"Rule 3 - Removed {dedup_removed} duplicate admissions")

# COMMAND ----------

# Add processing metadata
silver_final = (silver_clean
    .withColumn("processed_at", current_timestamp())
    .withColumn("event_ts", to_timestamp(col("timestamp")))
    .withColumn("event_hour", hour(col("event_ts"))))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Write to Silver Delta Table

# COMMAND ----------

# Write to Silver layer
silver_final.write.format("delta") \
    .mode("overwrite") \
    .partitionBy("event_date", "ward_id") \
    .saveAsTable("hospital_lakehouse.silver_events")

print("✅ Silver table created successfully")

# COMMAND ----------

# Optimize the Silver table for query performance
spark.sql("OPTIMIZE hospital_lakehouse.silver_events ZORDER BY (ward_id, event_ts)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. PySpark SQL for Data Analysis

# COMMAND ----------

# MAGIC %sql
# MAGIC -- We can query the Delta table directly with SQL
# MAGIC SELECT ward_name, 
# MAGIC        event_type, 
# MAGIC        COUNT(*) as event_count,
# MAGIC        MIN(event_ts) as first_event,
# MAGIC        MAX(event_ts) as last_event
# MAGIC FROM hospital_lakehouse.silver_events
# MAGIC GROUP BY ward_name, event_type
# MAGIC ORDER BY ward_name, event_type

# COMMAND ----------

# MAGIC %md
# MAGIC ### Using SQL to Perform Merge (Upsert)

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Create a small table of manual corrections we want to apply to Silver
# MAGIC CREATE OR REPLACE TEMP VIEW manual_corrections AS
# MAGIC SELECT 
# MAGIC   'msg-00001' as message_id, 
# MAGIC   'ADT_A01' as event_type,
# MAGIC   'P-999999' as patient_id, 
# MAGIC   'W-001' as ward_id,
# MAGIC   'ICU East' as ward_name,
# MAGIC   'B-001-001' as bed_id,
# MAGIC   current_timestamp() as timestamp,
# MAGIC   current_date() as event_date;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- MERGE operation (Upsert) using SQL
# MAGIC MERGE INTO hospital_lakehouse.silver_events target
# MAGIC USING manual_corrections source
# MAGIC ON target.message_id = source.message_id
# MAGIC WHEN MATCHED THEN
# MAGIC   UPDATE SET target.patient_id = source.patient_id
# MAGIC WHEN NOT MATCHED THEN
# MAGIC   INSERT (message_id, event_type, patient_id, ward_id, ward_name, bed_id, timestamp, event_date)
# MAGIC   VALUES (source.message_id, source.event_type, source.patient_id, source.ward_id, source.ward_name, source.bed_id, source.timestamp, source.event_date)

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Summary
# MAGIC 
# MAGIC In this notebook we demonstrated:
# MAGIC 1. Data Cleaning using PySpark DataFrame API
# MAGIC 2. Window Functions for complex deduplication logic
# MAGIC 3. Adding metadata and optimizing Delta tables
# MAGIC 4. Using Spark SQL for aggregations
# MAGIC 5. Delta `MERGE` statements for upserts
# MAGIC 
# MAGIC **Next →** 3- Incremental Data Processing
