"""Model Configuration and Hyperparameter Specifications.

Defines deterministic configurations and hyperparameters for Spark ML classifiers:
1. Logistic Regression
2. Random Forest
3. Decision Tree
4. Gradient Boosted Trees (GBT)
"""

from dataclasses import dataclass, field
from typing import Any

DEFAULT_FEATURES_COL: str = "features"
DEFAULT_LABEL_COL: str = "readmission_target"

MODEL_ORDER: tuple[str, ...] = (
    "logistic_regression",
    "random_forest",
    "decision_tree",
    "gbt",
)


@dataclass(frozen=True)
class ModelConfig:
    """Immutable configuration and hyperparameter container for a Spark ML model."""

    name: str
    estimator_name: str
    features_col: str = DEFAULT_FEATURES_COL
    label_col: str = DEFAULT_LABEL_COL
    hyperparameters: dict[str, Any] = field(default_factory=dict)
    artifact_path: str = ""


# -----------------------------------------------------------------------------
# Deterministic Model Specifications
# -----------------------------------------------------------------------------
LOGISTIC_REGRESSION_CONFIG = ModelConfig(
    name="logistic_regression",
    estimator_name="LogisticRegression",
    features_col=DEFAULT_FEATURES_COL,
    label_col=DEFAULT_LABEL_COL,
    hyperparameters={
        "maxIter": 100,
        "regParam": 0.01,
    },
    artifact_path="models/logistic_regression",
)

RANDOM_FOREST_CONFIG = ModelConfig(
    name="random_forest",
    estimator_name="RandomForestClassifier",
    features_col=DEFAULT_FEATURES_COL,
    label_col=DEFAULT_LABEL_COL,
    hyperparameters={
        "numTrees": 50,
        "maxDepth": 8,
    },
    artifact_path="models/random_forest",
)

DECISION_TREE_CONFIG = ModelConfig(
    name="decision_tree",
    estimator_name="DecisionTreeClassifier",
    features_col=DEFAULT_FEATURES_COL,
    label_col=DEFAULT_LABEL_COL,
    hyperparameters={
        "maxDepth": 6,
        "minInstancesPerNode": 3,
    },
    artifact_path="models/decision_tree",
)

GBT_CONFIG = ModelConfig(
    name="gbt",
    estimator_name="GBTClassifier",
    features_col=DEFAULT_FEATURES_COL,
    label_col=DEFAULT_LABEL_COL,
    hyperparameters={
        "maxIter": 30,
        "maxDepth": 5,
        "stepSize": 0.1,
    },
    artifact_path="models/gbt",
)

MODEL_CONFIGS: dict[str, ModelConfig] = {
    "logistic_regression": LOGISTIC_REGRESSION_CONFIG,
    "random_forest": RANDOM_FOREST_CONFIG,
    "decision_tree": DECISION_TREE_CONFIG,
    "gbt": GBT_CONFIG,
}


def get_model_names() -> list[str]:
    """Return the deterministic list of supported model names in execution order."""
    return list(MODEL_ORDER)


def get_model_config(model_name: str) -> ModelConfig:
    """Retrieve the configuration object for a specific model.

    Args:
        model_name: Canonical name of the model ('logistic_regression', 'random_forest', etc.).

    Returns:
        ModelConfig dataclass instance.

    Raises:
        KeyError: If model_name is not registered in MODEL_CONFIGS.
    """
    if model_name not in MODEL_CONFIGS:
        raise KeyError(
            f"Unknown model name '{model_name}'. Available models: {list(MODEL_CONFIGS.keys())}"
        )
    return MODEL_CONFIGS[model_name]


def get_all_model_configs() -> list[ModelConfig]:
    """Return list of all model configurations following deterministic model order."""
    return [MODEL_CONFIGS[name] for name in MODEL_ORDER]
