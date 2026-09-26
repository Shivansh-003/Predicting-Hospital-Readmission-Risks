"""Distributed Model Training Engine for Spark ML Classifiers.

Implements model training, deterministic dataset splitting, persistence,
and verification for:
1. Logistic Regression
2. Random Forest
3. Decision Tree
4. Gradient Boosted Trees (GBT)
"""

import logging
import time
from typing import Any

try:
    from pyspark import StorageLevel
    from pyspark.ml.classification import (
        DecisionTreeClassificationModel,
        DecisionTreeClassifier,
        GBTClassificationModel,
        GBTClassifier,
        LogisticRegression,
        LogisticRegressionModel,
        RandomForestClassificationModel,
        RandomForestClassifier,
    )
    from pyspark.sql import DataFrame
except ImportError:
    StorageLevel = None
    DecisionTreeClassificationModel = None
    DecisionTreeClassifier = None
    GBTClassificationModel = None
    GBTClassifier = None
    LogisticRegression = None
    LogisticRegressionModel = None
    RandomForestClassificationModel = None
    RandomForestClassifier = None
    DataFrame = None

from src.models.model_config import (
    DEFAULT_FEATURES_COL,
    DEFAULT_LABEL_COL,
    ModelConfig,
    get_all_model_configs,
    get_model_config,
)

logger = logging.getLogger(__name__)


def split_data(
    df: Any,
    train_ratio: float = 0.8,
    test_ratio: float = 0.2,
    seed: int = 42,
) -> tuple[Any, Any]:
    """Split DataFrame into deterministic training and test sets using Spark native randomSplit.

    Args:
        df: Input PySpark DataFrame containing features and target.
        train_ratio: Proportion of data allocated for training (default: 0.8).
        test_ratio: Proportion of data allocated for testing (default: 0.2).
        seed: Random seed for deterministic partition splitting (default: 42).

    Returns:
        Tuple of (train_df, test_df).

    Raises:
        ValueError: If ratios do not sum to 1.0 or required columns are missing.
    """
    if not (0.0 < train_ratio < 1.0 and 0.0 < test_ratio < 1.0):
        raise ValueError(
            f"Train and test ratios must be between 0 and 1. Got train={train_ratio}, test={test_ratio}"
        )

    # Validate essential columns exist before split
    cols = df.columns
    if DEFAULT_FEATURES_COL not in cols:
        raise ValueError(
            f"Required features column '{DEFAULT_FEATURES_COL}' not found in DataFrame."
        )
    if DEFAULT_LABEL_COL not in cols:
        raise ValueError(f"Required label column '{DEFAULT_LABEL_COL}' not found in DataFrame.")

    train_df, test_df = df.randomSplit([train_ratio, test_ratio], seed=seed)
    return train_df, test_df


def build_estimator(config: ModelConfig) -> Any:
    """Instantiate the appropriate PySpark ML Estimator according to ModelConfig.

    Args:
        config: ModelConfig instance defining algorithm and hyperparameters.

    Returns:
        Configured PySpark ML Estimator instance.

    Raises:
        RuntimeError: If PySpark is not installed.
        ValueError: If model name is unrecognized.
    """
    if LogisticRegression is None:
        raise RuntimeError("PySpark ML is required to instantiate model estimators.")

    name = config.name
    params = config.hyperparameters
    features_col = config.features_col
    label_col = config.label_col

    if name == "logistic_regression":
        return LogisticRegression(
            featuresCol=features_col,
            labelCol=label_col,
            maxIter=params.get("maxIter", 100),
            regParam=params.get("regParam", 0.01),
        )

    elif name == "random_forest":
        return RandomForestClassifier(
            featuresCol=features_col,
            labelCol=label_col,
            numTrees=params.get("numTrees", 50),
            maxDepth=params.get("maxDepth", 8),
            seed=42,
        )

    elif name == "decision_tree":
        return DecisionTreeClassifier(
            featuresCol=features_col,
            labelCol=label_col,
            maxDepth=params.get("maxDepth", 6),
            minInstancesPerNode=params.get("minInstancesPerNode", 3),
            seed=42,
        )

    elif name == "gbt":
        return GBTClassifier(
            featuresCol=features_col,
            labelCol=label_col,
            maxIter=params.get("maxIter", 30),
            maxDepth=params.get("maxDepth", 5),
            stepSize=params.get("stepSize", 0.1),
            seed=42,
        )

    else:
        raise ValueError(f"Unsupported model name: '{name}'")


def train_model(
    model_name: str,
    train_df: Any,
    config: ModelConfig | None = None,
) -> tuple[Any, float]:
    """Train a single Spark ML model on the provided training DataFrame.

    Args:
        model_name: Canonical name of the model to train.
        train_df: Training PySpark DataFrame containing features and label.
        config: Optional ModelConfig override. If None, default configuration is used.

    Returns:
        Tuple of (fitted_model, training_duration_seconds).
    """
    if config is None:
        config = get_model_config(model_name)

    logger.info("Building estimator for '%s'...", config.name)
    estimator = build_estimator(config)

    logger.info("Fitting '%s' on training data...", config.name)
    start_time = time.perf_counter()
    fitted_model = estimator.fit(train_df)
    duration = time.perf_counter() - start_time
    logger.info("Fitted '%s' in %.2f seconds.", config.name, duration)

    return fitted_model, duration


def save_model(model: Any, path: str, overwrite: bool = True) -> None:
    """Persist a fitted Spark ML model artifact to storage.

    Args:
        model: Fitted Spark ML model.
        path: Target filesystem or HDFS path.
        overwrite: Whether to overwrite existing directory.
    """
    writer = model.write()
    if overwrite:
        writer = writer.overwrite()
    writer.save(path)
    logger.info("Persisted model artifact to: %s", path)


def load_model(model_name: str, path: str) -> Any:
    """Load a persisted Spark ML model artifact from storage.

    Args:
        model_name: Canonical name of the model ('logistic_regression', 'random_forest', etc.).
        path: Path to the persisted model directory.

    Returns:
        Loaded PySpark ML model instance.

    Raises:
        RuntimeError: If PySpark is not installed.
        ValueError: If model name is unrecognized.
    """
    if LogisticRegressionModel is None:
        raise RuntimeError("PySpark ML is required to load model artifacts.")

    if model_name == "logistic_regression":
        return LogisticRegressionModel.load(path)
    elif model_name == "random_forest":
        return RandomForestClassificationModel.load(path)
    elif model_name == "decision_tree":
        return DecisionTreeClassificationModel.load(path)
    elif model_name == "gbt":
        return GBTClassificationModel.load(path)
    else:
        raise ValueError(f"Unsupported model name for loading: '{model_name}'")


def train_all_models(
    train_df: Any,
    test_df: Any | None = None,
    output_base_dir: str = "models",
    save_artifacts: bool = True,
) -> dict[str, dict[str, Any]]:
    """Train, time, persist, and verify all four Spark ML models deterministically.

    Workflow:
    1. Persists training/test DataFrames in Spark memory/disk.
    2. Iterates over Logistic Regression, Random Forest, Decision Tree, and GBT.
    3. Fits each model on the shared training partition.
    4. Measures and records elapsed training execution time.
    5. Saves model artifacts under output_base_dir/{model_name}/.
    6. Loads and validates saved artifacts.
    7. Cleans up cached DataFrames.

    Args:
        train_df: PySpark DataFrame containing training partitions.
        test_df: Optional PySpark DataFrame containing test partitions.
        output_base_dir: Base directory for model persistence.
        save_artifacts: Whether to write model artifacts to disk.

    Returns:
        Dictionary mapping model names to training metadata records.
    """
    # 1. Persist DataFrame to avoid recomputing upstream feature pipeline
    logger.info("Persisting training DataFrame...")
    if StorageLevel is not None:
        train_df.persist(StorageLevel.MEMORY_AND_DISK)
    else:
        train_df.cache()

    train_count = train_df.count()
    test_count = test_df.count() if test_df is not None else 0
    logger.info("Training set rows: %d | Test set rows: %d", train_count, test_count)

    # Inspect feature vector dimension from first record
    sample_first = train_df.select(DEFAULT_FEATURES_COL).first()
    feature_dimension = sample_first[DEFAULT_FEATURES_COL].size if sample_first else 0

    results: dict[str, dict[str, Any]] = {}
    configs = get_all_model_configs()

    try:
        for config in configs:
            name = config.name
            logger.info("==========================================")
            logger.info("Starting training for model: %s", name)
            logger.info("Hyperparameters: %s", config.hyperparameters)

            fitted_model, duration = train_model(name, train_df, config=config)

            artifact_path = f"{output_base_dir}/{name}" if output_base_dir else config.artifact_path
            loaded_verified = False

            if save_artifacts:
                save_model(fitted_model, artifact_path, overwrite=True)
                # Verify round-trip loadability
                loaded_model = load_model(name, artifact_path)
                loaded_verified = loaded_model is not None

                # Test transform on test partition if available
                if test_df is not None and loaded_model is not None:
                    test_predictions = loaded_model.transform(test_df.limit(10))
                    if "prediction" in test_predictions.columns:
                        logger.info("Verified '%s' transformation on test partition.", name)

            results[name] = {
                "model_name": name,
                "estimator": config.estimator_name,
                "hyperparameters": config.hyperparameters,
                "features_col": config.features_col,
                "label_col": config.label_col,
                "train_row_count": train_count,
                "test_row_count": test_count,
                "feature_dimension": feature_dimension,
                "training_duration_seconds": round(duration, 3),
                "artifact_path": artifact_path if save_artifacts else None,
                "model_saved": save_artifacts,
                "model_loaded_verified": loaded_verified,
            }
            logger.info(
                "Completed '%s' training in %.3fs (Artifact: %s)",
                name,
                duration,
                artifact_path if save_artifacts else "N/A",
            )

    finally:
        logger.info("Releasing cached training DataFrame...")
        train_df.unpersist()
        if test_df is not None:
            test_df.unpersist()

    return results
