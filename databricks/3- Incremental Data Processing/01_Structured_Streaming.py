# Databricks notebook source
# MAGIC %md
# MAGIC # 🌊 Incremental Processing — Auto Loader & Structured Streaming
# MAGIC 
# MAGIC Real-time ingestion of hospital HL7 events.
# MAGIC Demonstrates how Databricks handles continuous data streams robustly using 
# MAGIC Auto Loader and Structured Streaming with Delta Lake.
# MAGIC 
# MAGIC **Learning Objectives:**
# MAGIC - Use Databricks Auto Loader (`cloudFiles`)
# MAGIC - Set up schema inference and evolution
# MAGIC - Use checkpointing for exactly-once processing
# MAGIC - Perform streaming aggregations

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Setup & Simulated Landing Zone

# COMMAND ----------

from pyspark.sql.types import *
from pyspark.sql.functions import *
import time

# Create simulated landing zone and checkpoint directories
landing_zone = "/tmp/hospital/landing"
checkpoint_dir = "/tmp/hospital/checkpoints/bronze_stream"

dbutils.fs.rm(landing_zone, True)
dbutils.fs.rm(checkpoint_dir, True)
dbutils.fs.mkdirs(landing_zone)

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
# MAGIC ## 2. Start Auto Loader (Structured Streaming)

# COMMAND ----------

# MAGIC %md
# MAGIC * `cloudFiles` format automatically scales and handles new files efficiently
# MAGIC * `cloudFiles.schemaLocation` stores inferred schemas handling schema evolution

# COMMAND ----------

# Start reading the stream from the landing zone using Auto Loader
raw_stream = (spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "json")
    # Schema inference allows it to automatically detect schema, but we'll enforce ours
    .option("cloudFiles.schemaLocation", checkpoint_dir + "/schema")
    .schema(event_schema)
    .load(landing_zone))

# Add streaming metadata
bronze_stream = (raw_stream
    .withColumn("ingestion_timestamp", current_timestamp())
    .withColumn("event_date", to_date(col("timestamp")))
    .withColumn("source_file", input_file_name()))

# Start writing the stream to a Delta table
streaming_query = (bronze_stream.writeStream
    .format("delta")
    .outputMode("append")
    .partitionBy("event_date", "ward_id")
    .option("checkpointLocation", checkpoint_dir + "/data")
    .table("hospital_lakehouse.bronze_streaming_events"))

print("✅ Auto Loader Stream Started. Waiting for files...")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Simulate Arriving Data (JSON files)

# COMMAND ----------

from datetime import datetime
import json
import random

# Method to write simulated files to the landing zone
def write_simulated_batch(batch_id, num_records=50):
    wards = [("W-001", "ICU East"), ("W-002", "ICU West"), ("W-006", "Emergency")]
    
    events = []
    for i in range(num_records):
        w = random.choice(wards)
        ts = datetime.now()
        event = {
            "message_id": f"stream-{batch_id}-{i:04d}",
            "event_type": random.choice(["ADT_A01", "ADT_A02", "ADT_A03"]),
            "patient_id": f"P-STREAM-{random.randint(1000, 2000)}",
            "ward_id": w[0],
            "ward_name": w[1],
            "bed_id": f"B-{w[0][-3:]}-001",
            "timestamp": ts.isoformat(),
            "priority": "emergency"
        }
        events.append(event)
        
    # Write to a single JSON file
    file_path = f"{landing_zone}/batch_{batch_id}.json"
    with open(f"/dbfs{file_path}", "w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")
            
    print(f"Written batch {batch_id} to {file_path} ({num_records} records)")

# COMMAND ----------

# Simulate 3 continuous batches arriving over time
for b in range(1, 4):
    write_simulated_batch(b, 100)
    time.sleep(5)  # Let the stream process it

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Check if records have landed in the Delta table
# MAGIC SELECT ward_name, event_type, COUNT(*) 
# MAGIC FROM hospital_lakehouse.bronze_streaming_events
# MAGIC GROUP BY ward_name, event_type

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Streaming Aggregations
# MAGIC 
# MAGIC We can read from our Silver batch table or stream live data to calculate 
# MAGIC real-time statistics like the running minimum, maximum, and average occupancy.

# COMMAND ----------

# Let's read from the streaming Bronze table
live_bronze = spark.readStream.table("hospital_lakehouse.bronze_streaming_events")

# Calculate rolling admissions per ward over 10 minute windows
windowed_admissions = (live_bronze
    .filter(col("event_type") == "ADT_A01")
    .withColumn("event_time", to_timestamp(col("timestamp")))
    .withWatermark("event_time", "15 minutes") # Handle late arriving data
    .groupBy(
        window(col("event_time"), "10 minutes"),
        "ward_name"
    )
    .count()
    .alias("new_admissions"))

# Output to memory sink for real-time visualization in the notebook
display_query = (windowed_admissions.writeStream
    .format("memory")
    .queryName("live_admissions")
    .outputMode("complete")
    .start())

# COMMAND ----------

# MAGIC %md
# MAGIC *Note: The above streaming queries run continuously.*
# MAGIC *To stop them cleanly before exiting, we use `streaming_query.stop()`*

# COMMAND ----------

# Stop the streams
streaming_query.stop()
display_query.stop()
print("🛑 Streaming stopped")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Summary
# MAGIC 
# MAGIC In this notebook we demonstrated:
# MAGIC 1. Auto Loader (`cloudFiles`) to read JSON files automatically as they arrive
# MAGIC 2. Managing Checkpoints for exactly-once guarantees
# MAGIC 3. Inserting a continuous stream into a Delta Bronze table
# MAGIC 4. Streaming Aggregations with Watermarks for late data handling
# MAGIC 
# MAGIC **Next →** 4- Production Pipelines
