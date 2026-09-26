"""Reusable Spark ML Transformers for Clinical Feature Transformation.

Provides factory functions for StringIndexer, OneHotEncoder, VectorAssembler,
and StandardScaler stages configured for healthcare EHR feature processing.
"""

from typing import Any

try:
    from pyspark.ml.feature import (
        OneHotEncoder,
        StandardScaler,
        StringIndexer,
        VectorAssembler,
    )
except ImportError:
    # Allow import on environments without PySpark for inspection and testing
    OneHotEncoder = None
    StandardScaler = None
    StringIndexer = None
    VectorAssembler = None


def create_string_indexers(
    categorical_columns: list[str],
    handle_invalid: str = "keep",
    string_order_type: str = "frequencyDesc",
) -> list[Any]:
    """Create a list of StringIndexer estimators for categorical features.

    Using handleInvalid='keep' ensures that missing values or unseen categories
    during inference are placed into a separate index bucket instead of throwing exceptions.

    Args:
        categorical_columns: List of categorical feature column names.
        handle_invalid: Strategy for unseen/missing labels ('keep', 'skip', 'error').
        string_order_type: Ordering for indexing ('frequencyDesc', 'frequencyAsc', etc.).

    Returns:
        List of StringIndexer instances.
    """
    if StringIndexer is None:
        raise RuntimeError("PySpark is required to instantiate StringIndexer.")

    indexers = []
    for col in categorical_columns:
        indexers.append(
            StringIndexer(
                inputCol=col,
                outputCol=f"{col}_indexed",
                handleInvalid=handle_invalid,
                stringOrderType=string_order_type,
            )
        )
    return indexers


def create_one_hot_encoder(
    input_cols: list[str],
    output_cols: list[str],
    handle_invalid: str = "keep",
    drop_last: bool = False,
) -> Any:
    """Create a OneHotEncoder estimator for indexed categorical features.

    Args:
        input_cols: List of indexed categorical column names.
        output_cols: List of target one-hot vector column names.
        handle_invalid: Strategy for handling invalid values ('keep', 'error').
        drop_last: Whether to drop the last category (default False to keep full representation).

    Returns:
        OneHotEncoder instance.
    """
    if OneHotEncoder is None:
        raise RuntimeError("PySpark is required to instantiate OneHotEncoder.")

    return OneHotEncoder(
        inputCols=input_cols,
        outputCols=output_cols,
        handleInvalid=handle_invalid,
        dropLast=drop_last,
    )


def create_vector_assembler(
    input_cols: list[str],
    output_col: str = "assembled_features",
    handle_invalid: str = "keep",
) -> Any:
    """Create a VectorAssembler stage combining one-hot vectors and numerical features.

    Args:
        input_cols: List of column names (one-hot vector columns + numerical columns).
        output_col: Name of the output assembled vector column.
        handle_invalid: Strategy for handling invalid values ('keep', 'skip', 'error').

    Returns:
        VectorAssembler instance.
    """
    if VectorAssembler is None:
        raise RuntimeError("PySpark is required to instantiate VectorAssembler.")

    return VectorAssembler(
        inputCols=input_cols,
        outputCol=output_col,
        handleInvalid=handle_invalid,
    )


def create_standard_scaler(
    input_col: str = "assembled_features",
    output_col: str = "features",
    with_mean: bool = False,
    with_std: bool = True,
) -> Any:
    """Create a StandardScaler estimator for the assembled feature vector.

    Note: with_mean=False preserves matrix sparsity from one-hot encoding,
    while with_std=True normalizes variance across heterogeneous features.

    Args:
        input_col: Name of the input assembled vector column.
        output_col: Name of the output standardized feature vector column.
        with_mean: Whether to center data before scaling (False for sparse preservation).
        with_std: Whether to scale variance to unit standard deviation (True).

    Returns:
        StandardScaler instance.
    """
    if StandardScaler is None:
        raise RuntimeError("PySpark is required to instantiate StandardScaler.")

    return StandardScaler(
        inputCol=input_col,
        outputCol=output_col,
        withMean=with_mean,
        withStd=with_std,
    )
