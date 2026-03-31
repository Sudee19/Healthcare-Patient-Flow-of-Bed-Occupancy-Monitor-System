# Databricks notebook source
# MAGIC %md
# MAGIC # 03 — Gold Aggregation (Occupancy Analytics)
# MAGIC Window functions, running occupancy, 7-day baselines.
# MAGIC **Showcases:** Complex window functions, Delta Lake, analytical queries.

# COMMAND ----------

from pyspark.sql.functions import *
from pyspark.sql.window import Window

silver_path = "/mnt/hospital/silver"
gold_occupancy_path = "/mnt/hospital/gold/occupancy_hourly"
gold_baseline_path = "/mnt/hospital/gold/baseline_7day"
gold_daily_path = "/mnt/hospital/gold/daily_summary"

silver = spark.read.format("delta").load(silver_path)

# Ward bed config
ward_beds = {"W-001":20,"W-002":20,"W-003":40,"W-004":40,"W-005":25,"W-006":30,"W-007":15}
beds_df = spark.createDataFrame([(k,v) for k,v in ward_beds.items()], ["ward_id","capacity"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Hourly Occupancy Snapshots

# COMMAND ----------

# Event counts per ward per hour
hourly = (silver
    .withColumn("snapshot_hour", date_trunc("hour", col("event_ts")))
    .groupBy("ward_id","ward_name","snapshot_hour")
    .agg(
        count(when(col("event_type")=="ADT_A01",True)).alias("admits"),
        count(when(col("event_type")=="ADT_A03",True)).alias("discharges"),
        count(when(col("event_type")=="ADT_A02",True)).alias("transfers")))

# Running occupancy via window
w = Window.partitionBy("ward_id").orderBy("snapshot_hour").rowsBetween(Window.unboundedPreceding, Window.currentRow)
hourly = (hourly
    .withColumn("cum_admits", sum("admits").over(w))
    .withColumn("cum_discharges", sum("discharges").over(w))
    .withColumn("net", col("cum_admits")-col("cum_discharges"))
    .join(beds_df, "ward_id")
    .withColumn("occupied", when(col("net")<0,0).when(col("net")>col("capacity"),col("capacity")).otherwise(col("net")))
    .withColumn("occupancy_pct", round((col("occupied")/col("capacity"))*100,1)))

hourly.write.format("delta").mode("overwrite").partitionBy("ward_id").save(gold_occupancy_path)
spark.sql(f"OPTIMIZE delta.`{gold_occupancy_path}` ZORDER BY (ward_id, snapshot_hour)")
print("✅ Hourly occupancy written")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Rolling 7-Day Baseline

# COMMAND ----------

baseline_input = hourly.withColumn("hour_of_day", hour(col("snapshot_hour")))
bw = Window.partitionBy("ward_id","hour_of_day").orderBy("snapshot_hour").rowsBetween(-168, 0)

baseline = (baseline_input
    .withColumn("baseline_avg", round(avg("occupancy_pct").over(bw), 1))
    .withColumn("baseline_std", round(coalesce(stddev("occupancy_pct").over(bw), lit(0.0)), 2))
    .withColumn("delta", round(col("occupancy_pct") - col("baseline_avg"), 1))
    .withColumn("trend", when(col("delta")>5,"rising").when(col("delta")<-5,"falling").otherwise("stable")))

baseline.write.format("delta").mode("overwrite").partitionBy("ward_id").save(gold_baseline_path)
print("✅ 7-day baseline written")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Daily Summary

# COMMAND ----------

daily = (hourly
    .withColumn("report_date", to_date(col("snapshot_hour")))
    .groupBy("ward_id","ward_name","report_date")
    .agg(
        round(avg("occupancy_pct"),1).alias("avg_occ"),
        round(max("occupancy_pct"),1).alias("peak_occ"),
        round(min("occupancy_pct"),1).alias("min_occ"),
        sum("admits").alias("total_admits"),
        sum("discharges").alias("total_discharges"),
        count(when(col("occupancy_pct")>=85,True)).alias("breach_hours")))

daily.write.format("delta").mode("overwrite").partitionBy("ward_id").save(gold_daily_path)
print("✅ Daily summary written")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Delta Lake Features Demo

# COMMAND ----------

# Time Travel: query data as it was before
spark.sql(f"DESCRIBE HISTORY delta.`{gold_occupancy_path}`").display()

# COMMAND ----------

# Query a previous version
# spark.read.format("delta").option("versionAsOf", 0).load(gold_occupancy_path).display()

# COMMAND ----------

display(hourly.orderBy("ward_id","snapshot_hour").limit(50))
