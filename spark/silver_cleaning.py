"""
Silver Layer — Data Quality & Cleaning

Reads from Bronze Parquet, applies data quality rules, deduplicates,
standardizes, and writes cleaned events to Silver Parquet.

Quality Rules:
1. Reject events where patient_id is null
2. Reject events where event_type is not one of ADT_A01, ADT_A02, ADT_A03
3. Flag events where timestamp > 24 hours old (late arrivals)
4. Standardize ward names to controlled vocabulary
5. Deduplicate: patient cannot be admitted to two wards simultaneously
"""

import os
import logging
from datetime import datetime, timedelta

from pyspark.sql import SparkSession, DataFrame, Window
from pyspark.sql.types import StringType, BooleanType
from pyspark.sql.functions import (
    col, when, lit, trim, upper, lower, regexp_replace,
    to_timestamp, current_timestamp, datediff, hour,
    row_number, count, lag, lead, coalesce,
    concat, date_format, to_date
)

logger = logging.getLogger("spark.silver")

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRONZE_PATH = os.path.join(BASE_DIR, "data", "bronze")
SILVER_PATH = os.path.join(BASE_DIR, "data", "silver")
REJECTED_PATH = os.path.join(BASE_DIR, "data", "rejected")

# ─── Constants ───────────────────────────────────────────────────────────────
VALID_EVENT_TYPES = ["ADT_A01", "ADT_A02", "ADT_A03"]
VALID_WARD_NAMES = {
    "ICU EAST": "ICU East",
    "ICU WEST": "ICU West",
    "GENERAL A": "General A",
    "GENERAL B": "General B",
    "PEDIATRICS": "Pediatrics",
    "EMERGENCY": "Emergency",
    "ONCOLOGY": "Oncology",
}
VALID_WARD_IDS = ["W-001", "W-002", "W-003", "W-004", "W-005", "W-006", "W-007"]
LATE_ARRIVAL_HOURS = 24


def get_spark_session(app_name: str = "HospitalSilver") -> SparkSession:
    """Create or get a SparkSession."""
    return (
        SparkSession.builder
        .appName(app_name)
        .master("local[*]")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.driver.memory", "2g")
        .getOrCreate()
    )


def read_bronze(spark: SparkSession, date_filter: str = None) -> DataFrame:
    """Read from Bronze Parquet, optionally filtering by date."""
    logger.info(f"Reading Bronze layer from {BRONZE_PATH}...")
    df = spark.read.parquet(BRONZE_PATH)

    if date_filter:
        df = df.filter(col("event_date") == date_filter)
        logger.info(f"  Filtered to date: {date_filter}")

    total = df.count()
    logger.info(f"  Bronze records loaded: {total}")
    return df


def rule_1_null_patient_id(df: DataFrame) -> tuple:
    """Rule 1: Reject events where patient_id is null."""
    good = df.filter(col("patient_id").isNotNull())
    bad = df.filter(col("patient_id").isNull()).withColumn(
        "rejection_reason", lit("null_patient_id")
    )
    rejected = bad.count()
    if rejected > 0:
        logger.warning(f"  Rule 1: Rejected {rejected} records (null patient_id)")
    else:
        logger.info(f"  Rule 1: ✅ No null patient_ids")
    return good, bad


def rule_2_invalid_event_type(df: DataFrame) -> tuple:
    """Rule 2: Reject events where event_type is not valid."""
    good = df.filter(col("event_type").isin(VALID_EVENT_TYPES))
    bad = df.filter(~col("event_type").isin(VALID_EVENT_TYPES)).withColumn(
        "rejection_reason", lit("invalid_event_type")
    )
    rejected = bad.count()
    if rejected > 0:
        logger.warning(f"  Rule 2: Rejected {rejected} records (invalid event_type)")
    else:
        logger.info(f"  Rule 2: ✅ All event types valid")
    return good, bad


def rule_3_late_arrivals(df: DataFrame) -> DataFrame:
    """Rule 3: Flag events where timestamp > 24 hours old."""
    df_with_flag = df.withColumn(
        "event_ts", to_timestamp(col("timestamp"))
    ).withColumn(
        "is_late_arrival",
        when(
            (current_timestamp().cast("long") - col("event_ts").cast("long")) > (LATE_ARRIVAL_HOURS * 3600),
            lit(True)
        ).otherwise(lit(False))
    )

    late_count = df_with_flag.filter(col("is_late_arrival") == True).count()
    if late_count > 0:
        logger.warning(f"  Rule 3: Flagged {late_count} late arrivals (>{LATE_ARRIVAL_HOURS}h old)")
    else:
        logger.info(f"  Rule 3: ✅ No late arrivals")

    return df_with_flag


def rule_4_standardize_ward_names(df: DataFrame) -> DataFrame:
    """Rule 4: Standardize ward names to controlled vocabulary."""
    # Build CASE expression for standardization
    standardized = df
    for raw_name, clean_name in VALID_WARD_NAMES.items():
        standardized = standardized.withColumn(
            "ward_name",
            when(upper(trim(col("ward_name"))) == raw_name, lit(clean_name))
            .otherwise(col("ward_name"))
        )

    logger.info("  Rule 4: ✅ Ward names standardized")
    return standardized


def rule_5_deduplicate(df: DataFrame) -> tuple:
    """
    Rule 5: Deduplicate — a patient cannot be admitted to two wards simultaneously.
    Keep the latest admission event for each patient.
    """
    # For ADT_A01 (admits), ensure a patient is only in one ward at a time
    admits = df.filter(col("event_type") == "ADT_A01")
    non_admits = df.filter(col("event_type") != "ADT_A01")

    # Window: partition by patient_id, order by timestamp desc
    window = Window.partitionBy("patient_id").orderBy(col("timestamp").desc())

    # For admits, keep only the latest admission per patient
    admits_deduped = (
        admits
        .withColumn("row_num", row_number().over(window))
        .filter(col("row_num") == 1)
        .drop("row_num")
    )

    # Duplicates removed
    dup_count = admits.count() - admits_deduped.count()

    # Combine back
    result = admits_deduped.unionByName(non_admits, allowMissingColumns=True)

    if dup_count > 0:
        logger.warning(f"  Rule 5: Removed {dup_count} duplicate admissions")
    else:
        logger.info(f"  Rule 5: ✅ No duplicate admissions")

    # Get the duplicates for rejection tracking
    admits_with_row = admits.withColumn("row_num", row_number().over(window))
    duplicates = (
        admits_with_row
        .filter(col("row_num") > 1)
        .drop("row_num")
        .withColumn("rejection_reason", lit("duplicate_admission"))
    )

    return result, duplicates


def clean_bronze_to_silver(spark: SparkSession, date_filter: str = None):
    """
    Main Silver layer processing pipeline.
    Applies all quality rules and writes to Silver Parquet.
    """
    logger.info("=" * 60)
    logger.info("🔄 Silver Layer Processing Started")
    logger.info("=" * 60)

    # Read Bronze
    bronze_df = read_bronze(spark, date_filter)
    initial_count = bronze_df.count()

    if initial_count == 0:
        logger.warning("No Bronze data found. Exiting.")
        return 0

    all_rejected = []

    # Apply rules
    logger.info("\n📋 Applying Data Quality Rules...")

    # Rule 1: Null patient_id
    df, rejected_1 = rule_1_null_patient_id(bronze_df)
    if rejected_1.count() > 0:
        all_rejected.append(rejected_1)

    # Rule 2: Invalid event type
    df, rejected_2 = rule_2_invalid_event_type(df)
    if rejected_2.count() > 0:
        all_rejected.append(rejected_2)

    # Rule 3: Late arrivals (flag, don't reject)
    df = rule_3_late_arrivals(df)

    # Rule 4: Standardize ward names
    df = rule_4_standardize_ward_names(df)

    # Rule 5: Deduplicate
    df, rejected_5 = rule_5_deduplicate(df)
    if rejected_5.count() > 0:
        all_rejected.append(rejected_5)

    # Add Silver metadata
    silver_df = (
        df
        .withColumn("processed_at", current_timestamp())
        .withColumn("event_date", to_date(col("timestamp")))
        .withColumn("event_hour", hour(to_timestamp(col("timestamp"))))
    )

    # Write Silver
    os.makedirs(SILVER_PATH, exist_ok=True)
    (
        silver_df.write
        .mode("append")
        .partitionBy("event_date", "ward_id")
        .parquet(SILVER_PATH)
    )

    final_count = silver_df.count()
    logger.info(f"\n📊 Silver Layer Summary:")
    logger.info(f"   Input (Bronze):  {initial_count}")
    logger.info(f"   Output (Silver): {final_count}")
    logger.info(f"   Rejected:        {initial_count - final_count}")
    logger.info(f"   Pass rate:       {(final_count / initial_count * 100):.1f}%")

    # Write rejected records
    if all_rejected:
        os.makedirs(REJECTED_PATH, exist_ok=True)
        # Select common columns only for union
        common_cols = ["message_id", "event_type", "patient_id", "ward_id",
                       "ward_name", "timestamp", "bed_id", "rejection_reason"]
        rejected_dfs = []
        for r_df in all_rejected:
            # Ensure all columns exist
            for c in common_cols:
                if c not in r_df.columns:
                    r_df = r_df.withColumn(c, lit(None).cast(StringType()))
            rejected_dfs.append(r_df.select(*common_cols))

        from functools import reduce
        all_rejected_df = reduce(lambda a, b: a.unionByName(b), rejected_dfs)
        all_rejected_df = all_rejected_df.withColumn("rejected_at", current_timestamp())

        (
            all_rejected_df.write
            .mode("append")
            .parquet(REJECTED_PATH)
        )
        logger.info(f"   Rejected records saved to {REJECTED_PATH}")

    logger.info("✅ Silver layer processing complete")
    return final_count


def verify_silver(spark: SparkSession):
    """Verify Silver layer data quality."""
    logger.info("Verifying Silver layer...")

    if not os.path.exists(SILVER_PATH):
        logger.error("❌ Silver path does not exist!")
        return False

    df = spark.read.parquet(SILVER_PATH)
    total = df.count()

    logger.info(f"  Total records: {total}")

    # Verify no nulls in critical fields
    for field in ["message_id", "patient_id", "event_type", "ward_id"]:
        null_count = df.filter(col(field).isNull()).count()
        status = "✅" if null_count == 0 else "❌"
        logger.info(f"  {status} {field}: {null_count} nulls")

    # Verify event types
    invalid = df.filter(~col("event_type").isin(VALID_EVENT_TYPES)).count()
    logger.info(f"  {'✅' if invalid == 0 else '❌'} Invalid event types: {invalid}")

    # Late arrival stats
    if "is_late_arrival" in df.columns:
        late = df.filter(col("is_late_arrival") == True).count()
        logger.info(f"  ℹ️ Late arrivals flagged: {late}")

    return True


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s")

    parser = argparse.ArgumentParser(description="Silver Layer Processing")
    parser.add_argument("--date", type=str, default=None, help="Filter by date (YYYY-MM-DD)")
    parser.add_argument("--verify", action="store_true", help="Verify Silver layer only")
    args = parser.parse_args()

    spark = get_spark_session()

    if args.verify:
        verify_silver(spark)
    else:
        clean_bronze_to_silver(spark, args.date)

    spark.stop()
