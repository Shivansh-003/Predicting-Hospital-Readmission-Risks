"""Spark ML Model Training Engine Integration and Verification Suite."""

from pyspark.ml.linalg import Vector
from pyspark.sql import SparkSession

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
    load_model,
    split_data,
    train_all_models,
)


def run_model_training_tests() -> None:
    print("============================================================")
    print("Running Spark ML Model Training Engine Integration Tests")
    print("============================================================")

    spark = (
        SparkSession.builder.appName("ModelTrainingIntegrationTests")
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
    print("\n[1/5] Loading patient features and executing feature pipeline...")
    try:
        df_raw_features = spark.sql("SELECT * FROM readmission.patient_features_view")
    except Exception as e:
        print(f"Direct HiveQL query failed ({e}), loading via HDFS clean Parquet...")
        df_raw_features = spark.read.parquet(
            "hdfs://namenode:9000/readmission/clean/patient_records_clean"
        )

    raw_count = df_raw_features.count()
    print(f"Loaded raw feature view records: {raw_count}")
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

    # 2. Verify Transformed Feature Columns and Vectors
    print("\n[2/5] Verifying feature vector and target presence...")
    assert_test(
        DEFAULT_FEATURES_COL in df_transformed.columns,
        "Features column exists in transformed DataFrame",
    )
    assert_test(
        DEFAULT_LABEL_COL in df_transformed.columns, "Target column exists in transformed DataFrame"
    )
    assert_test(
        "encounter_id" not in df_transformed.columns,
        "encounter_id excluded from model training DataFrame",
    )
    assert_test(
        "patient_nbr" not in df_transformed.columns,
        "patient_nbr excluded from model training DataFrame",
    )

    sample_row = df_transformed.first()
    feat_vector = sample_row[DEFAULT_FEATURES_COL]
    assert_test(
        isinstance(feat_vector, Vector), "Feature vector is an instance of pyspark.ml.linalg.Vector"
    )
    feature_dim = feat_vector.size
    print(f"Feature vector dimension: {feature_dim}")
    assert_test(feature_dim > 0, f"Feature dimension is positive ({feature_dim})")

    # 3. Deterministic 80/20 Train / Test Split
    print("\n[3/5] Executing deterministic 80/20 train/test split (seed=42)...")
    train_df, test_df = split_data(df_transformed, train_ratio=0.8, test_ratio=0.2, seed=42)

    train_count = train_df.count()
    test_count = test_df.count()
    total_split_count = train_count + test_count
    print(f"Train row count: {train_count} ({train_count / total_split_count * 100:.2f}%)")
    print(f"Test row count:  {test_count} ({test_count / total_split_count * 100:.2f}%)")

    assert_test(train_count > 0, f"Train set is non-empty ({train_count} rows)")
    assert_test(test_count > 0, f"Test set is non-empty ({test_count} rows)")
    assert_test(
        total_split_count == raw_count,
        f"Total split count ({total_split_count}) preserves input count ({raw_count})",
    )

    # 4. Train All Four Models
    print("\n[4/5] Training all four Spark ML classifiers...")
    output_models_dir = "/tmp/hospital_readmission_models"
    training_results = train_all_models(
        train_df=train_df,
        test_df=test_df,
        output_base_dir=output_models_dir,
        save_artifacts=True,
    )

    assert_test(
        len(training_results) == 4,
        f"All 4 models were trained and recorded (got {len(training_results)})",
    )
    assert_test(
        list(training_results.keys()) == list(MODEL_ORDER),
        "Models were trained in deterministic order: " + ", ".join(MODEL_ORDER),
    )

    # 5. Verify Model Artifacts and Loadability
    print("\n[5/5] Validating model persistence and loaded transformations...")
    for model_name in MODEL_ORDER:
        meta = training_results[model_name]
        artifact_path = meta["artifact_path"]
        print(f" - Validating artifact for {model_name} at: {artifact_path}")

        assert_test(artifact_path is not None, f"Artifact path recorded for {model_name}")
        assert_test(
            meta["training_duration_seconds"] > 0, f"Training duration recorded for {model_name}"
        )
        assert_test(
            meta["model_loaded_verified"] is True, f"Loaded model verified for {model_name}"
        )

        # Load model explicitly and test transformation on test set
        loaded_model = load_model(model_name, artifact_path)
        test_pred_df = loaded_model.transform(test_df.limit(20))
        assert_test(
            "prediction" in test_pred_df.columns,
            f"Prediction column exists for loaded {model_name}",
        )
        assert_test(
            "rawPrediction" in test_pred_df.columns,
            f"rawPrediction column exists for loaded {model_name}",
        )

    print("\n============================================================")
    print(f"✔ ALL {passed}/{total} SPARK MODEL TRAINING TESTS PASSED!")
    print("============================================================")
    print("\nModel Training Execution Summary:")
    print("------------------------------------------------------------")
    for name, res in training_results.items():
        print(f" Model:               {name}")
        print(f" Estimator:           {res['estimator']}")
        print(f" Hyperparameters:     {res['hyperparameters']}")
        print(f" Training Duration:   {res['training_duration_seconds']:.3f} s")
        print(f" Train / Test Rows:   {res['train_row_count']} / {res['test_row_count']}")
        print(f" Feature Dimension:   {res['feature_dimension']}")
        print(f" Artifact Path:       {res['artifact_path']}")
        print("------------------------------------------------------------")

    spark.stop()


if __name__ == "__main__":
    run_model_training_tests()
