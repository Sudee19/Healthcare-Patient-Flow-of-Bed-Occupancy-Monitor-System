# Databricks notebook source
# MAGIC %md
# MAGIC # 04 — Anomaly Detection (Z-Score)
# MAGIC Detects outbreak-level admission spikes per ward.
# MAGIC **Showcases:** Statistical analysis in Spark, window functions, alerting logic.

# COMMAND ----------

from pyspark.sql.functions import *
from pyspark.sql.window import Window

gold_occ = "/mnt/hospital/gold/occupancy_hourly"
anomaly_path = "/mnt/hospital/gold/anomaly_flags"
THRESHOLD = 2.5

hourly = spark.read.format("delta").load(gold_occ)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Compute Z-Scores

# COMMAND ----------

# Rolling 7-day window per ward per hour-of-day
hourly_z = hourly.withColumn("hour_of_day", hour(col("snapshot_hour")))

w = Window.partitionBy("ward_id","hour_of_day").orderBy("snapshot_hour").rowsBetween(-168, -1)

anomalies = (hourly_z
    .withColumn("rolling_mean", round(avg("admits").over(w), 2))
    .withColumn("rolling_std", round(coalesce(stddev("admits").over(w), lit(1.0)), 2))
    .withColumn("rolling_std", when(col("rolling_std")==0, lit(1.0)).otherwise(col("rolling_std")))
    .withColumn("z_score", round((col("admits") - col("rolling_mean")) / col("rolling_std"), 3))
    .withColumn("is_anomaly", abs(col("z_score")) > THRESHOLD)
    .withColumn("threshold_used", lit(THRESHOLD))
    .select("ward_id","ward_name","snapshot_hour","hour_of_day",
            "z_score","is_anomaly","rolling_mean","rolling_std",
            "admits","threshold_used"))

anomalies.write.format("delta").mode("overwrite").save(anomaly_path)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Results Summary

# COMMAND ----------

total = anomalies.count()
flagged = anomalies.filter(col("is_anomaly")).count()
print(f"Total observations: {total}")
print(f"Anomalies detected: {flagged} ({flagged/max(total,1)*100:.1f}%)")

# COMMAND ----------

# Show flagged anomalies
display(anomalies.filter(col("is_anomaly")).orderBy(col("z_score").desc()).limit(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Anomaly Summary by Ward

# COMMAND ----------

display(anomalies.filter(col("is_anomaly"))
    .groupBy("ward_id","ward_name")
    .agg(count("*").alias("anomaly_count"),
         round(max("z_score"),2).alias("max_z_score"),
         round(avg("z_score"),2).alias("avg_z_score"))
    .orderBy(col("anomaly_count").desc()))
