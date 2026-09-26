"""PySpark data cleaning operations for clinical encounter records."""

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

TERMINAL_DISCHARGE_DISPOSITION_IDS: tuple[int, ...] = (11, 13, 14, 19, 20, 21)
INVALID_GENDERS: tuple[str, ...] = ("Unknown/Invalid",)
DEFAULT_MISSING_TOKEN: str = "?"


def replace_missing_tokens(
    df: DataFrame,
    missing_token: str = DEFAULT_MISSING_TOKEN,
    target_columns: Sequence[str] | None = None,
) -> DataFrame:
    """Replace placeholder missing-value tokens with standard SQL NULL (None).

    Args:
        df: Input PySpark DataFrame.
        missing_token: Character or string token representing missing values.
        target_columns: Optional subset of columns to process. If None, processes all
            string-type columns in the DataFrame.

    Returns:
        DataFrame: PySpark DataFrame with placeholder tokens replaced by NULLs.
    """
    from pyspark.sql import functions as F
    from pyspark.sql.types import StringType

    cols_to_process = (
        list(target_columns)
        if target_columns is not None
        else [f.name for f in df.schema.fields if isinstance(f.dataType, StringType)]
    )

    result_df = df
    for col_name in cols_to_process:
        if col_name in df.columns:
            result_df = result_df.withColumn(
                col_name,
                F.when(F.trim(F.col(col_name)) == missing_token, F.lit(None)).otherwise(
                    F.col(col_name)
                ),
            )

    return result_df


def filter_terminal_discharges(
    df: DataFrame,
    discharge_col: str = "discharge_disposition_id",
    terminal_ids: Sequence[int] = TERMINAL_DISCHARGE_DISPOSITION_IDS,
) -> DataFrame:
    """Filter out terminal encounter records where readmission is not applicable.

    Discharge disposition IDs representing expiration (deceased) or hospice discharge
    are non-viable for 30-day readmission prediction.

    Args:
        df: Input PySpark DataFrame.
        discharge_col: Name of the discharge disposition ID column.
        terminal_ids: Sequence of discharge disposition IDs to exclude.

    Returns:
        DataFrame: Filtered DataFrame containing only non-terminal encounters.
    """
    from pyspark.sql import functions as F

    return df.filter(~F.col(discharge_col).cast("int").isin(list(terminal_ids)))


def filter_invalid_demographics(
    df: DataFrame,
    gender_col: str = "gender",
    invalid_genders: Sequence[str] = INVALID_GENDERS,
) -> DataFrame:
    """Filter out records with invalid or unidentifiable demographic attributes.

    Args:
        df: Input PySpark DataFrame.
        gender_col: Name of the gender column.
        invalid_genders: Sequence of invalid gender tokens to exclude.

    Returns:
        DataFrame: Filtered DataFrame containing valid demographic records.
    """
    from pyspark.sql import functions as F

    return df.filter(
        F.col(gender_col).isNotNull() & (~F.col(gender_col).isin(list(invalid_genders)))
    )


def clean_patient_records(
    df: DataFrame,
    missing_token: str = DEFAULT_MISSING_TOKEN,
    terminal_ids: Sequence[int] = TERMINAL_DISCHARGE_DISPOSITION_IDS,
    invalid_genders: Sequence[str] = INVALID_GENDERS,
) -> DataFrame:
    """Execute complete deterministic data cleaning pipeline on patient encounter records.

    Operations:
        1. Remove terminal discharge disposition records (expired/hospice).
        2. Remove invalid demographic records (unknown gender).
        3. Convert '?' missing tokens to standard SQL NULLs across all string columns.

    Args:
        df: Raw PySpark DataFrame.
        missing_token: Missing value placeholder token.
        terminal_ids: Non-viable discharge disposition IDs.
        invalid_genders: Non-viable demographic gender tokens.

    Returns:
        DataFrame: Cleaned PySpark DataFrame.
    """
    df_filtered_discharges = filter_terminal_discharges(
        df, discharge_col="discharge_disposition_id", terminal_ids=terminal_ids
    )

    df_filtered_demographics = filter_invalid_demographics(
        df_filtered_discharges, gender_col="gender", invalid_genders=invalid_genders
    )

    df_cleaned = replace_missing_tokens(df_filtered_demographics, missing_token=missing_token)

    return df_cleaned
