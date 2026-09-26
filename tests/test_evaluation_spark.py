"""Spark ML Model Evaluation Engine Integration and Verification Suite."""

from pathlib import Path

from pyspark.sql import SparkSession

from src.evaluation.evaluator import (
    REPORT_COLUMNS,
    evaluate_all_models,
)
from src.features.pipeline import (
    build_feature_pipeline,
    fit_feature_pipeline,
    transform_features,
)
from src.models.model_config import (
    DEFAULT_FEATURES_COL,
    DEFAULT_LABEL_COL,
    MODEL_ORDER,
)
from src.models.trainer import (
    split_data,
    train_all_models,
)


def run_evaluation_engine_tests() -> None:
    print("============================================================")
    print("Running Spark ML Model Evaluation Engine Integration Tests")
    print("============================================================")

    spark = (
        SparkSession.builder.appName("ModelEvaluationIntegrationTests")
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

    # 1. Load Clinical Dataset and Run Feature Pipeline
    print("\n[1/6] Loading patient features and executing feature pipeline...")
    try:
        df_raw_features = spark.sql("SELECT * FROM readmission.patient_features_view")
    except Exception as e:
        print(f"Direct HiveQL query failed ({e}), loading via HDFS clean Parquet...")
        df_raw_features = spark.read.parquet(
            "hdfs://namenode:9000/readmission/clean/patient_records_clean"
        )

    raw_count = df_raw_features.count()
    print(f"Loaded raw feature records: {raw_count}")
    assert_test(
        raw_count == 99340, f"Raw feature dataset has exact 99,340 records (got {raw_count})"
    )

    # Fit feature pipeline
    feature_pipeline = build_feature_pipeline()
    fitted_feature_model = fit_feature_pipeline(
        df_raw_features, feature_pipeline, require_target=True
    )
    df_transformed = transform_features(
        df_raw_features,
        fitted_feature_model,
        feature_col=DEFAULT_FEATURES_COL,
        target_col=DEFAULT_LABEL_COL,
        include_identifiers=False,
    )

    # 2. Deterministic 80/20 Train / Test Split
    print("\n[2/6] Executing deterministic 80/20 train/test split (seed=42)...")
    train_df, test_df = split_data(df_transformed, train_ratio=0.8, test_ratio=0.2, seed=42)
    train_count = train_df.count()
    test_count = test_df.count()
    print(f"Train row count: {train_count} | Test row count: {test_count}")
    assert_test(train_count > 0 and test_count > 0, "Train and test splits are non-empty")
    assert_test(
        train_count + test_count == raw_count, "Train + test row count matches input dataset"
    )

    # 3. Fit Models to ensure actual trained models and real training timings
    print("\n[3/6] Fitting all four models to measure actual training durations...")
    models_dir = "/tmp/hospital_readmission_models"
    training_results = train_all_models(
        train_df=train_df,
        test_df=test_df,
        output_base_dir=models_dir,
        save_artifacts=True,
    )
    assert_test(len(training_results) == 4, "All 4 models fitted and persisted")

    # 4. Comparative Evaluation on Shared Test Set
    print("\n[4/6] Evaluating all four models on the deterministic test partition...")
    output_report_path = "outputs/model_comparison_report.csv"
    evaluation_records = evaluate_all_models(
        models_source=models_dir,
        test_df=test_df,
        train_metadata=training_results,
        output_csv_path=output_report_path,
    )

    assert_test(
        len(evaluation_records) == 4,
        f"Evaluation generated records for all 4 models (got {len(evaluation_records)})",
    )
    assert_test(
        [r["model"] for r in evaluation_records] == list(MODEL_ORDER),
        "Evaluation records follow deterministic model ordering: " + ", ".join(MODEL_ORDER),
    )

    # 5. Invariant Checks for Each Model Result
    print("\n[5/6] Validating evaluation metrics and confusion matrix totals...")
    for rec in evaluation_records:
        name = rec["model"]
        tp, tn, fp, fn = rec["tp"], rec["tn"], rec["fp"], rec["fn"]
        cm_total = tp + tn + fp + fn

        print(
            f" - {name}: TP={tp}, TN={tn}, FP={fp}, FN={fn} | Total={cm_total} (Expected={test_count})"
        )
        assert_test(cm_total == test_count, f"{name}: TP+TN+FP+FN equals test row count")
        assert_test(0.0 <= rec["accuracy"] <= 1.0, f"{name}: 0 <= accuracy <= 1")
        assert_test(0.0 <= rec["precision"] <= 1.0, f"{name}: 0 <= precision <= 1")
        assert_test(0.0 <= rec["recall"] <= 1.0, f"{name}: 0 <= recall <= 1")
        assert_test(0.0 <= rec["f1"] <= 1.0, f"{name}: 0 <= f1 <= 1")
        assert_test(0.0 <= rec["auc_roc"] <= 1.0, f"{name}: 0 <= auc_roc <= 1")
        assert_test(0.0 <= rec["sensitivity"] <= 1.0, f"{name}: 0 <= sensitivity <= 1")
        assert_test(0.0 <= rec["specificity"] <= 1.0, f"{name}: 0 <= specificity <= 1")
        assert_test(rec["prediction_time_seconds"] > 0, f"{name}: prediction time measured")
        assert_test(rec["training_time_seconds"] > 0, f"{name}: training time measured")

    # 6. Verify Output Report CSV
    print("\n[6/6] Verifying output CSV file structure and integrity...")
    csv_path = Path(output_report_path)
    assert_test(csv_path.is_file(), f"Output CSV file exists at: {output_report_path}")

    csv_content = csv_path.read_text(encoding="utf-8").strip().split("\n")
    assert_test(
        len(csv_content) == 5,
        f"CSV contains 5 lines (header + 4 model rows, got {len(csv_content)})",
    )
    assert_test(
        csv_content[0].strip() == ",".join(REPORT_COLUMNS),
        "CSV header matches REPORT_COLUMNS exactly",
    )

    print("\n============================================================")
    print(f"✔ ALL {passed}/{total} EVALUATION ENGINE INTEGRATION TESTS PASSED!")
    print("============================================================")
    print(f"\nModel Comparison Report Preview ({output_report_path}):")
    print(
        "---------------------------------------------------------------------------------------------------------------------------------"
    )
    for line in csv_content:
        print(line)
    print(
        "---------------------------------------------------------------------------------------------------------------------------------"
    )

    spark.stop()


if __name__ == "__main__":
    run_evaluation_engine_tests()
