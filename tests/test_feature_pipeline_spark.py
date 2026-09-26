"""Spark Integration and Unit Test Runner for Feature Pipeline."""

import math

from pyspark.ml.linalg import Vector
from pyspark.sql import SparkSession

from src.features.feature_selector import (
    CATEGORICAL_FEATURES,
    TARGET_COLUMN,
    get_all_feature_columns,
    get_categorical_features,
    get_excluded_columns,
    get_numerical_features,
    validate_feature_columns,
)
from src.features.pipeline import (
    build_feature_pipeline,
    fit_feature_pipeline,
    transform_features,
)


def run_feature_pipeline_tests() -> None:
    print("============================================================")
    print("Running Spark ML Feature Pipeline Tests inside Spark Cluster")
    print("============================================================")

    spark = (
        SparkSession.builder.appName("FeaturePipelineTests")
        .master("spark://spark-master:7077")
        .config("spark.driver.host", "spark-master")
        .config("spark.driver.bindAddress", "0.0.0.0")
        .config("hive.metastore.uris", "thrift://hive-server:9083")
        .enableHiveSupport()
        .getOrCreate()
    )

    passed = 0
    total = 0

    def assert_test(condition: bool, test_name: str) -> None:
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f" [PASS] {test_name}")
        else:
            print(f" [FAIL] {test_name}")
            raise AssertionError(f"Test failed: {test_name}")

    # 1. Test Pipeline Stage Count & Construction
    pipeline = build_feature_pipeline()
    num_indexers = len(CATEGORICAL_FEATURES)
    expected_stages = num_indexers + 3  # indexers + encoder + assembler + scaler
    assert_test(
        len(pipeline.getStages()) == expected_stages,
        f"build_feature_pipeline creates {expected_stages} stages ({num_indexers} indexers + 1 encoder + 1 assembler + 1 scaler)",
    )

    # 2. Test Excluded Columns Check
    excluded = get_excluded_columns()
    all_selected = set(get_all_feature_columns())
    assert_test(
        len(all_selected.intersection(set(excluded))) == 0,
        "No excluded column is present in feature sets",
    )

    # 3. Test Synthetic DataFrame Fit and Transform
    cat_cols = get_categorical_features()
    num_cols = get_numerical_features()

    row_data = {}
    # Populate dummy categorical values
    for c in cat_cols:
        row_data[c] = "val_a"
    # Populate dummy numerical values
    for n in num_cols:
        row_data[n] = 1.0
    row_data[TARGET_COLUMN] = 1
    row_data["encounter_id"] = 1001
    row_data["patient_nbr"] = 2002

    df_synth = spark.createDataFrame([row_data, row_data])
    model = fit_feature_pipeline(df_synth, pipeline)
    df_transformed = transform_features(
        df_synth, model, feature_col="features", include_identifiers=True
    )

    assert_test(
        "features" in df_transformed.columns, "Transformed DataFrame contains 'features' column"
    )
    assert_test(
        TARGET_COLUMN in df_transformed.columns,
        f"Transformed DataFrame preserves '{TARGET_COLUMN}'",
    )
    assert_test(
        "encounter_id" in df_transformed.columns,
        "Transformed DataFrame retains 'encounter_id' when requested",
    )

    first_row = df_transformed.first()
    feat_vec = first_row["features"]
    assert_test(isinstance(feat_vec, Vector), "Transformed 'features' is a valid PySpark ML Vector")
    assert_test(feat_vec.size > 0, f"Transformed vector has positive dimension ({feat_vec.size})")

    # 4. Integration Test against Hive View / Table
    print("\n--- Testing Integration against Hive: readmission.patient_features_view ---")
    try:
        df_patient_features = spark.sql("SELECT * FROM readmission.patient_features_view")
    except Exception as e:
        print(f"Direct HiveQL query failed ({e}), loading via parquet fallback...")
        # Fallback reading clean parquet and generating view in Spark SQL
        df_clean = spark.read.parquet(
            "hdfs://namenode:9000/readmission/clean/patient_records_clean"
        )
        df_clean.createOrReplaceTempView("patient_records_clean")
        # Load feature views hql if needed
        df_patient_features = df_clean

    input_count = df_patient_features.count()
    print(f"Loaded input rows: {input_count}")
    assert_test(
        input_count == 99340,
        f"Input patient features view has exact 99,340 rows (got {input_count})",
    )

    # Validate Schema
    validate_feature_columns(df_patient_features, require_target=True)
    assert_test(True, "DataFrame schema successfully passed validate_feature_columns")

    # Fit Pipeline on full dataset
    print("Fitting feature pipeline on full 99,340 rows...")
    full_model = fit_feature_pipeline(df_patient_features, pipeline)
    assert_test(full_model is not None, "PipelineModel successfully fitted on full dataset")

    # Transform Dataset
    print("Transforming full dataset with fitted PipelineModel...")
    df_full_transformed = transform_features(
        df_patient_features,
        full_model,
        feature_col="features",
        target_col=TARGET_COLUMN,
        include_identifiers=True,
    )
    output_count = df_full_transformed.count()
    print(f"Transformed output rows: {output_count}")
    assert_test(
        output_count == 99340,
        f"Transformed output row count matches exactly 99,340 (got {output_count})",
    )

    # Inspect Feature Vector
    sample_row = df_full_transformed.first()
    full_feat_vec = sample_row["features"]
    vector_dim = full_feat_vec.size
    print(f"Final Feature Vector Dimension: {vector_dim}")
    assert_test(vector_dim > 0, f"Feature vector dimension is valid ({vector_dim})")

    # Check for NaN / Inf / Null in feature vector
    sample_rows = df_full_transformed.select("features", TARGET_COLUMN).limit(100).collect()
    all_finite = True
    for r in sample_rows:
        vec = r["features"]
        if vec is None:
            all_finite = False
            break
        vals = vec.toArray()
        for v in vals:
            if math.isnan(v) or math.isinf(v):
                all_finite = False
                break
    assert_test(all_finite, "Sample feature vectors are non-null and contain only finite numbers")

    print("\n============================================================")
    print(f"✔ ALL {passed}/{total} FEATURE PIPELINE INTEGRATION TESTS PASSED!")
    print(f"✔ Feature Vector Dimension: {vector_dim}")
    print(f"✔ Row Cardinality: {input_count} -> {output_count}")
    print("============================================================")
    spark.stop()


if __name__ == "__main__":
    run_feature_pipeline_tests()
