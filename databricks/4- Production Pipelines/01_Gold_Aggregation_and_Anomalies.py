# Databricks notebook source
# MAGIC %md
# MAGIC # 📈 Production Pipelines — Gold Layer & Anomaly Detection
# MAGIC 
# MAGIC Final stage of the Medallion architecture. 
# MAGIC Calculates business-level metrics (occupancy, baselines) and detects anomalies.
# MAGIC 
# MAGIC **Learning Objectives:**
# MAGIC - Generate Gold layer data for Dashboards/BI tools
# MAGIC - Complex PySpark Window operations
# MAGIC - Z-Score Statistical Anomaly Detection
# MAGIC - Orchestration readiness for Databricks Jobs

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Setup & Read Silver Data

# COMMAND ----------

from pyspark.sql.functions import *
from pyspark.sql.window import Window

# Read from Silver Delta table
try:
    silver_df = spark.read.table("hospital_lakehouse.silver_events")
    wards_df = spark.read.table("hospital_lakehouse.wards")
    print(f"Loaded {silver_df.count()} records from Silver.")
except:
    print("Run previous notebooks to generate Silver data.")

# Set up Gold Paths for the lakehouse database
# (We could also use Delta Tables)
gold_occ_table = "hospital_lakehouse.gold_occupancy_hourly"
gold_baseline_table = "hospital_lakehouse.gold_baseline_7day"
gold_anomaly_table = "hospital_lakehouse.gold_anomaly_flags"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Hourly Snapshot (Occupancy Metrics)

# COMMAND ----------

# Group events per ward per 1 hour window
hourly_events = (silver_df
    .withColumn("snapshot_hour", date_trunc("hour", col("event_ts")))
    .groupBy("ward_id", "ward_name", "snapshot_hour")
    .agg(
        count(when(col("event_type") == "ADT_A01", True)).alias("admits"),
        count(when(col("event_type") == "ADT_A03", True)).alias("discharges"),
        count(when(col("event_type") == "ADT_A02", True)).alias("transfers")
    ))

# Cumulative sum using unbounded window
w_cum = Window.partitionBy("ward_id").orderBy("snapshot_hour").rowsBetween(Window.unboundedPreceding, Window.currentRow)

hourly_occupancy = (hourly_events
    .withColumn("cum_admits", sum("admits").over(w_cum))
    .withColumn("cum_discharges", sum("discharges").over(w_cum))
    .withColumn("net_occupancy", col("cum_admits") - col("cum_discharges"))
    .join(wards_df.select("ward_id", "total_beds"), on="ward_id", how="left")
    # Cap occupancy between 0 and total beds 
    .withColumn("occupied_beds",
        when(col("net_occupancy") < 0, 0)
        .when(col("net_occupancy") > col("total_beds"), col("total_beds"))
        .otherwise(col("net_occupancy")))
    .withColumn("occupancy_pct", round((col("occupied_beds") / col("total_beds")) * 100, 1)))

# Write to Gold Delta table
hourly_occupancy.write.format("delta").mode("overwrite").partitionBy("ward_id").saveAsTable(gold_occ_table)
print("✅ Gold Hourly Occupancy table created")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Rolling 7-Day Baseline

# COMMAND ----------

# Calculate baseline mean and standard deviation for the last 168 hours (7 days)
baseline_input = hourly_occupancy.withColumn("hour_of_day", hour(col("snapshot_hour")))

# Window: previous 168 hours up to previous hour (-1)
w_baseline = Window.partitionBy("ward_id", "hour_of_day").orderBy("snapshot_hour").rowsBetween(-168, -1)

baseline = (baseline_input
    .withColumn("baseline_avg", round(avg("occupancy_pct").over(w_baseline), 1))
    .withColumn("baseline_std", round(coalesce(stddev("occupancy_pct").over(w_baseline), lit(0.0)), 2)))

baseline.write.format("delta").mode("overwrite").partitionBy("ward_id").saveAsTable(gold_baseline_table)
print("✅ Gold Rolling Baseline table created")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Anomaly Detection (Z-Score)
# MAGIC 
# MAGIC Detect outbreak-level admission spikes per ward using Statistical Z-score.
# MAGIC $$ Z = \frac{(x - \mu)}{\sigma} $$

# COMMAND ----------

THRESHOLD = 2.5 # Anything further than 2.5 Standard Deviations is flagged as anomaly

w_anomaly = Window.partitionBy("ward_id", "hour_of_day").orderBy("snapshot_hour").rowsBetween(-168, -1)

anomalies = (hourly_occupancy.withColumn("hour_of_day", hour(col("snapshot_hour")))
    .withColumn("rolling_mean", round(avg("admits").over(w_anomaly), 2))
    .withColumn("rolling_std", round(coalesce(stddev("admits").over(w_anomaly), lit(1.0)), 2))
    # Prevent divide by zero if std is 0
    .withColumn("rolling_std", when(col("rolling_std") == 0, lit(1.0)).otherwise(col("rolling_std")))
    .withColumn("z_score", round((col("admits") - col("rolling_mean")) / col("rolling_std"), 3))
    # Flag Anomalies!
    .withColumn("is_anomaly", abs(col("z_score")) > lit(THRESHOLD))
    .withColumn("threshold_used", lit(THRESHOLD))
    .select("ward_id", "ward_name", "snapshot_hour", "hour_of_day", 
            "z_score", "is_anomaly", "rolling_mean", "rolling_std", "admits", "threshold_used"))

# Save table
anomalies.write.format("delta").mode("overwrite").saveAsTable(gold_anomaly_table)

flagged_count = anomalies.filter(col("is_anomaly") == True).count()
print(f"✅ Anomaly Detection Done. Flagged {flagged_count} spikes.")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Visualize top anomalies
# MAGIC SELECT ward_name, snapshot_hour, admits, rolling_mean, z_score
# MAGIC FROM hospital_lakehouse.gold_anomaly_flags
# MAGIC WHERE is_anomaly = true
# MAGIC ORDER BY z_score DESC
# MAGIC LIMIT 10

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Data Quality Dashboard (Gold Layer)
# MAGIC 
# MAGIC Using SQL to create business intelligence queries directly in the Databricks UI.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Query: What is the average occupancy per ward?
# MAGIC SELECT ward_name, 
# MAGIC        AVG(occupancy_pct) as avg_occupancy,
# MAGIC        MAX(occupancy_pct) as max_occupancy
# MAGIC FROM hospital_lakehouse.gold_occupancy_hourly
# MAGIC GROUP BY ward_name
# MAGIC ORDER BY avg_occupancy DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Summary & Orchestration Readiness
# MAGIC 
# MAGIC In this notebook we:
# MAGIC 1. Read Silver data to calculate **Business logic** (Gold metrics).
# MAGIC 2. Used **Advanced Spark Window Functions** to build a statistical baseline over a rolling 7-day period.
# MAGIC 3. Evaluated Data against the baseline using the **Z-Score Formula** to flag Outbreaks/Anomalies.
# MAGIC 4. Generated the final tables for **Business Intelligence** ready for connection to Power BI or Tableau.
# MAGIC 
# MAGIC ### Orchestrating as a Production Job
# MAGIC This notebook is typically the final task in a Pipeline DAG.
# MAGIC ```
# MAGIC [01_Introductions] -> [02_Working_DFs] -> [Lakehouse_Architecture] -> [Structured_Streaming]
# MAGIC ```
# MAGIC In Databricks, use **Workflows (Jobs)** to schedule these notebooks to run sequentially, every 15 minutes!
