# Databricks notebook source
# MAGIC %md
# MAGIC # 03 — Gold Aggregation (Occupancy Analytics)
# MAGIC Window functions, running occupancy, 7-day baselines.
# MAGIC **Showcases:** Complex window functions, Delta Lake, analytical queries.

# COMMAND ----------

from pyspark.sql.types import *
from pyspark.sql.functions import *

# Schema for HL7 events
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

# COMMAND ----------

# MAGIC %md
# MAGIC ## Option A: AutoLoader (Simulated Incremental Ingestion)

# COMMAND ----------

# Using AutoLoader for incremental file ingestion
# In production this would point to ADLS Gen2
bronze_path = "/mnt/hospital/bronze"
checkpoint_path = "/mnt/hospital/checkpoints/bronze"

# Simulated: read from uploaded JSON or mounted ADLS
try:
    raw_df = (spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", checkpoint_path + "/schema")
        .schema(event_schema)
        .load("/mnt/hospital/raw/"))

    # Add ingestion metadata
    bronze_df = (raw_df
        .withColumn("ingestion_timestamp", current_timestamp())
        .withColumn("event_date", to_date(col("timestamp")))
        .withColumn("source_file", input_file_name()))

    # Write to Delta
    (bronze_df.writeStream
        .format("delta")
        .outputMode("append")
        .partitionBy("event_date", "ward_id")
        .option("checkpointLocation", checkpoint_path)
        .trigger(availableNow=True)
        .start(bronze_path))

    print("✅ AutoLoader Bronze ingestion started")
except Exception as e:
    print(f"AutoLoader not available, using batch mode: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Option B: Batch Mode (for demo/testing)

# COMMAND ----------

# Read from JSON file directly
try:
    raw_batch = spark.read.json("/mnt/hospital/raw/test_events.json", schema=event_schema)
except:
    # Create sample data for demonstration
    from datetime import datetime, timedelta
    import random

    rows = []
    wards = [("W-001","ICU East",20), ("W-002","ICU West",20), ("W-003","General A",40),
             ("W-004","General B",40), ("W-005","Pediatrics",25), ("W-006","Emergency",30),
             ("W-007","Oncology",15)]

    for i in range(5000):
        w = random.choice(wards)
        evt = random.choice(["ADT_A01","ADT_A02","ADT_A03"])
        ts = datetime.now() - timedelta(hours=random.randint(0,168))
        rows.append((f"msg-{i}", evt, f"P-{i:06d}", w[0], w[1],
                     f"B-{w[0][-3:]}-{random.randint(1,w[2]):03d}",
                     ts.isoformat(), random.choice(["cardiac","respiratory","trauma"]),
                     random.choice(["adult","pediatric","geriatric"]),
                     random.choice(["emergency","elective","transfer"]), None, None))

    raw_batch = spark.createDataFrame(rows, event_schema)
    print(f"✅ Created {raw_batch.count()} sample events")

# Add metadata and write to Delta
bronze_batch = (raw_batch
    .withColumn("ingestion_timestamp", current_timestamp())
    .withColumn("event_date", to_date(col("timestamp"))))

bronze_batch.write.format("delta").mode("overwrite").partitionBy("event_date","ward_id").save(bronze_path)
print(f"✅ Bronze Delta table created: {bronze_batch.count()} records")

# COMMAND ----------

# Register as table for SQL access
spark.sql(f"CREATE TABLE IF NOT EXISTS hospital.bronze USING DELTA LOCATION '{bronze_path}'")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Bronze Layer

# COMMAND ----------

display(spark.read.format("delta").load(bronze_path).limit(10))

# COMMAND ----------

# Delta Lake features: DESCRIBE HISTORY (Time Travel)
spark.sql(f"DESCRIBE HISTORY delta.`{bronze_path}`").display()
