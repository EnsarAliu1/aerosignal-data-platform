from pathlib import Path
from pyspark.sql import functions as F

from validation import (
    validate_ingestion_params,
    validate_required_columns,
    validate_file_checksum,
)

TABLE_NAME = "workspace.aerosignal_bronze.flights_raw"

REQUIRED_COLUMNS = [
    "YEAR",
    "MONTH",
    "FL_DATE",
    "OP_UNIQUE_CARRIER",
    "OP_CARRIER_FL_NUM",
    "ORIGIN",
    "DEST",
    "CRS_DEP_TIME",
    "DEP_DELAY",
    "ARR_DELAY",
    "CANCELLED",
    "DIVERTED",
]

def ingest_bts_month(
    spark,
    source_path: str,
    year: int,
    month: int,
    source_sha256: str,
) -> int:
    """
        Ingest BTS monthly flights inot Bronze Delta table.
    """

    # 1. Validate parameters
    validate_ingestion_params(
        year=year,
        month=month,
        source_sha256=source_sha256
    )

    # 2. Verify source file checksum
    validate_file_checksum(
        source_path=source_path,
        expected_sha256=source_sha256
    )

    # 3. Read raw CSV
    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "false")
        .option("mode", "FAILFAST")
        .csv(source_path)
    )

    # 4. Validate required columns
    validate_required_columns(
        actual_columns=df.columns,
        required_columns=REQUIRED_COLUMNS,
    )

    # 5. Validate source rows
    row_count = df.count()

    if row_count == 0:
        raise ValueError("Source file is empty")

    flight_date = F.to_date(
    F.col("FL_DATE"),
    "M/d/yyyy h:mm:ss a"
    )

    invalid_rows = df.filter(
        F.col("YEAR").cast("int").isNull()
        | (F.col("YEAR").cast("int") != year)
        | F.col("MONTH").cast("int").isNull()
        | (F.col("MONTH").cast("int") != month)
        | flight_date.isNull()
        | (F.year(flight_date) != year)
        | (F.month(flight_date) != month)
    )

    if invalid_rows.limit(1).count() > 0:
        raise ValueError("CSV contains invalid dates or wrong month")

    # 6. Add ingestion metadata
    bronze_df = (
        df
        .withColumn("_source_file", F.lit(Path(source_path).name))
        .withColumn("_source_sha256", F.lit(source_sha256.lower()))
        .withColumn("_ingested_at_utc", F.current_timestamp())
        .withColumn("_source_year", F.lit(year))
        .withColumn("_source_month", F.lit(month))
    )

    # 7. Save to Delta
    if not spark.catalog.tableExists(TABLE_NAME):
        (
            bronze_df.write
            .format("delta")
            .mode("append")
            .partitionBy("_source_year", "_source_month")
            .saveAsTable(TABLE_NAME)
        )
    else:
        predicate = (
            f"_source_year = {year} AND _source_month = {month}"
        )

        (
            bronze_df.write
            .format("delta")
            .mode("overwrite")
            .option("replaceWhere", predicate)
            .saveAsTable(TABLE_NAME)
        )

    return row_count