"""Spark ML Clinical Feature Transformation Pipeline.

Constructs, fits, and executes the complete feature transformation pipeline:
StringIndexer -> OneHotEncoder -> VectorAssembler -> StandardScaler -> features
"""

import logging
from typing import Any

try:
    from pyspark.ml import Pipeline, PipelineModel
    from pyspark.sql import DataFrame, SparkSession
except ImportError:
    Pipeline = None
    PipelineModel = None
    DataFrame = None
    SparkSession = None

from src.features.feature_selector import (
    TARGET_COLUMN,
    get_categorical_features,
    get_numerical_features,
    validate_feature_columns,
)
from src.features.transformer import (
    create_one_hot_encoder,
    create_standard_scaler,
    create_string_indexers,
    create_vector_assembler,
)

logger = logging.getLogger(__name__)


def build_feature_pipeline(
    categorical_columns: list[str] | None = None,
    numerical_columns: list[str] | None = None,
    output_feature_col: str = "features",
    assembled_feature_col: str = "assembled_features",
    handle_invalid: str = "keep",
    drop_last: bool = False,
    with_mean: bool = False,
    with_std: bool = True,
) -> Any:
    """Build an unfitted PySpark ML Pipeline for feature transformation.

    Transformation Stages:
    1. StringIndexer: Encodes each categorical string column into numeric index.
    2. OneHotEncoder: Encodes indexed columns into one-hot binary sparse vectors.
    3. VectorAssembler: Combines one-hot vectors and continuous numerical features.
    4. StandardScaler: Normalizes feature variance while preserving vector sparsity.

    Args:
        categorical_columns: List of categorical column names (default: CATEGORICAL_FEATURES).
        numerical_columns: List of numerical column names (default: NUMERICAL_FEATURES).
        output_feature_col: Name of the final standardized feature vector column.
        assembled_feature_col: Intermediate vector column name before scaling.
        handle_invalid: Handling strategy for invalid/unseen categories ('keep', 'skip', 'error').
        drop_last: Whether to drop the last one-hot category.
        with_mean: Whether StandardScaler centers data (False for sparsity).
        with_std: Whether StandardScaler scales variance to unit standard deviation (True).

    Returns:
        pyspark.ml.Pipeline instance with configured transformation stages.
    """
    if Pipeline is None:
        raise RuntimeError("PySpark is required to build the feature pipeline.")

    cat_cols = list(
        categorical_columns if categorical_columns is not None else get_categorical_features()
    )
    num_cols = list(
        numerical_columns if numerical_columns is not None else get_numerical_features()
    )

    # Stage 1: StringIndexers
    indexers = create_string_indexers(
        categorical_columns=cat_cols,
        handle_invalid=handle_invalid,
    )

    # Stage 2: OneHotEncoder
    indexed_cols = [f"{col}_indexed" for col in cat_cols]
    encoded_cols = [f"{col}_vec" for col in cat_cols]
    encoder = create_one_hot_encoder(
        input_cols=indexed_cols,
        output_cols=encoded_cols,
        handle_invalid=handle_invalid,
        drop_last=drop_last,
    )

    # Stage 3: VectorAssembler
    assembler_inputs = encoded_cols + num_cols
    assembler = create_vector_assembler(
        input_cols=assembler_inputs,
        output_col=assembled_feature_col,
        handle_invalid=handle_invalid,
    )

    # Stage 4: StandardScaler
    scaler = create_standard_scaler(
        input_col=assembled_feature_col,
        output_col=output_feature_col,
        with_mean=with_mean,
        with_std=with_std,
    )

    # Combine all stages in sequential order
    stages = indexers + [encoder, assembler, scaler]
    pipeline = Pipeline(stages=stages)
    logger.info(
        "Built feature pipeline with %d total stages (%d indexers, 1 encoder, 1 assembler, 1 scaler).",
        len(stages),
        len(indexers),
    )
    return pipeline


def fit_feature_pipeline(
    df: Any,
    pipeline: Any | None = None,
    require_target: bool = True,
) -> Any:
    """Validate DataFrame schema and fit the feature transformation pipeline.

    Args:
        df: Input PySpark DataFrame (e.g., loaded from patient_features_view).
        pipeline: Optional pre-constructed Pipeline. If None, builds default pipeline.
        require_target: Whether to require presence of readmission_target column.

    Returns:
        Fitted pyspark.ml.PipelineModel.
    """
    logger.info("Validating schema before fitting feature pipeline...")
    validate_feature_columns(df, require_target=require_target)

    if pipeline is None:
        pipeline = build_feature_pipeline()

    logger.info(
        "Fitting feature transformation pipeline on DataFrame (%d columns)...", len(df.columns)
    )
    model = pipeline.fit(df)
    logger.info("Feature transformation pipeline fitted successfully.")
    return model


def transform_features(
    df: Any,
    model: Any,
    feature_col: str = "features",
    target_col: str = TARGET_COLUMN,
    include_identifiers: bool = False,
) -> Any:
    """Transform input DataFrame using fitted PipelineModel and select essential columns.

    Args:
        df: PySpark DataFrame to transform.
        model: Fitted PipelineModel.
        feature_col: Name of final output feature vector column.
        target_col: Name of target column (preserved if present).
        include_identifiers: Whether to retain encounter_id and patient_nbr alongside features.

    Returns:
        Transformed PySpark DataFrame.
    """
    transformed = model.transform(df)

    # Select clean projection
    select_cols = []
    if include_identifiers:
        for ident in ["encounter_id", "patient_nbr"]:
            if ident in transformed.columns:
                select_cols.append(ident)

    if feature_col in transformed.columns:
        select_cols.append(feature_col)

    if target_col in transformed.columns:
        select_cols.append(target_col)

    if select_cols:
        return transformed.select(select_cols)
    return transformed


def load_patient_features_view(
    spark: Any,
    hive_view: str = "readmission.patient_features_view",
) -> Any:
    """Load the patient features dataset from Hive view or Spark catalog.

    Args:
        spark: Active SparkSession.
        hive_view: Qualified Hive view/table name.

    Returns:
        PySpark DataFrame.
    """
    logger.info("Loading patient features from %s...", hive_view)
    return spark.table(hive_view)
