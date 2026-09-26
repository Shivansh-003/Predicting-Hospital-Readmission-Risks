"""Clinical Feature Selector for Hospital Readmission Machine Learning Pipeline.

Defines deterministic categorical, numerical, excluded, and target features,
providing strict schema validation against input DataFrames.
"""

from typing import Any

# -----------------------------------------------------------------------------
# Target Definition
# -----------------------------------------------------------------------------
TARGET_COLUMN: str = "readmission_target"

# -----------------------------------------------------------------------------
# Excluded Columns (Identifiers, Raw Target Strings, High Missingness / Superseded)
# -----------------------------------------------------------------------------
EXCLUDED_COLUMNS: list[str] = [
    "encounter_id",
    "patient_nbr",
    "readmission_target",
    "readmitted",
    "weight",
    "diag_1",
    "diag_2",
    "diag_3",
    "age",
]

# -----------------------------------------------------------------------------
# Categorical Features for Spark ML Pipeline
# -----------------------------------------------------------------------------
CATEGORICAL_FEATURES: list[str] = [
    # Demographics
    "race",
    "gender",
    "age_category",
    # Admission / Discharge Identifiers
    "admission_type_id",
    "discharge_disposition_id",
    "admission_source_id",
    # Hospital Encounter & Physician Specialty
    "stay_category",
    "payer_code",
    "medical_specialty",
    # Laboratory Results
    "max_glu_serum",
    "a1cresult",
    # Diagnosis Groups (ICD-9 Clinical Mappings)
    "primary_diagnosis_group",
    "secondary_diagnosis_group",
    "additional_diagnosis_group",
    # Utilization Tiers
    "utilization_tier",
    "inpatient_frequency_tier",
    # Diabetic Medications (23 specific agents)
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
    # General Medication Alteration Indicators
    "change",
    "diabetesmed",
]

# -----------------------------------------------------------------------------
# Numerical Features for Spark ML Pipeline
# -----------------------------------------------------------------------------
NUMERICAL_FEATURES: list[str] = [
    # Encounter Duration & Lab / Procedure Counts
    "age_midpoint",
    "time_in_hospital",
    "num_lab_procedures",
    "num_procedures",
    "num_medications",
    "number_diagnoses",
    # Historical Utilization Volumes
    "number_outpatient",
    "number_emergency",
    "number_inpatient",
    "total_prior_visits",
    # Binary Utilization & Clinical Flags
    "has_prior_inpatient",
    "has_prior_emergency",
    "has_prior_outpatient",
    "has_prior_visits",
    "is_senior",
    "is_geriatric",
    "is_long_stay",
    "is_short_stay",
    # Comorbidity Indicators
    "has_diabetes_diagnosis",
    "has_circulatory_diagnosis",
    "has_respiratory_diagnosis",
    "has_digestive_diagnosis",
    "has_genitourinary_diagnosis",
    # Medication Regimen Flags
    "insulin_flag",
    "medication_change_flag",
    "diabetes_med_flag",
]


class FeatureValidationError(Exception):
    """Raised when DataFrame schema fails feature selection validation."""

    pass


def get_target_column() -> str:
    """Return the designated prediction target column name."""
    return TARGET_COLUMN


def get_excluded_columns() -> list[str]:
    """Return the list of explicitly excluded column names."""
    return list(EXCLUDED_COLUMNS)


def get_categorical_features() -> list[str]:
    """Return deterministic list of categorical feature column names."""
    return list(CATEGORICAL_FEATURES)


def get_numerical_features() -> list[str]:
    """Return deterministic list of numerical feature column names."""
    return list(NUMERICAL_FEATURES)


def get_all_feature_columns() -> list[str]:
    """Return the combined list of all feature columns (categorical + numerical)."""
    return get_categorical_features() + get_numerical_features()


def validate_feature_columns(
    df_or_columns: Any | list[str] | set[str],
    require_target: bool = True,
) -> None:
    """Validate that required feature columns and target exist, and no exclusions leak.

    Args:
        df_or_columns: A PySpark DataFrame, list of column names, or set of column names.
        require_target: Whether to strictly assert presence of the target column.

    Raises:
        FeatureValidationError: If any required feature is missing or exclusions conflict.
    """
    if hasattr(df_or_columns, "columns"):
        available_columns = set(df_or_columns.columns)
    elif isinstance(df_or_columns, (list, tuple, set)):
        available_columns = set(df_or_columns)
    else:
        raise TypeError(
            f"Expected DataFrame or collection of column names, got {type(df_or_columns).__name__}"
        )

    # 1. Check for missing categorical features
    missing_categorical = [col for col in CATEGORICAL_FEATURES if col not in available_columns]
    if missing_categorical:
        raise FeatureValidationError(
            f"Missing required categorical feature columns ({len(missing_categorical)}): {missing_categorical}"
        )

    # 2. Check for missing numerical features
    missing_numerical = [col for col in NUMERICAL_FEATURES if col not in available_columns]
    if missing_numerical:
        raise FeatureValidationError(
            f"Missing required numerical feature columns ({len(missing_numerical)}): {missing_numerical}"
        )

    # 3. Check for target column
    if require_target and TARGET_COLUMN not in available_columns:
        raise FeatureValidationError(f"Missing required target column: '{TARGET_COLUMN}'")

    # 4. Ensure no excluded columns leak into feature sets
    all_selected = set(CATEGORICAL_FEATURES) | set(NUMERICAL_FEATURES)
    overlap = all_selected.intersection(set(EXCLUDED_COLUMNS))
    if overlap:
        raise FeatureValidationError(
            f"Feature selection conflict: excluded columns found in feature set: {overlap}"
        )
