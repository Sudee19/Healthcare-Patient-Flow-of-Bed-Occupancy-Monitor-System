"""
Bronze Layer — Raw Event Ingestion

Reads raw HL7 ADT events from Kafka (streaming) or JSON files (batch)
and writes them as unmodified Parquet files partitioned by date and ward.

This is the raw truth layer — no transformations applied.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, TimestampType
)
from pyspark.sql.functions import (
    col, from_json, to_date, current_timestamp, lit
)

logger = logging.getLogger("spark.bronze")

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRONZE_PATH = os.path.join(BASE_DIR, "data", "bronze")
CHECKPOINT_PATH = os.path.join(BASE_DIR, "data", "checkpoints", "bronze")
DEAD_LETTER_PATH = os.path.join(BASE_DIR, "data", "dead_letter")

# ─── Schema ──────────────────────────────────────────────────────────────────
HL7_EVENT_SCHEMA = StructType([
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


def get_spark_session(app_name: str = "HospitalBronze") -> SparkSession:
    """Create or get a SparkSession with optimized settings."""
    return (
        SparkSession.builder
        .appName(app_name)
        .master("local[*]")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.driver.memory", "2g")
        .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_PATH)
        .getOrCreate()
    )


def ingest_from_kafka(spark: SparkSession, kafka_servers: str = "localhost:9092",
                       topic: str = "hospital_adt_events"):
    """
    Structured streaming from Kafka → Bronze Parquet.
    Runs continuously until stopped.
    """
    logger.info(f"Starting Kafka structured streaming from {topic}...")

    # Read from Kafka
    kafka_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_servers)
        .option("subscribe", topic)
        .option("startingOffsets", "earliest")
        .option("failOnDataLoss", "false")
        .load()
    )

    # Parse JSON values
    parsed_df = (
        kafka_df
        .selectExpr("CAST(value AS STRING) as json_str", "timestamp as kafka_timestamp")
        .select(
            from_json(col("json_str"), HL7_EVENT_SCHEMA).alias("data"),
            col("kafka_timestamp").alias("ingestion_timestamp"),
            col("json_str")
        )
    )

    # Separate good records from bad (dead letter)
    good_records = (
        parsed_df
        .filter(col("data").isNotNull())
        .select(
            "data.*",
            col("ingestion_timestamp"),
            to_date(col("data.timestamp")).alias("event_date")
        )
    )

    bad_records = (
        parsed_df
        .filter(col("data").isNull())
        .select(
            col("json_str").alias("raw_event"),
            col("ingestion_timestamp"),
            current_timestamp().alias("error_timestamp"),
            lit("parse_failure").alias("error_reason")
        )
    )

    # Write good records to Bronze
    os.makedirs(BRONZE_PATH, exist_ok=True)
    bronze_query = (
        good_records.writeStream
        .format("parquet")
        .outputMode("append")
        .partitionBy("event_date", "ward_id")
        .option("path", BRONZE_PATH)
        .option("checkpointLocation", os.path.join(CHECKPOINT_PATH, "good"))
        .trigger(processingTime="10 seconds")
        .start()
    )

    # Write bad records to dead letter
    os.makedirs(DEAD_LETTER_PATH, exist_ok=True)
    dead_letter_query = (
        bad_records.writeStream
        .format("parquet")
        .outputMode("append")
        .option("path", DEAD_LETTER_PATH)
        .option("checkpointLocation", os.path.join(CHECKPOINT_PATH, "dead_letter"))
        .trigger(processingTime="30 seconds")
        .start()
    )

    logger.info("✅ Bronze streaming started. Awaiting termination...")
    bronze_query.awaitTermination()


def ingest_from_json(spark: SparkSession, json_path: str):
    """
    Batch ingestion from a JSON events file → Bronze Parquet.
    Used for testing and seeding historical data.
    """
    logger.info(f"Batch ingesting from {json_path}...")

    # Read JSON
    raw_df = spark.read.json(json_path, schema=HL7_EVENT_SCHEMA)

    # Add metadata columns
    bronze_df = (
        raw_df
        .withColumn("ingestion_timestamp", current_timestamp())
        .withColumn("event_date", to_date(col("timestamp")))
    )

    # Separate good and bad
    good_df = bronze_df.filter(
        col("message_id").isNotNull() &
        col("patient_id").isNotNull() &
        col("event_type").isNotNull()
    )

    bad_df = bronze_df.filter(
        col("message_id").isNull() |
        col("patient_id").isNull() |
        col("event_type").isNull()
    )

    # Write good records
    os.makedirs(BRONZE_PATH, exist_ok=True)
    (
        good_df.write
        .mode("append")
        .partitionBy("event_date", "ward_id")
        .parquet(BRONZE_PATH)
    )

    # Write bad records
    if bad_df.count() > 0:
        os.makedirs(DEAD_LETTER_PATH, exist_ok=True)
        (
            bad_df
            .withColumn("error_reason", lit("null_critical_field"))
            .write
            .mode("append")
            .parquet(DEAD_LETTER_PATH)
        )
        logger.warning(f"⚠️ {bad_df.count()} malformed records sent to dead letter")

    logger.info(f"✅ Bronze ingestion complete: {good_df.count()} records written")
    logger.info(f"   Partition path: {BRONZE_PATH}")

    return good_df.count()


def verify_bronze(spark: SparkSession):
    """Verify Bronze layer data integrity."""
    logger.info("Verifying Bronze layer...")

    if not os.path.exists(BRONZE_PATH):
        logger.error("❌ Bronze path does not exist!")
        return False

    df = spark.read.parquet(BRONZE_PATH)
    total = df.count()
    partitions = df.select("event_date", "ward_id").distinct().count()

    logger.info(f"  Total records: {total}")
    logger.info(f"  Unique partitions: {partitions}")
    logger.info(f"  Schema:")
    df.printSchema()

    # Check for nulls in critical fields
    for field in ["message_id", "patient_id", "event_type", "ward_id", "timestamp", "bed_id"]:
        null_count = df.filter(col(field).isNull()).count()
        if null_count > 0:
            logger.warning(f"  ⚠️ {null_count} null values in {field}")
        else:
            logger.info(f"  ✅ {field}: no nulls")

    return True


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s")

    parser = argparse.ArgumentParser(description="Bronze Layer Ingestion")
    parser.add_argument("--mode", choices=["kafka", "json", "verify"], default="json")
    parser.add_argument("--input", type=str, help="JSON file path for batch mode")
    parser.add_argument("--kafka-servers", type=str, default="localhost:9092")
    args = parser.parse_args()

    spark = get_spark_session()

    if args.mode == "kafka":
        ingest_from_kafka(spark, args.kafka_servers)
    elif args.mode == "json":
        if not args.input:
            print("Error: --input required for json mode")
            sys.exit(1)
        ingest_from_json(spark, args.input)
    elif args.mode == "verify":
        verify_bronze(spark)

    spark.stop()
