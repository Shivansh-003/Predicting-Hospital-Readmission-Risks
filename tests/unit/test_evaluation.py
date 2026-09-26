"""Unit tests for evaluation metrics, confusion matrix, and reporting contracts."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.evaluation.evaluator import (
    REPORT_COLUMNS,
    evaluate_all_models,
    write_comparison_report_csv,
)
from src.evaluation.metrics import (
    ConfusionMatrix,
    MetricValidationError,
    calculate_accuracy,
    calculate_all_metrics,
    calculate_f1,
    calculate_precision,
    calculate_recall,
    calculate_sensitivity,
    calculate_specificity,
    compute_confusion_matrix,
    validate_metrics,
)
from src.models.model_config import MODEL_ORDER


def test_confusion_matrix_mapping() -> None:
    """Verify explicit mapping of (actual, prediction) count pairs to confusion matrix."""
    counts_map = {
        (1, 1): 25,  # TP
        (0, 0): 65,  # TN
        (0, 1): 5,  # FP
        (1, 0): 5,  # FN
    }
    cm = compute_confusion_matrix(counts_map)
    assert cm.tp == 25
    assert cm.tn == 65
    assert cm.fp == 5
    assert cm.fn == 5
    assert cm.total == 100


def test_confusion_matrix_missing_keys_default_to_zero() -> None:
    """Verify missing count pairs default to 0."""
    cm = compute_confusion_matrix({})
    assert cm.tp == 0
    assert cm.tn == 0
    assert cm.fp == 0
    assert cm.fn == 0
    assert cm.total == 0


def test_metric_calculations_exact_values() -> None:
    """Verify exact formula calculations for all metrics on synthetic confusion matrix."""
    # TP=20, TN=70, FP=5, FN=5 -> Total=100
    cm = ConfusionMatrix(tp=20, tn=70, fp=5, fn=5)

    assert calculate_accuracy(cm) == pytest.approx(0.90)
    assert calculate_precision(cm) == pytest.approx(20 / 25)  # 0.80
    assert calculate_recall(cm) == pytest.approx(20 / 25)  # 0.80
    assert calculate_sensitivity(cm) == pytest.approx(0.80)
    assert calculate_specificity(cm) == pytest.approx(70 / 75)  # 0.933333
    assert calculate_f1(cm) == pytest.approx(0.80)

    all_m = calculate_all_metrics(cm, auc_roc=0.88)
    assert all_m["accuracy"] == pytest.approx(0.90)
    assert all_m["precision"] == pytest.approx(0.80)
    assert all_m["recall"] == pytest.approx(0.80)
    assert all_m["f1"] == pytest.approx(0.80)
    assert all_m["sensitivity"] == pytest.approx(0.80)
    assert all_m["specificity"] == pytest.approx(70 / 75)
    assert all_m["auc_roc"] == pytest.approx(0.88)


def test_zero_division_safety() -> None:
    """Verify that all metrics safely return 0.0 when denominators are zero without throwing."""
    cm_zero = ConfusionMatrix(tp=0, tn=0, fp=0, fn=0)
    assert calculate_accuracy(cm_zero) == 0.0
    assert calculate_precision(cm_zero) == 0.0
    assert calculate_recall(cm_zero) == 0.0
    assert calculate_sensitivity(cm_zero) == 0.0
    assert calculate_specificity(cm_zero) == 0.0
    assert calculate_f1(cm_zero) == 0.0


def test_metric_validation_passes_valid() -> None:
    """Verify that validate_metrics succeeds on valid bounded metrics and matching row count."""
    cm = ConfusionMatrix(tp=10, tn=80, fp=5, fn=5)
    metrics = calculate_all_metrics(cm, auc_roc=0.75)
    # Should not raise
    validate_metrics(metrics, cm, expected_total_rows=100)


def test_metric_validation_fails_on_row_count_mismatch() -> None:
    """Verify MetricValidationError when confusion matrix total != expected test count."""
    cm = ConfusionMatrix(tp=10, tn=80, fp=5, fn=5)
    metrics = calculate_all_metrics(cm, auc_roc=0.75)
    with pytest.raises(MetricValidationError, match="does not match expected test row count"):
        validate_metrics(metrics, cm, expected_total_rows=200)


def test_metric_validation_fails_on_out_of_bounds() -> None:
    """Verify MetricValidationError when a rate metric exceeds 1.0."""
    cm = ConfusionMatrix(tp=10, tn=80, fp=5, fn=5)
    metrics = calculate_all_metrics(cm, auc_roc=1.5)  # Invalid AUC > 1.0
    with pytest.raises(MetricValidationError, match="is out of bounds"):
        validate_metrics(metrics, cm, expected_total_rows=100)


def test_metric_validation_fails_on_nan() -> None:
    """Verify MetricValidationError when a metric contains NaN."""
    cm = ConfusionMatrix(tp=10, tn=80, fp=5, fn=5)
    metrics = {"accuracy": float("nan"), "precision": 0.5}
    with pytest.raises(MetricValidationError, match="contains invalid non-finite value"):
        validate_metrics(metrics, cm, expected_total_rows=100)


def test_report_columns_order() -> None:
    """Verify REPORT_COLUMNS schema specification."""
    expected = [
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
    assert REPORT_COLUMNS == expected


def test_write_comparison_report_csv(tmp_path: Path) -> None:
    """Verify write_comparison_report_csv creates valid CSV with correct headers and rows."""
    out_csv = tmp_path / "test_report.csv"
    mock_results = [
        {
            "model": "logistic_regression",
            "train_rows": 800,
            "test_rows": 200,
            "feature_dimension": 286,
            "accuracy": 0.885,
            "precision": 0.45,
            "recall": 0.35,
            "f1": 0.39,
            "auc_roc": 0.65,
            "sensitivity": 0.35,
            "specificity": 0.92,
            "tp": 10,
            "tn": 167,
            "fp": 15,
            "fn": 8,
            "training_time_seconds": 2.5,
            "prediction_time_seconds": 0.45,
        }
    ]
    written_path = write_comparison_report_csv(mock_results, output_path=out_csv)
    assert written_path.is_file()

    content = written_path.read_text(encoding="utf-8")
    lines = content.strip().split("\n")
    assert len(lines) == 2  # header + 1 row
    assert lines[0].strip() == ",".join(REPORT_COLUMNS)
    assert "logistic_regression" in lines[1]


def test_evaluate_all_models_orchestration(tmp_path: Path) -> None:
    """Verify evaluate_all_models orchestrates evaluation across all 4 models deterministically."""
    mock_test_df = MagicMock()
    mock_vector = MagicMock()
    mock_vector.size = 286
    mock_test_df.count.return_value = 200
    mock_test_df.select.return_value.first.return_value = {"features": mock_vector}

    mock_models_dict = {name: MagicMock() for name in MODEL_ORDER}

    mock_eval_record = {
        "model": "logistic_regression",
        "train_rows": 800,
        "test_rows": 200,
        "feature_dimension": 286,
        "accuracy": 0.85,
        "precision": 0.5,
        "recall": 0.4,
        "f1": 0.44,
        "auc_roc": 0.65,
        "sensitivity": 0.4,
        "specificity": 0.9,
        "tp": 10,
        "tn": 160,
        "fp": 15,
        "fn": 15,
        "training_time_seconds": 1.2,
        "prediction_time_seconds": 0.3,
    }

    with patch(
        "src.evaluation.evaluator.evaluate_single_model", return_value=mock_eval_record
    ) as mock_eval_single:
        out_csv = tmp_path / "model_comparison_report.csv"
        results = evaluate_all_models(
            models_source=mock_models_dict,
            test_df=mock_test_df,
            output_csv_path=out_csv,
        )

        assert len(results) == 4
        assert mock_eval_single.call_count == 4
        assert mock_test_df.unpersist.called
        assert out_csv.is_file()
