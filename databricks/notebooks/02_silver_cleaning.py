# Databricks notebook source
# MAGIC %md
# MAGIC # 03 — Gold Aggregation (Occupancy Analytics)
# MAGIC Window functions, running occupancy, 7-day baselines.
# MAGIC **Showcases:** Complex window functions, Delta Lake, analytical queries.

# COMMAND ----------

from pyspark.sql.functions import *
from pyspark.sql.window import Window

bronze_path = "/mnt/hospital/bronze"
silver_path = "/mnt/hospital/silver"

# Read Bronze Delta
bronze_df = spark.read.format("delta").load(bronze_path)
print(f"Bronze records: {bronze_df.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Rules

# COMMAND ----------

VALID_EVENTS = ["ADT_A01", "ADT_A02", "ADT_A03"]
VALID_WARDS = {"ICU EAST":"ICU East","ICU WEST":"ICU West","GENERAL A":"General A",
               "GENERAL B":"General B","PEDIATRICS":"Pediatrics",
               "EMERGENCY":"Emergency","ONCOLOGY":"Oncology"}

# Rule 1: Reject null patient_id
df = bronze_df.filter(col("patient_id").isNotNull())
r1_rejected = bronze_df.count() - df.count()

# Rule 2: Valid event types only
df = df.filter(col("event_type").isin(VALID_EVENTS))
r2_rejected = bronze_df.count() - r1_rejected - df.count()

# Rule 3: Flag late arrivals (>24h old)
df = df.withColumn("event_ts", to_timestamp(col("timestamp")))
df = df.withColumn("is_late_arrival",
    when((unix_timestamp(current_timestamp()) - unix_timestamp(col("event_ts"))) > 86400, True)
    .otherwise(False))

# Rule 4: Standardize ward names
for raw, clean in VALID_WARDS.items():
    df = df.withColumn("ward_name",
        when(upper(trim(col("ward_name"))) == raw, lit(clean)).otherwise(col("ward_name")))

# Rule 5: Deduplicate admits
w = Window.partitionBy("patient_id").orderBy(col("timestamp").desc())
admits = df.filter(col("event_type") == "ADT_A01").withColumn("rn", row_number().over(w)).filter(col("rn")==1).drop("rn")
non_admits = df.filter(col("event_type") != "ADT_A01")
df = admits.unionByName(non_admits, allowMissingColumns=True)

# Add processing metadata
silver_df = df.withColumn("processed_at", current_timestamp()).withColumn("event_hour", hour(col("event_ts")))

print(f"Rule 1 rejected: {r1_rejected}")
print(f"Rule 2 rejected: {r2_rejected}")
print(f"Silver records: {silver_df.count()}")

# COMMAND ----------

# Write to Delta with OPTIMIZE
silver_df.write.format("delta").mode("overwrite").partitionBy("event_date","ward_id").save(silver_path)

# OPTIMIZE with ZORDER for fast queries
spark.sql(f"OPTIMIZE delta.`{silver_path}` ZORDER BY (ward_id, timestamp)")
print("✅ Silver Delta table created and optimized")

# COMMAND ----------

# Register table
spark.sql(f"CREATE TABLE IF NOT EXISTS hospital.silver USING DELTA LOCATION '{silver_path}'")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Report

# COMMAND ----------

display(spark.sql(f"""
    SELECT ward_name, event_type, COUNT(*) as count,
           SUM(CASE WHEN is_late_arrival THEN 1 ELSE 0 END) as late_arrivals
    FROM delta.`{silver_path}`
    GROUP BY ward_name, event_type
    ORDER BY ward_name, event_type
"""))
