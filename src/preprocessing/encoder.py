"""Feature encoding and target transformation functions for clinical encounter data."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyspark.sql import DataFrame
else:
    try:
        from pyspark.sql import DataFrame
    except ImportError:
        DataFrame = Any

INSULIN_ACTIVE_STATUSES: tuple[str, ...] = ("Up", "Down", "Steady")
CHANGE_ACTIVE_STATUS: str = "Ch"
DIABETES_MED_ACTIVE_STATUS: str = "Yes"


def parse_age_bracket_midpoint(age_str: str | None) -> int | None:
    """Parse an age interval string generically and compute its numeric midpoint.

    Supports interval formats such as '[0-10)', '[10-20)', '20-30', '[80-90]', etc.

    Args:
        age_str: Raw age interval string (e.g., '[10-20)').

    Returns:
        int | None: Numeric midpoint (e.g., 15) or None if unparseable/null.
    """
    if age_str is None:
        return None

    match = re.search(r"(\d+)\s*-\s*(\d+)", str(age_str))
    if not match:
        return None

    lower = int(match.group(1))
    upper = int(match.group(2))
    return (lower + upper) // 2


def encode_age_midpoint(
    df: DataFrame,
    input_col: str = "age",
    output_col: str = "age_midpoint",
) -> DataFrame:
    """Transform age interval brackets into generic numeric midpoint values in PySpark.

    Extracts lower and upper bound digits from any bracket format (e.g. '[0-10)' -> 5,
    '[50-60)' -> 55, '[90-100)' -> 95) using regex extraction and computes the midpoint.

    Args:
        df: Input PySpark DataFrame.
        input_col: Name of the raw age bracket column.
        output_col: Name of the resulting integer midpoint column.

    Returns:
        DataFrame: DataFrame with the new numeric age midpoint column.
    """
    from pyspark.sql import functions as F

    lower_bound = F.regexp_extract(F.col(input_col), r"(\d+)\s*-\s*(\d+)", 1).cast("int")
    upper_bound = F.regexp_extract(F.col(input_col), r"(\d+)\s*-\s*(\d+)", 2).cast("int")

    midpoint_expr = ((lower_bound + upper_bound) / 2).cast("int")

    return df.withColumn(
        output_col,
        F.when(
            lower_bound.isNotNull() & upper_bound.isNotNull() & (F.length(F.col(input_col)) > 0),
            midpoint_expr,
        ).otherwise(F.lit(None).cast("int")),
    )


def encode_insulin_flag(
    df: DataFrame,
    input_col: str = "insulin",
    output_col: str = "insulin_flag",
    active_statuses: Sequence[str] = INSULIN_ACTIVE_STATUSES,
) -> DataFrame:
    """Create a binary flag indicating whether insulin was administered or adjusted.

    Values 'Up', 'Down', and 'Steady' map to 1 (active insulin regimen).
    Value 'No' maps to 0.

    Args:
        df: Input PySpark DataFrame.
        input_col: Name of the raw insulin medication column.
        output_col: Name of the resulting integer flag column.
        active_statuses: Sequence of statuses indicating active insulin use.

    Returns:
        DataFrame: DataFrame with the binary insulin flag column.
    """
    from pyspark.sql import functions as F

    return df.withColumn(
        output_col,
        F.when(F.col(input_col).isin(list(active_statuses)), F.lit(1))
        .otherwise(F.lit(0))
        .cast("int"),
    )


def encode_medication_change_flag(
    df: DataFrame,
    input_col: str = "change",
    output_col: str = "medication_change_flag",
    active_status: str = CHANGE_ACTIVE_STATUS,
) -> DataFrame:
    """Create a binary flag indicating whether diabetic medication was altered during encounter.

    Value 'Ch' maps to 1 (dosage or medication changed).
    Value 'No' maps to 0.

    Args:
        df: Input PySpark DataFrame.
        input_col: Name of the raw change column.
        output_col: Name of the resulting integer flag column.
        active_status: Token representing a medication modification.

    Returns:
        DataFrame: DataFrame with the binary medication change flag column.
    """
    from pyspark.sql import functions as F

    return df.withColumn(
        output_col,
        F.when(F.col(input_col) == active_status, F.lit(1)).otherwise(F.lit(0)).cast("int"),
    )


def encode_diabetes_med_flag(
    df: DataFrame,
    input_col: str = "diabetesMed",
    output_col: str = "diabetes_med_flag",
    active_status: str = DIABETES_MED_ACTIVE_STATUS,
) -> DataFrame:
    """Create a binary flag indicating whether any diabetic medication was prescribed.

    Value 'Yes' maps to 1.
    Value 'No' maps to 0.

    Args:
        df: Input PySpark DataFrame.
        input_col: Name of the raw diabetesMed column.
        output_col: Name of the resulting integer flag column.
        active_status: Token representing prescription.

    Returns:
        DataFrame: DataFrame with the binary diabetes medication flag column.
    """
    from pyspark.sql import functions as F

    return df.withColumn(
        output_col,
        F.when(F.col(input_col) == active_status, F.lit(1)).otherwise(F.lit(0)).cast("int"),
    )


def encode_readmission_target(
    df: DataFrame,
    input_col: str = "readmitted",
    output_col: str = "readmission_target",
) -> DataFrame:
    """Encode the 30-day all-cause hospital readmission binary target.

    Mapping:
        '<30' -> 1 (Readmitted within 30 days — positive class)
        '>30' -> 0 (Readmitted after 30 days — negative class for 30-day window)
        'NO'  -> 0 (No readmission recorded — negative class)

    Args:
        df: Input PySpark DataFrame.
        input_col: Name of the raw readmission status column.
        output_col: Name of the resulting integer target column.

    Returns:
        DataFrame: DataFrame with the binary target column.
    """
    from pyspark.sql import functions as F

    return df.withColumn(
        output_col,
        F.when(F.col(input_col) == "<30", F.lit(1))
        .when(F.col(input_col).isin([">30", "NO"]), F.lit(0))
        .otherwise(F.lit(None).cast("int"))
        .cast("int"),
    )


def encode_features(df: DataFrame) -> DataFrame:
    """Apply all feature encoding and target derivation transformations in sequence.

    Args:
        df: Cleaned PySpark DataFrame.

    Returns:
        DataFrame: Enriched PySpark DataFrame with numeric age, medication flags,
            and binary readmission target.
    """
    df_encoded = encode_age_midpoint(df, input_col="age", output_col="age_midpoint")
    df_encoded = encode_insulin_flag(df_encoded, input_col="insulin", output_col="insulin_flag")
    df_encoded = encode_medication_change_flag(
        df_encoded, input_col="change", output_col="medication_change_flag"
    )
    df_encoded = encode_diabetes_med_flag(
        df_encoded, input_col="diabetesMed", output_col="diabetes_med_flag"
    )
    df_encoded = encode_readmission_target(
        df_encoded, input_col="readmitted", output_col="readmission_target"
    )

    return df_encoded
