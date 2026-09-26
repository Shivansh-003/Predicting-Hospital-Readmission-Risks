"""Model Evaluation Engine for Spark ML Classifiers.

Executes comparative evaluation across Logistic Regression, Random Forest,
Decision Tree, and GBT on the shared deterministic test partition, producing
outputs/model_comparison_report.csv.
"""

import csv
import logging
import time
from pathlib import Path
from typing import Any

try:
    from pyspark import StorageLevel
    from pyspark.ml.evaluation import BinaryClassificationEvaluator
    from pyspark.sql import DataFrame
except ImportError:
    StorageLevel = None
    BinaryClassificationEvaluator = None
    DataFrame = None

from src.evaluation.metrics import (
    calculate_all_metrics,
    compute_confusion_matrix,
    validate_metrics,
)
from src.models.model_config import (
    DEFAULT_LABEL_COL,
    MODEL_ORDER,
)
from src.models.trainer import load_model

logger = logging.getLogger(__name__)

REPORT_COLUMNS: list[str] = [
    "model",
    "train_rows",
    "test_rows",
    "feature_dimension",
    "accuracy",
    "precision",
    "recall",
    "f1",
    "auc_roc",
    "sensitivity",
    "specificity",
    "tp",
    "tn",
    "fp",
    "fn",
    "training_time_seconds",
    "prediction_time_seconds",
]


def evaluate_single_model(
    model: Any,
    test_df: Any,
    model_name: str,
    training_duration_seconds: float = 0.0,
    train_row_count: int = 0,
    feature_dimension: int = 0,
    label_col: str = DEFAULT_LABEL_COL,
) -> dict[str, Any]:
    """Evaluate a single fitted Spark ML model on the test partition.

    Timing Methodology:
    Measures elapsed wall-clock time required to apply model.transform() and
    force materialization of prediction results via a Spark DataFrame count().

    Args:
        model: Fitted Spark ML Model instance.
        test_df: PySpark DataFrame containing test partition.
        model_name: Canonical model name identifier.
        training_duration_seconds: Measured training execution duration.
        train_row_count: Number of training records used during fitting.
        feature_dimension: Number of features in feature vector.
        label_col: Name of actual target label column.

    Returns:
        Dictionary containing all evaluation metrics, confusion matrix counts, and timings.
    """
    logger.info("Evaluating model: %s...", model_name)

    # 1. Measure prediction execution time with forced materialization
    start_time = time.perf_counter()
    predictions_df = model.transform(test_df)
    test_row_count = predictions_df.select("prediction", label_col).count()
    prediction_duration = time.perf_counter() - start_time
    logger.info(
        "Prediction completed for %s in %.3fs (%d test rows).",
        model_name,
        prediction_duration,
        test_row_count,
    )

    # 2. Derive Confusion Matrix via Spark aggregation (aggregates on cluster, collects <= 4 rows)
    cm_rows = predictions_df.groupBy(label_col, "prediction").count().collect()
    counts_map: dict[tuple[int, int], int] = {}
    for row in cm_rows:
        actual_val = int(row[label_col])
        pred_val = int(row["prediction"])
        counts_map[(actual_val, pred_val)] = row["count"]

    cm = compute_confusion_matrix(counts_map)
    logger.info(
        "Confusion Matrix for %s: TP=%d, TN=%d, FP=%d, FN=%d (Total=%d)",
        model_name,
        cm.tp,
        cm.tn,
        cm.fp,
        cm.fn,
        cm.total,
    )

    # 3. Calculate AUC-ROC using Spark BinaryClassificationEvaluator
    auc_roc = 0.0
    if BinaryClassificationEvaluator is not None:
        raw_pred_col = (
            "rawPrediction" if "rawPrediction" in predictions_df.columns else "probability"
        )
        evaluator = BinaryClassificationEvaluator(
            rawPredictionCol=raw_pred_col,
            labelCol=label_col,
            metricName="areaUnderROC",
        )
        auc_roc = float(evaluator.evaluate(predictions_df))
    logger.info("AUC-ROC for %s: %.4f", model_name, auc_roc)

    # 4. Compute all derived metrics
    metrics = calculate_all_metrics(cm=cm, auc_roc=auc_roc)

    # 5. Invariant Validation
    validate_metrics(metrics, cm, expected_total_rows=test_row_count)

    record = {
        "model": model_name,
        "train_rows": train_row_count,
        "test_rows": test_row_count,
        "feature_dimension": feature_dimension,
        "accuracy": round(metrics["accuracy"], 6),
        "precision": round(metrics["precision"], 6),
        "recall": round(metrics["recall"], 6),
        "f1": round(metrics["f1"], 6),
        "auc_roc": round(metrics["auc_roc"], 6),
        "sensitivity": round(metrics["sensitivity"], 6),
        "specificity": round(metrics["specificity"], 6),
        "tp": cm.tp,
        "tn": cm.tn,
        "fp": cm.fp,
        "fn": cm.fn,
        "training_time_seconds": round(training_duration_seconds, 3),
        "prediction_time_seconds": round(prediction_duration, 3),
    }
    return record


def write_comparison_report_csv(
    results: list[dict[str, Any]],
    output_path: str | Path = "outputs/model_comparison_report.csv",
) -> Path:
    """Write model comparison results to CSV file.

    Args:
        results: List of model evaluation dictionaries.
        output_path: Target CSV file path.

    Returns:
        Resolved Path object of the written CSV file.
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with open(out_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        for row in results:
            writer.writerow({k: row.get(k, "") for k in REPORT_COLUMNS})

    logger.info("Wrote model comparison report to: %s", out_file.resolve())
    return out_file


def evaluate_all_models(
    models_source: dict[str, Any] | str,
    test_df: Any,
    train_metadata: dict[str, dict[str, Any]] | None = None,
    output_csv_path: str | Path = "outputs/model_comparison_report.csv",
) -> list[dict[str, Any]]:
    """Evaluate all four trained models deterministically and write the comparison report.

    Args:
        models_source: Dictionary mapping model names to fitted model instances,
                       OR base directory path containing saved model artifacts.
        test_df: PySpark DataFrame for the shared test partition.
        train_metadata: Optional dictionary mapping model names to training metadata
                        (train_row_count, training_duration_seconds, feature_dimension).
        output_csv_path: Target path for the output CSV report.

    Returns:
        List of evaluation records in deterministic model order.
    """
    # 1. Persist test DataFrame for efficient sequential evaluation
    logger.info("Persisting test DataFrame for comparative evaluation...")
    if StorageLevel is not None:
        test_df.persist(StorageLevel.MEMORY_AND_DISK)
    else:
        test_df.cache()

    test_count = test_df.count()
    logger.info("Test partition materialized with %d rows.", test_count)

    # Determine feature dimension if available
    sample_first = test_df.select("features").first()
    feat_dim = sample_first["features"].size if sample_first else 0

    evaluation_records: list[dict[str, Any]] = []

    try:
        for model_name in MODEL_ORDER:
            # Retrieve model instance
            if isinstance(models_source, dict):
                model_instance = models_source[model_name]
            elif isinstance(models_source, str):
                artifact_path = f"{models_source}/{model_name}"
                logger.info("Loading persisted model '%s' from %s...", model_name, artifact_path)
                model_instance = load_model(model_name, artifact_path)
            else:
                raise TypeError(f"Unsupported models_source type: {type(models_source)}")

            # Extract training metadata if provided
            meta = (train_metadata or {}).get(model_name, {})
            train_rows = meta.get("train_row_count", 0)
            train_duration = meta.get("training_duration_seconds", 0.0)
            model_feat_dim = meta.get("feature_dimension", feat_dim)

            eval_res = evaluate_single_model(
                model=model_instance,
                test_df=test_df,
                model_name=model_name,
                training_duration_seconds=train_duration,
                train_row_count=train_rows,
                feature_dimension=model_feat_dim,
            )
            evaluation_records.append(eval_res)

        # Write final comparison CSV
        write_comparison_report_csv(evaluation_records, output_path=output_csv_path)

    finally:
        logger.info("Releasing cached test DataFrame...")
        test_df.unpersist()

    return evaluation_records
