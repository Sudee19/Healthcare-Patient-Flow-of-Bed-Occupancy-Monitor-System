# Databricks notebook source
# MAGIC %md
# MAGIC # 📊 Working with DataFrames — Hospital Event Processing
# MAGIC 
# MAGIC Deep dive into PySpark DataFrame operations using real hospital ADT events.
# MAGIC 
# MAGIC **Learning Objectives:**
# MAGIC - Create and manipulate DataFrames
# MAGIC - Apply transformations and actions
# MAGIC - Use column expressions and built-in functions
# MAGIC - Write and read different file formats

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Creating DataFrames — Multiple Methods

# COMMAND ----------

from pyspark.sql.types import *
from pyspark.sql.functions import *
from datetime import datetime, timedelta
import random

random.seed(42)

# Method 1: From Python list
wards_data = [
    ("W-001", "ICU East", 20, "critical"),
    ("W-002", "ICU West", 20, "critical"),
    ("W-003", "General A", 40, "general"),
    ("W-004", "General B", 40, "general"),
    ("W-005", "Pediatrics", 25, "specialty"),
    ("W-006", "Emergency", 30, "emergency"),
    ("W-007", "Oncology", 15, "specialty"),
]

wards_schema = StructType([
    StructField("ward_id", StringType()),
    StructField("ward_name", StringType()),
    StructField("total_beds", IntegerType()),
    StructField("ward_type", StringType()),
])

wards_df = spark.createDataFrame(wards_data, wards_schema)
print("✅ Wards DataFrame created")
display(wards_df)

# COMMAND ----------

# Method 2: Generate event data programmatically
event_schema = StructType([
    StructField("message_id", StringType()),
    StructField("event_type", StringType()),
    StructField("patient_id", StringType()),
    StructField("ward_id", StringType()),
    StructField("ward_name", StringType()),
    StructField("bed_id", StringType()),
    StructField("timestamp", StringType()),
    StructField("diagnosis_category", StringType()),
    StructField("age_group", StringType()),
    StructField("priority", StringType()),
])

rows = []
for i in range(2000):
    w = random.choice(wards_data)
    evt = random.choices(["ADT_A01", "ADT_A02", "ADT_A03"], weights=[45, 15, 40])[0]
    ts = datetime.now() - timedelta(hours=random.randint(0, 336))
    rows.append((
        f"msg-{i:05d}", evt, f"P-{random.randint(1, 500):06d}",
        w[0], w[1], f"B-{w[0][-3:]}-{random.randint(1, w[2]):03d}",
        ts.isoformat(),
        random.choice(["cardiac", "respiratory", "trauma", "neurological", "infection"]),
        random.choice(["adult", "pediatric", "geriatric"]),
        random.choice(["emergency", "elective", "transfer"])
    ))

events_df = spark.createDataFrame(rows, event_schema)
print(f"✅ Generated {events_df.count()} hospital events")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. DataFrame Transformations

# COMMAND ----------

# Select and rename columns
selected = events_df.select(
    col("message_id"),
    col("event_type").alias("event"),
    col("ward_name").alias("ward"),
    col("patient_id"),
    to_timestamp(col("timestamp")).alias("event_time")
)
display(selected.limit(5))

# COMMAND ----------

# Add computed columns
enriched = events_df.withColumns({
    "event_time": to_timestamp(col("timestamp")),
    "event_date": to_date(col("timestamp")),
    "event_hour": hour(to_timestamp(col("timestamp"))),
    "is_admission": when(col("event_type") == "ADT_A01", True).otherwise(False),
    "is_discharge": when(col("event_type") == "ADT_A03", True).otherwise(False),
})

display(enriched.select(
    "message_id", "event_type", "ward_name", 
    "event_date", "event_hour", "is_admission", "is_discharge"
).limit(10))

# COMMAND ----------

# Filter operations
icu_admissions = enriched.filter(
    (col("ward_name").contains("ICU")) &
    (col("is_admission") == True)
)
print(f"ICU Admissions: {icu_admissions.count()}")

emergency_events = enriched.filter(
    col("priority") == "emergency"
)
print(f"Emergency Priority Events: {emergency_events.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Aggregations

# COMMAND ----------

# Group by ward — admission/discharge summary
ward_stats = (enriched
    .groupBy("ward_id", "ward_name")
    .agg(
        count("*").alias("total_events"),
        count(when(col("is_admission"), True)).alias("admissions"),
        count(when(col("is_discharge"), True)).alias("discharges"),
        countDistinct("patient_id").alias("unique_patients"),
        min("event_time").alias("earliest_event"),
        max("event_time").alias("latest_event"),
    )
    .orderBy(col("total_events").desc()))

display(ward_stats)

# COMMAND ----------

# Hourly distribution
hourly_dist = (enriched
    .groupBy("event_hour")
    .agg(
        count("*").alias("event_count"),
        count(when(col("is_admission"), True)).alias("admissions"),
    )
    .orderBy("event_hour"))

display(hourly_dist)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Joins — Enrich Events with Ward Capacity

# COMMAND ----------

# Join events with ward configuration
events_with_capacity = enriched.join(
    wards_df.select("ward_id", "total_beds", "ward_type"),
    on="ward_id",
    how="left"
)

# Compute bed utilization per ward
utilization = (events_with_capacity
    .groupBy("ward_id", "ward_name", "total_beds", "ward_type")
    .agg(
        count(when(col("is_admission"), True)).alias("admits"),
        count(when(col("is_discharge"), True)).alias("discharges"),
    )
    .withColumn("net_occupancy", col("admits") - col("discharges"))
    .withColumn("net_occupancy", 
        when(col("net_occupancy") < 0, 0)
        .when(col("net_occupancy") > col("total_beds"), col("total_beds"))
        .otherwise(col("net_occupancy")))
    .withColumn("occupancy_pct", round((col("net_occupancy") / col("total_beds")) * 100, 1))
    .orderBy(col("occupancy_pct").desc()))

display(utilization)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Saving DataFrames

# COMMAND ----------

# Save as Delta table
events_with_capacity.write.format("delta").mode("overwrite").saveAsTable("hospital_events_enriched")
print("✅ Saved as Delta table: hospital_events_enriched")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Verify the saved table
# MAGIC SELECT ward_name, ward_type, event_type, COUNT(*) as cnt
# MAGIC FROM hospital_events_enriched
# MAGIC GROUP BY ward_name, ward_type, event_type
# MAGIC ORDER BY ward_name, event_type

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Summary
# MAGIC 
# MAGIC In this notebook we covered:
# MAGIC 1. Creating DataFrames from lists and schemas
# MAGIC 2. Column transformations (`withColumn`, `select`, `alias`)
# MAGIC 3. Filtering with complex conditions
# MAGIC 4. Aggregations (`groupBy`, `agg`, `count`, `countDistinct`)
# MAGIC 5. Joins for data enrichment
# MAGIC 6. Saving to Delta tables
# MAGIC 
# MAGIC **Next →** Module 1: Databricks Lakehouse Platform
