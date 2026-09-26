"""Data integrity, schema, and statistical validation for preprocessed clinical datasets."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyspark.sql import DataFrame
else:
    try:
        from pyspark.sql import DataFrame
    except ImportError:
        DataFrame = Any

EXPECTED_RAW_COLUMNS: list[str] = [
    "encounter_id",
    "patient_nbr",
    "race",
    "gender",
    "age",
    "weight",
    "admission_type_id",
    "discharge_disposition_id",
    "admission_source_id",
    "time_in_hospital",
    "payer_code",
    "medical_specialty",
    "num_lab_procedures",
    "num_procedures",
    "num_medications",
    "number_outpatient",
    "number_emergency",
    "number_inpatient",
    "diag_1",
    "diag_2",
    "diag_3",
    "number_diagnoses",
    "max_glu_serum",
    "a1cresult",
    "metformin",
    "repaglinide",
    "nateglinide",
    "chlorpropamide",
    "glimepiride",
    "acetohexamide",
    "glipizide",
    "glyburide",
    "tolbutamide",
    "pioglitazone",
    "rosiglitazone",
    "acarbose",
    "miglitol",
    "troglitazone",
    "tolazamide",
    "examide",
    "citoglipton",
    "insulin",
    "glyburide_metformin",
    "glipizide_metformin",
    "glimepiride_pioglitazone",
    "metformin_rosiglitazone",
    "metformin_pioglitazone",
    "change",
    "diabetesMed",
    "readmitted",
]

REQUIRED_CLEAN_COLUMNS: list[str] = EXPECTED_RAW_COLUMNS + [
    "age_midpoint",
    "insulin_flag",
    "medication_change_flag",
    "diabetes_med_flag",
    "readmission_target",
]


class ValidationError(Exception):
    """Base exception for data validation failures."""


class SchemaValidationError(ValidationError):
    """Exception raised when dataset schema does not conform to specification."""


class DataIntegrityError(ValidationError):
    """Exception raised when data values violate integrity constraints."""


def normalize_column_name(col: str) -> str:
    """Normalize column name for case-insensitive and delimiter-agnostic comparison."""
    return col.lower().replace("-", "_")


def validate_input_columns(
    df: DataFrame,
    expected_columns: Sequence[str] | None = None,
) -> None:
    """Validate that the input DataFrame contains all expected raw columns.

    Args:
        df: Input PySpark DataFrame.
        expected_columns: Sequence of required column names.

    Raises:
        SchemaValidationError: If any expected columns are missing from the DataFrame.
    """
    expected = expected_columns if expected_columns is not None else EXPECTED_RAW_COLUMNS
    actual_cols_normalized = {normalize_column_name(c): c for c in df.columns}

    missing_cols = [c for c in expected if normalize_column_name(c) not in actual_cols_normalized]

    if missing_cols:
        raise SchemaValidationError(
            f"Input DataFrame is missing {len(missing_cols)} expected column(s): {missing_cols}"
        )


def validate_output_columns(
    df: DataFrame,
    required_columns: Sequence[str] | None = None,
) -> None:
    """Validate that the cleaned DataFrame contains all required output and engineered columns.

    Args:
        df: Cleaned PySpark DataFrame.
        required_columns: Sequence of required column names.

    Raises:
        SchemaValidationError: If any required columns are missing from the DataFrame.
    """
    required = required_columns if required_columns is not None else REQUIRED_CLEAN_COLUMNS
    actual_cols_normalized = {normalize_column_name(c): c for c in df.columns}

    missing_cols = [c for c in required if normalize_column_name(c) not in actual_cols_normalized]

    if missing_cols:
        raise SchemaValidationError(
            f"Output DataFrame is missing {len(missing_cols)} required column(s): {missing_cols}"
        )


def validate_target_values(
    df: DataFrame,
    target_col: str = "readmission_target",
) -> dict[int, int]:
    """Validate that the target column has no NULLs and contains only binary values {0, 1}.

    Args:
        df: PySpark DataFrame.
        target_col: Name of the binary target column.

    Returns:
        dict[int, int]: Value distribution counts {0: count_0, 1: count_1}.

    Raises:
        DataIntegrityError: If target values contain NULLs or values outside {0, 1}.
    """
    if target_col not in df.columns:
        raise SchemaValidationError(f"Target column '{target_col}' not found in DataFrame.")

    agg_df = df.groupBy(target_col).count().collect()

    distribution: dict[Any, int] = {row[target_col]: row["count"] for row in agg_df}

    if None in distribution:
        raise DataIntegrityError(
            f"Target column '{target_col}' contains {distribution[None]} NULL values."
        )

    invalid_keys = [k for k in distribution if k not in (0, 1)]
    if invalid_keys:
        raise DataIntegrityError(
            f"Target column '{target_col}' contains invalid non-binary values: {invalid_keys}"
        )

    return {int(k): v for k, v in distribution.items()}


def validate_age_range(
    df: DataFrame,
    age_col: str = "age_midpoint",
    min_age: int = 0,
    max_age: int = 120,
) -> dict[str, int]:
    """Validate that all age midpoint values fall within valid physiological bounds [min_age, max_age].

    Args:
        df: PySpark DataFrame.
        age_col: Name of the numeric age midpoint column.
        min_age: Minimum acceptable age.
        max_age: Maximum acceptable age.

    Returns:
        dict[str, int]: Age statistics summary.

    Raises:
        DataIntegrityError: If any age values are NULL or outside the allowed range.
    """
    from pyspark.sql import functions as F

    if age_col not in df.columns:
        raise SchemaValidationError(f"Age column '{age_col}' not found in DataFrame.")

    null_count = df.filter(F.col(age_col).isNull()).count()
    if null_count > 0:
        raise DataIntegrityError(f"Age midpoint column '{age_col}' contains {null_count} NULLs.")

    out_of_bounds = df.filter((F.col(age_col) < min_age) | (F.col(age_col) > max_age)).count()
    if out_of_bounds > 0:
        raise DataIntegrityError(
            f"Age midpoint column '{age_col}' contains {out_of_bounds} values outside [{min_age}, {max_age}]."
        )

    stats = df.select(
        F.min(age_col).alias("min_age"),
        F.max(age_col).alias("max_age"),
        F.count(age_col).alias("count"),
    ).collect()[0]

    return {
        "min_age": int(stats["min_age"]),
        "max_age": int(stats["max_age"]),
        "total_records": int(stats["count"]),
    }


def validate_binary_flags(
    df: DataFrame,
    flag_cols: Sequence[str] = (
        "insulin_flag",
        "medication_change_flag",
        "diabetes_med_flag",
    ),
) -> dict[str, dict[int, int]]:
    """Validate that specified flag columns are non-null and strictly binary {0, 1}.

    Args:
        df: PySpark DataFrame.
        flag_cols: Sequence of binary flag column names.

    Returns:
        dict[str, dict[int, int]]: Map of column names to their {0: count, 1: count} distributions.

    Raises:
        DataIntegrityError: If any flag column has NULLs or non-binary values.
    """
    results: dict[str, dict[int, int]] = {}

    for flag_col in flag_cols:
        if flag_col not in df.columns:
            raise SchemaValidationError(f"Flag column '{flag_col}' not found in DataFrame.")

        agg_df = df.groupBy(flag_col).count().collect()
        dist: dict[Any, int] = {row[flag_col]: row["count"] for row in agg_df}

        if None in dist:
            raise DataIntegrityError(f"Flag column '{flag_col}' contains {dist[None]} NULLs.")

        invalid_keys = [k for k in dist if k not in (0, 1)]
        if invalid_keys:
            raise DataIntegrityError(
                f"Flag column '{flag_col}' contains invalid non-binary values: {invalid_keys}"
            )

        results[flag_col] = {int(k): v for k, v in dist.items()}

    return results


def validate_no_terminal_discharges(
    df: DataFrame,
    discharge_col: str = "discharge_disposition_id",
    terminal_ids: Sequence[int] = (11, 13, 14, 19, 20, 21),
) -> None:
    """Validate that no terminal discharge disposition records exist in the cleaned DataFrame.

    Args:
        df: PySpark DataFrame.
        discharge_col: Name of the discharge disposition column.
        terminal_ids: Sequence of terminal discharge IDs.

    Raises:
        DataIntegrityError: If any terminal discharge records remain.
    """
    from pyspark.sql import functions as F

    if discharge_col not in df.columns:
        return

    terminal_count = df.filter(F.col(discharge_col).cast("int").isin(list(terminal_ids))).count()

    if terminal_count > 0:
        raise DataIntegrityError(
            f"Found {terminal_count} forbidden terminal discharge records in cleaned data."
        )


def validate_cleaned_dataframe(
    df: DataFrame,
    expected_input_count: int | None = None,
) -> dict[str, Any]:
    """Execute complete validation suite on the cleaned and encoded DataFrame.

    Args:
        df: Cleaned and encoded PySpark DataFrame.
        expected_input_count: Optional row count of the raw input dataset for verification.

    Returns:
        dict[str, Any]: Validation summary report containing counts and distributions.

    Raises:
        ValidationError: If any validation checks fail.
    """
    validate_output_columns(df)
    validate_no_terminal_discharges(df)

    target_dist = validate_target_values(df, target_col="readmission_target")
    age_stats = validate_age_range(df, age_col="age_midpoint")
    flag_dists = validate_binary_flags(df)

    output_count = df.count()
    removed_count = (
        expected_input_count - output_count if expected_input_count is not None else None
    )

    return {
        "status": "PASSED",
        "output_row_count": output_count,
        "input_row_count": expected_input_count,
        "rows_removed": removed_count,
        "target_distribution": target_dist,
        "age_statistics": age_stats,
        "flag_distributions": flag_dists,
        "total_columns": len(df.columns),
    }
