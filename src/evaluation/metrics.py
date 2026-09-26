"""Pure Evaluation Metrics Computation and Validation for Binary Classification.

Computes accuracy, precision, recall, F1, sensitivity, specificity, and confusion matrix
with strict zero-division safety and invariant validation.
"""

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConfusionMatrix:
    """Immutable container for binary classification confusion matrix counts."""

    tp: int  # Actual=1, Predicted=1
    tn: int  # Actual=0, Predicted=0
    fp: int  # Actual=0, Predicted=1
    fn: int  # Actual=1, Predicted=0

    @property
    def total(self) -> int:
        """Return the sum of all four confusion matrix quadrants."""
        return self.tp + self.tn + self.fp + self.fn


class MetricValidationError(Exception):
    """Raised when calculated metrics violate mathematical or domain invariants."""

    pass


def compute_confusion_matrix(
    counts_map: dict[tuple[int, int], int],
) -> ConfusionMatrix:
    """Map aggregated (actual, prediction) count pairs into a structured ConfusionMatrix.

    Explicit Mapping:
    - actual=1, prediction=1 -> True Positive (TP)
    - actual=0, prediction=0 -> True Negative (TN)
    - actual=0, prediction=1 -> False Positive (FP)
    - actual=1, prediction=0 -> False Negative (FN)

    Args:
        counts_map: Dictionary mapping (int(actual), int(prediction)) -> count.

    Returns:
        ConfusionMatrix instance.
    """
    tp = counts_map.get((1, 1), 0)
    tn = counts_map.get((0, 0), 0)
    fp = counts_map.get((0, 1), 0)
    fn = counts_map.get((1, 0), 0)

    return ConfusionMatrix(tp=tp, tn=tn, fp=fp, fn=fn)


def calculate_accuracy(cm: ConfusionMatrix) -> float:
    """Calculate overall accuracy: (TP + TN) / (TP + TN + FP + FN).

    Returns 0.0 if total count is zero.
    """
    total = cm.total
    if total <= 0:
        return 0.0
    return float((cm.tp + cm.tn) / total)


def calculate_precision(cm: ConfusionMatrix) -> float:
    """Calculate precision (Positive Predictive Value): TP / (TP + FP).

    Returns 0.0 if (TP + FP) is zero.
    """
    denom = cm.tp + cm.fp
    if denom <= 0:
        return 0.0
    return float(cm.tp / denom)


def calculate_recall(cm: ConfusionMatrix) -> float:
    """Calculate recall / sensitivity: TP / (TP + FN).

    Returns 0.0 if (TP + FN) is zero.
    """
    denom = cm.tp + cm.fn
    if denom <= 0:
        return 0.0
    return float(cm.tp / denom)


def calculate_sensitivity(cm: ConfusionMatrix) -> float:
    """Calculate clinical sensitivity (True Positive Rate): TP / (TP + FN).

    Returns 0.0 if (TP + FN) is zero.
    """
    return calculate_recall(cm)


def calculate_specificity(cm: ConfusionMatrix) -> float:
    """Calculate specificity (True Negative Rate): TN / (TN + FP).

    Returns 0.0 if (TN + FP) is zero.
    """
    denom = cm.tn + cm.fp
    if denom <= 0:
        return 0.0
    return float(cm.tn / denom)


def calculate_f1(cm: ConfusionMatrix) -> float:
    """Calculate harmonic mean F1-Score: 2 * (precision * recall) / (precision + recall).

    Returns 0.0 if (precision + recall) is zero.
    """
    prec = calculate_precision(cm)
    rec = calculate_recall(cm)
    denom = prec + rec
    if denom <= 0.0:
        return 0.0
    return float(2.0 * (prec * rec) / denom)


def calculate_all_metrics(
    cm: ConfusionMatrix,
    auc_roc: float = 0.0,
) -> dict[str, float]:
    """Calculate all standard classification metrics from ConfusionMatrix and AUC-ROC.

    Args:
        cm: ConfusionMatrix instance.
        auc_roc: Measured Area Under ROC Curve (0.0 to 1.0).

    Returns:
        Dictionary mapping metric names to floating point scores.
    """
    acc = calculate_accuracy(cm)
    prec = calculate_precision(cm)
    rec = calculate_recall(cm)
    f1 = calculate_f1(cm)
    sens = calculate_sensitivity(cm)
    spec = calculate_specificity(cm)

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "auc_roc": float(auc_roc),
        "sensitivity": sens,
        "specificity": spec,
    }


def validate_metrics(
    metrics_dict: dict[str, Any],
    cm: ConfusionMatrix,
    expected_total_rows: int,
) -> None:
    """Validate metric bounds, non-negativity, and confusion matrix totals.

    Args:
        metrics_dict: Dictionary containing metric scores.
        cm: ConfusionMatrix instance.
        expected_total_rows: Expected test row count.

    Raises:
        MetricValidationError: If any metric is out of bounds, NaN, Infinite,
                               or confusion matrix does not equal expected total.
    """
    # 1. Confusion matrix non-negativity
    if cm.tp < 0 or cm.tn < 0 or cm.fp < 0 or cm.fn < 0:
        raise MetricValidationError(
            f"Confusion matrix counts must be non-negative: TP={cm.tp}, TN={cm.tn}, FP={cm.fp}, FN={cm.fn}"
        )

    # 2. Confusion matrix sum equals test set count
    if cm.total != expected_total_rows:
        raise MetricValidationError(
            f"Confusion matrix total ({cm.total}) does not match expected test row count ({expected_total_rows})"
        )

    # 3. Numeric bounds [0.0, 1.0] and finiteness
    rate_keys = [
        "accuracy",
        "precision",
        "recall",
        "f1",
        "auc_roc",
        "sensitivity",
        "specificity",
    ]
    for key in rate_keys:
        if key in metrics_dict:
            val = metrics_dict[key]
            if val is None or math.isnan(val) or math.isinf(val):
                raise MetricValidationError(
                    f"Metric '{key}' contains invalid non-finite value: {val}"
                )
            if not (0.0 <= val <= 1.0):
                raise MetricValidationError(f"Metric '{key}' is out of bounds [0.0, 1.0]: {val}")
