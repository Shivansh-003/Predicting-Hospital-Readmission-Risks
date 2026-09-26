"""Unit tests for feature selection, transformation contracts, and pipeline definitions."""

from unittest.mock import MagicMock

import pytest

from src.features.feature_selector import (
    FeatureValidationError,
    get_all_feature_columns,
    get_categorical_features,
    get_excluded_columns,
    get_numerical_features,
    get_target_column,
    validate_feature_columns,
)
from src.features.pipeline import (
    load_patient_features_view,
    transform_features,
)


def test_target_column_definition() -> None:
    """Verify that the target column is designated as readmission_target."""
    assert get_target_column() == "readmission_target"


def test_excluded_columns_contain_identifiers_and_raw_fields() -> None:
    """Verify that identifiers and raw superseded columns are explicitly listed as excluded."""
    excluded = get_excluded_columns()
    assert "encounter_id" in excluded
    assert "patient_nbr" in excluded
    assert "readmission_target" in excluded
    assert "readmitted" in excluded
    assert "weight" in excluded
    assert "diag_1" in excluded
    assert "diag_2" in excluded
    assert "diag_3" in excluded
    assert "age" in excluded


def test_no_excluded_columns_in_selected_features() -> None:
    """Ensure zero overlap between excluded columns and selected feature columns."""
    cat_features = set(get_categorical_features())
    num_features = set(get_numerical_features())
    all_features = cat_features | num_features
    excluded_set = set(get_excluded_columns())

    overlap = all_features.intersection(excluded_set)
    assert not overlap, f"Excluded columns leaked into feature sets: {overlap}"


def test_categorical_and_numerical_feature_disjointness() -> None:
    """Ensure categorical and numerical feature lists are mutually exclusive."""
    cat_features = set(get_categorical_features())
    num_features = set(get_numerical_features())

    overlap = cat_features.intersection(num_features)
    assert not overlap, f"Overlapping columns between categorical and numerical sets: {overlap}"


def test_feature_counts() -> None:
    """Verify the expected deterministic counts of features."""
    cat_features = get_categorical_features()
    num_features = get_numerical_features()
    all_features = get_all_feature_columns()

    assert len(cat_features) == 41
    assert len(num_features) == 26
    assert len(all_features) == 67


def test_validation_passes_with_complete_schema() -> None:
    """Verify that validate_feature_columns succeeds when all required columns are present."""
    mock_columns = get_all_feature_columns() + [get_target_column(), "encounter_id", "patient_nbr"]
    validate_feature_columns(mock_columns, require_target=True)


def test_validation_with_dataframe_like_object() -> None:
    """Verify that validate_feature_columns accepts DataFrame-like objects with .columns."""
    mock_df = MagicMock()
    mock_df.columns = get_all_feature_columns() + [get_target_column()]
    validate_feature_columns(mock_df, require_target=True)


def test_validation_fails_on_missing_categorical_column() -> None:
    """Verify that missing categorical column triggers FeatureValidationError."""
    all_cols = get_all_feature_columns() + [get_target_column()]
    all_cols.remove("primary_diagnosis_group")

    with pytest.raises(
        FeatureValidationError, match="Missing required categorical feature columns"
    ):
        validate_feature_columns(all_cols)


def test_validation_fails_on_missing_numerical_column() -> None:
    """Verify that missing numerical column triggers FeatureValidationError."""
    all_cols = get_all_feature_columns() + [get_target_column()]
    all_cols.remove("time_in_hospital")

    with pytest.raises(FeatureValidationError, match="Missing required numerical feature columns"):
        validate_feature_columns(all_cols)


def test_validation_fails_on_missing_target_when_required() -> None:
    """Verify that missing target column triggers FeatureValidationError when require_target=True."""
    all_cols = get_all_feature_columns()

    with pytest.raises(FeatureValidationError, match="Missing required target column"):
        validate_feature_columns(all_cols, require_target=True)


def test_validation_succeeds_without_target_when_require_target_false() -> None:
    """Verify that missing target passes if require_target is False (e.g. at scoring time)."""
    all_cols = get_all_feature_columns()
    validate_feature_columns(all_cols, require_target=False)


def test_validation_type_error_on_invalid_input() -> None:
    """Verify TypeError on unsupported input type."""
    with pytest.raises(TypeError):
        validate_feature_columns(12345)  # type: ignore


def test_load_patient_features_view_helper() -> None:
    """Verify load_patient_features_view invokes spark.table on target view."""
    mock_spark = MagicMock()
    load_patient_features_view(mock_spark, hive_view="readmission.patient_features_view")
    mock_spark.table.assert_called_once_with("readmission.patient_features_view")


def test_transform_features_projection() -> None:
    """Verify transform_features returns projected DataFrame retaining features and target."""
    mock_df = MagicMock()
    mock_model = MagicMock()
    mock_transformed = MagicMock()
    mock_transformed.columns = ["features", "readmission_target", "encounter_id", "extra_col"]
    mock_model.transform.return_value = mock_transformed

    result = transform_features(
        mock_df, mock_model, feature_col="features", target_col="readmission_target"
    )
    mock_transformed.select.assert_called_once_with(["features", "readmission_target"])
    assert result == mock_transformed.select.return_value
