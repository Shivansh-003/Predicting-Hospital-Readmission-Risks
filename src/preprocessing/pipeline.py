"""Preprocessing orchestration pipeline for clinical hospital readmission dataset."""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyspark.sql import DataFrame, SparkSession
else:
    try:
        from pyspark.sql import DataFrame, SparkSession
    except ImportError:
        DataFrame = Any
        SparkSession = Any

from src.preprocessing.cleaner import clean_patient_records
from src.preprocessing.encoder import encode_features
from src.preprocessing.validators import validate_cleaned_dataframe, validate_input_columns

DEFAULT_INPUT_HDFS_PATH: str = "hdfs://namenode:9000/readmission/raw/diabetic_data.csv"
DEFAULT_OUTPUT_HDFS_PATH: str = "hdfs://namenode:9000/readmission/clean/patient_records_clean"
DEFAULT_OUTPUT_HIVE_TABLE: str = "readmission.patient_records_clean"


def build_spark_session(
    app_name: str = "HospitalReadmissionPreprocessing",
    master: str | None = None,
) -> SparkSession:
    """Construct and configure a PySpark SparkSession for distributed data processing.

    Args:
        app_name: Name of the Spark application.
        master: Master URL (e.g., 'spark://spark-master:7077', 'local[*]').

    Returns:
        SparkSession: Configured Spark session instance.
    """
    from pyspark.sql import SparkSession

    builder = (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.warehouse.dir", "hdfs://namenode:9000/user/hive/warehouse")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
    )

    if master:
        builder = builder.master(master)

    return builder.getOrCreate()


def run_preprocessing_pipeline(
    spark: SparkSession,
    input_path: str = DEFAULT_INPUT_HDFS_PATH,
    output_path: str = DEFAULT_OUTPUT_HDFS_PATH,
    output_table: str = DEFAULT_OUTPUT_HIVE_TABLE,
) -> tuple[DataFrame, dict[str, Any]]:
    """Execute end-to-end distributed preprocessing pipeline.

    Workflow:
        1. Read raw encounter dataset from HDFS / Hive source.
        2. Validate raw schema columns.
        3. Execute deterministic cleaning (filter terminal cases, replace '?' with NULL).
        4. Encode features (numeric age midpoint, insulin flag, medication flags, binary target).
        5. Validate cleaned dataset schema and data integrity constraints.
        6. Persist cleaned DataFrame as Parquet to HDFS.

    Args:
        spark: Active SparkSession.
        input_path: Source HDFS path or URI.
        output_path: Target HDFS Parquet storage path.
        output_table: Name of the Hive table target.

    Returns:
        Tuple[DataFrame, Dict[str, Any]]: (Cleaned DataFrame, validation report metrics dictionary).
    """
    print("============================================================")
    print("Hospital Readmission — PySpark Preprocessing Engine")
    print("============================================================")

    # 1. Read Raw Dataset
    print(f"\n[1/5] Loading raw encounter dataset from {input_path}...")
    df_raw = spark.read.option("header", "true").option("inferSchema", "true").csv(input_path)

    raw_count = df_raw.count()
    print(f"✔ Successfully loaded {raw_count:,} raw records with {len(df_raw.columns)} columns.")

    # 2. Validate Raw Input Schema
    print("\n[2/5] Validating input schema...")
    validate_input_columns(df_raw)
    print("✔ Input schema validation PASSED.")

    # 3. Clean Dataset
    print("\n[3/5] Cleaning patient records...")
    df_cleaned = clean_patient_records(df_raw)

    # 4. Encode Features and Target
    print("\n[4/5] Encoding clinical features and target variable...")
    df_encoded = encode_features(df_cleaned)

    # 5. Validate Clean Output
    print("\n[5/5] Validating processed dataset integrity...")
    validation_metrics = validate_cleaned_dataframe(df_encoded, expected_input_count=raw_count)
    print("✔ Processed dataset validation PASSED.")
    print(f" - Initial rows:     {validation_metrics['input_row_count']:,}")
    print(f" - Rows removed:     {validation_metrics['rows_removed']:,}")
    print(f" - Clean output rows:{validation_metrics['output_row_count']:,}")
    print(f" - Target 30d dist:  {validation_metrics['target_distribution']}")
    print(f" - Flag dists:       {validation_metrics['flag_distributions']}")
    print(f" - Age bounds:       {validation_metrics['age_statistics']}")

    # 6. Persist to HDFS Parquet
    print(f"\nWriting clean dataset to Parquet at {output_path}...")
    df_encoded.write.mode("overwrite").parquet(output_path)
    print("✔ HDFS Parquet write completed successfully.")

    print("\n============================================================")
    print("✔ PREPROCESSING PIPELINE COMPLETED SUCCESSFULLY!")
    print("============================================================")

    return df_encoded, validation_metrics


def main() -> None:
    """CLI entry point for executing preprocessing pipeline via spark-submit."""
    parser = argparse.ArgumentParser(
        description="Run Hospital Readmission PySpark Preprocessing Pipeline"
    )
    parser.add_argument(
        "--input-path",
        default=DEFAULT_INPUT_HDFS_PATH,
        help="Input CSV path on HDFS",
    )
    parser.add_argument(
        "--output-path",
        default=DEFAULT_OUTPUT_HDFS_PATH,
        help="Output Parquet path on HDFS",
    )
    parser.add_argument(
        "--output-table",
        default=DEFAULT_OUTPUT_HIVE_TABLE,
        help="Target Hive table name",
    )
    parser.add_argument(
        "--master",
        default=None,
        help="Spark master URL",
    )

    args = parser.parse_args()

    spark = build_spark_session(
        app_name="HospitalReadmissionPreprocessing",
        master=args.master,
    )

    try:
        run_preprocessing_pipeline(
            spark=spark,
            input_path=args.input_path,
            output_path=args.output_path,
            output_table=args.output_table,
        )
    except Exception as e:
        print(f"\n✖ Preprocessing pipeline failed with error: {e}", file=sys.stderr)
        spark.stop()
        sys.exit(1)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
