"""Hospital Readmission - Model Evaluation Engine and Comparative Reporting."""

from src.evaluation.evaluator import (
    REPORT_COLUMNS,
    evaluate_all_models,
    evaluate_single_model,
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

__all__ = [
    "ConfusionMatrix",
    "MetricValidationError",
    "REPORT_COLUMNS",
    "compute_confusion_matrix",
    "calculate_accuracy",
    "calculate_precision",
    "calculate_recall",
    "calculate_f1",
    "calculate_sensitivity",
    "calculate_specificity",
    "calculate_all_metrics",
    "validate_metrics",
    "evaluate_single_model",
    "evaluate_all_models",
    "write_comparison_report_csv",
]
