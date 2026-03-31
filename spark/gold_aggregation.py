"""
Gold Layer — Occupancy Aggregation
Computes current occupancy, hourly snapshots, 7-day baseline, daily summary.
Writes to Parquet + SQLite.
"""
import os, json, sqlite3, logging
from datetime import datetime, timedelta
from pyspark.sql import SparkSession, DataFrame, Window
from pyspark.sql.functions import (
    col, count, sum as spark_sum, avg, stddev, min as spark_min, max as spark_max,
    when, lit, hour, to_timestamp, to_date, row_number, current_timestamp,
    round as spark_round, coalesce, expr, udf
)
from pyspark.sql.types import IntegerType

logger = logging.getLogger("spark.gold")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SILVER_PATH = os.path.join(BASE_DIR, "data", "silver")
GOLD_PATH = os.path.join(BASE_DIR, "data", "gold")
GOLD_OCC_PATH = os.path.join(GOLD_PATH, "occupancy_hourly")
GOLD_BASE_PATH = os.path.join(GOLD_PATH, "baseline_7day")
GOLD_DAILY_PATH = os.path.join(GOLD_PATH, "daily_summary")
DB_PATH = os.path.join(BASE_DIR, "data", "hospital.db")
WARD_CFG = os.path.join(BASE_DIR, "config", "wards.json")

def get_spark(name="HospitalGold"):
    return (SparkSession.builder.appName(name).master("local[*]")
        .config("spark.sql.adaptive.enabled","true")
        .config("spark.sql.parquet.compression.codec","snappy")
        .config("spark.driver.memory","2g").getOrCreate())

def load_ward_beds():
    with open(WARD_CFG) as f: cfg = json.load(f)
    return {w["ward_id"]: w["total_beds"] for w in cfg["wards"]}

def load_ward_names():
    with open(WARD_CFG) as f: cfg = json.load(f)
    return {w["ward_id"]: w["ward_name"] for w in cfg["wards"]}

def read_silver(spark, date_filter=None):
    df = spark.read.parquet(SILVER_PATH)
    if date_filter: df = df.filter(col("event_date") == date_filter)
    return df

def compute_current_occupancy(silver_df, ward_beds):
    logger.info("Computing current occupancy...")
    spark = silver_df.sparkSession
    beds_bc = spark.sparkContext.broadcast(ward_beds)

    @udf(IntegerType())
    def get_beds(wid): return beds_bc.value.get(wid, 0)

    occ = (silver_df.groupBy("ward_id","ward_name").agg(
        count(when(col("event_type")=="ADT_A01",True)).alias("total_admits"),
        count(when(col("event_type")=="ADT_A03",True)).alias("total_discharges"),
    ).withColumn("occupied_beds", col("total_admits")-col("total_discharges"))
     .withColumn("total_beds", get_beds(col("ward_id")))
     .withColumn("occupied_beds",
        when(col("occupied_beds")<0,lit(0))
        .when(col("occupied_beds")>col("total_beds"),col("total_beds"))
        .otherwise(col("occupied_beds")))
     .withColumn("occupancy_percent",
        spark_round((col("occupied_beds")/col("total_beds"))*100,1))
     .withColumn("status",
        when(col("occupancy_percent")>=95,lit("critical"))
        .when(col("occupancy_percent")>=85,lit("warning"))
        .when(col("occupancy_percent")>=70,lit("elevated"))
        .otherwise(lit("normal"))))
    return occ

def compute_hourly_snapshots(silver_df, ward_beds):
    logger.info("Computing hourly snapshots...")
    spark = silver_df.sparkSession
    beds_bc = spark.sparkContext.broadcast(ward_beds)

    @udf(IntegerType())
    def get_beds(wid): return beds_bc.value.get(wid, 0)

    ev = (silver_df
        .withColumn("event_ts", to_timestamp(col("timestamp")))
        .withColumn("snapshot_hour", expr("date_trunc('hour', event_ts)")))
    hc = (ev.groupBy("ward_id","ward_name","snapshot_hour").agg(
        count(when(col("event_type")=="ADT_A01",True)).alias("admits_count"),
        count(when(col("event_type")=="ADT_A03",True)).alias("discharges_count"),
        count(when(col("event_type")=="ADT_A02",True)).alias("transfers_count")))
    w = Window.partitionBy("ward_id").orderBy("snapshot_hour").rowsBetween(
        Window.unboundedPreceding, Window.currentRow)
    hc = (hc
        .withColumn("cum_a", spark_sum("admits_count").over(w))
        .withColumn("cum_d", spark_sum("discharges_count").over(w))
        .withColumn("net", col("cum_a")-col("cum_d"))
        .withColumn("total_beds", get_beds(col("ward_id")))
        .withColumn("occupied_beds",
            when(col("net")<0,lit(0))
            .when(col("net")>col("total_beds"),col("total_beds"))
            .otherwise(col("net")))
        .withColumn("occupancy_percent",
            spark_round((col("occupied_beds")/col("total_beds"))*100,1))
        .drop("cum_a","cum_d","net"))
    return hc

def compute_7day_baseline(hourly_df):
    logger.info("Computing 7-day baseline...")
    bl = hourly_df.withColumn("hour_of_day", hour(col("snapshot_hour")))
    w = Window.partitionBy("ward_id","hour_of_day").orderBy("snapshot_hour").rowsBetween(-168,0)
    bl = (bl
        .withColumn("baseline_avg", spark_round(avg("occupancy_percent").over(w),1))
        .withColumn("baseline_std", spark_round(coalesce(stddev("occupancy_percent").over(w),lit(0.0)),2))
        .withColumn("delta", spark_round(col("occupancy_percent")-col("baseline_avg"),1))
        .withColumn("trend",
            when(col("delta")>5,lit("rising"))
            .when(col("delta")<-5,lit("falling"))
            .otherwise(lit("stable"))))
    return bl

def compute_daily_summary(hourly_df):
    logger.info("Computing daily summaries...")
    d = (hourly_df.withColumn("report_date", to_date(col("snapshot_hour")))
        .groupBy("ward_id","ward_name","report_date").agg(
            spark_round(avg("occupancy_percent"),1).alias("avg_occ"),
            spark_round(spark_max("occupancy_percent"),1).alias("peak_occ"),
            spark_round(spark_min("occupancy_percent"),1).alias("min_occ"),
            spark_sum("admits_count").alias("total_admits"),
            spark_sum("discharges_count").alias("total_discharges"),
            count(when(col("occupancy_percent")>=85,True)).alias("sla_breach_hours")))
    return d

def write_parquet(df, path, pcols=None):
    os.makedirs(path, exist_ok=True)
    w = df.write.mode("overwrite")
    if pcols: w = w.partitionBy(*pcols)
    w.parquet(path)

def write_sqlite(df, table, mode="replace"):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    pdf = df.toPandas()
    conn = sqlite3.connect(DB_PATH)
    pdf.to_sql(table, conn, if_exists=mode, index=False)
    conn.close()

def write_current_occ_sqlite(occ_df):
    pdf = occ_df.toPandas()
    conn = sqlite3.connect(DB_PATH)
    now = datetime.now().isoformat()
    for _, r in pdf.iterrows():
        conn.execute("""INSERT OR REPLACE INTO ward_occupancy_current
            (ward_id,ward_name,occupied_beds,total_beds,occupancy_percent,status,updated_at)
            VALUES(?,?,?,?,?,?,?)""",
            (r["ward_id"],r["ward_name"],int(r["occupied_beds"]),
             int(r["total_beds"]),float(r["occupancy_percent"]),r["status"],now))
    conn.commit(); conn.close()

def run_gold(spark, date_filter=None):
    logger.info("="*60+"\n🥇 Gold Layer Aggregation\n"+"="*60)
    wb = load_ward_beds()
    sdf = read_silver(spark, date_filter)
    if sdf.count()==0: logger.warning("No data"); return
    occ = compute_current_occupancy(sdf, wb)
    write_current_occ_sqlite(occ)
    hourly = compute_hourly_snapshots(sdf, wb)
    write_parquet(hourly, GOLD_OCC_PATH, ["ward_id"])
    write_sqlite(hourly.select("ward_id","ward_name","snapshot_hour",
        "occupied_beds","total_beds","occupancy_percent",
        "admits_count","discharges_count"), "ward_occupancy_hourly")
    bl = compute_7day_baseline(hourly)
    write_parquet(bl, GOLD_BASE_PATH, ["ward_id"])
    bl_sum = (bl.groupBy("ward_id","ward_name","hour_of_day").agg(
        spark_round(avg("baseline_avg"),1).alias("baseline_avg_occupancy"),
        spark_round(avg("baseline_std"),2).alias("baseline_std_occupancy"),
        count("*").alias("sample_count")))
    write_sqlite(bl_sum, "ward_baseline")
    daily = compute_daily_summary(hourly)
    write_parquet(daily, GOLD_DAILY_PATH, ["ward_id"])
    write_sqlite(daily, "ward_occupancy_daily")
    occ.show(truncate=False)
    logger.info("✅ Gold complete")

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)
    p = argparse.ArgumentParser()
    p.add_argument("--date", default=None)
    a = p.parse_args()
    s = get_spark(); run_gold(s, a.date); s.stop()
