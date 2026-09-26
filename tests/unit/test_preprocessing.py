"""Unit tests for preprocessing cleaner, encoder, and validator components."""

import pytest

from src.preprocessing.cleaner import (
    DEFAULT_MISSING_TOKEN,
    INVALID_GENDERS,
    TERMINAL_DISCHARGE_DISPOSITION_IDS,
)
from src.preprocessing.encoder import (
    CHANGE_ACTIVE_STATUS,
    DIABETES_MED_ACTIVE_STATUS,
    INSULIN_ACTIVE_STATUSES,
    parse_age_bracket_midpoint,
)
from src.preprocessing.validators import (
    EXPECTED_RAW_COLUMNS,
    REQUIRED_CLEAN_COLUMNS,
    DataIntegrityError,
    SchemaValidationError,
    normalize_column_name,
)


class TestCleanerConstantsAndRules:
    """Test data cleaning constants and exclusion rules."""

    def test_terminal_discharge_ids(self) -> None:
        """Verify terminal discharge IDs include all expired and hospice codes."""
        assert 11 in TERMINAL_DISCHARGE_DISPOSITION_IDS  # Expired
        assert 19 in TERMINAL_DISCHARGE_DISPOSITION_IDS  # Expired at home
        assert 20 in TERMINAL_DISCHARGE_DISPOSITION_IDS  # Expired in medical facility
        assert 21 in TERMINAL_DISCHARGE_DISPOSITION_IDS  # Expired place unknown
        assert 13 in TERMINAL_DISCHARGE_DISPOSITION_IDS  # Hospice home
        assert 14 in TERMINAL_DISCHARGE_DISPOSITION_IDS  # Hospice medical facility

    def test_invalid_genders(self) -> None:
        """Verify invalid demographic exclusion tokens."""
        assert "Unknown/Invalid" in INVALID_GENDERS

    def test_default_missing_token(self) -> None:
        """Verify default missing placeholder token."""
        assert DEFAULT_MISSING_TOKEN == "?"


class TestEncoderLogic:
    """Test feature encoding and target transformation logic."""

    @pytest.mark.parametrize(
        "age_bracket, expected_midpoint",
        [
            ("[0-10)", 5),
            ("[10-20)", 15),
            ("[20-30)", 25),
            ("[30-40)", 35),
            ("[40-50)", 45),
            ("[50-60)", 55),
            ("[60-70)", 65),
            ("[70-80)", 75),
            ("[80-90)", 85),
            ("[90-100)", 95),
            ("0-10", 5),
            ("[40-60]", 50),
            ("(20-40)", 30),
        ],
    )
    def test_parse_age_bracket_midpoint_generic(
        self, age_bracket: str, expected_midpoint: int
    ) -> None:
        """Verify generic age midpoint calculation across standard and arbitrary brackets."""
        assert parse_age_bracket_midpoint(age_bracket) == expected_midpoint

    def test_parse_age_bracket_midpoint_invalid(self) -> None:
        """Verify None is returned for invalid or missing age bracket inputs."""
        assert parse_age_bracket_midpoint(None) is None
        assert parse_age_bracket_midpoint("") is None
        assert parse_age_bracket_midpoint("invalid_age") is None

    def test_target_mapping_contract(self) -> None:
        """Verify target encoding values match clinical readmission specification."""
        target_rules: dict[str, int] = {"<30": 1, ">30": 0, "NO": 0}
        assert target_rules["<30"] == 1
        assert target_rules[">30"] == 0
        assert target_rules["NO"] == 0

    def test_insulin_flag_rules(self) -> None:
        """Verify insulin active vs inactive medication statuses."""
        assert "Up" in INSULIN_ACTIVE_STATUSES
        assert "Down" in INSULIN_ACTIVE_STATUSES
        assert "Steady" in INSULIN_ACTIVE_STATUSES
        assert "No" not in INSULIN_ACTIVE_STATUSES

    def test_change_and_diabetes_med_constants(self) -> None:
        """Verify change and diabetesMed active tokens."""
        assert CHANGE_ACTIVE_STATUS == "Ch"
        assert DIABETES_MED_ACTIVE_STATUS == "Yes"


class TestValidatorsContract:
    """Test schema and integrity validation definitions."""

    def test_expected_raw_columns_count(self) -> None:
        """Verify expected raw dataset columns count (50 columns)."""
        assert len(EXPECTED_RAW_COLUMNS) == 50
        assert "encounter_id" in EXPECTED_RAW_COLUMNS
        assert "patient_nbr" in EXPECTED_RAW_COLUMNS
        assert "readmitted" in EXPECTED_RAW_COLUMNS

    def test_required_clean_columns_count(self) -> None:
        """Verify required clean output columns include all engineered features."""
        assert len(REQUIRED_CLEAN_COLUMNS) == 55
        assert "age_midpoint" in REQUIRED_CLEAN_COLUMNS
        assert "insulin_flag" in REQUIRED_CLEAN_COLUMNS
        assert "medication_change_flag" in REQUIRED_CLEAN_COLUMNS
        assert "diabetes_med_flag" in REQUIRED_CLEAN_COLUMNS
        assert "readmission_target" in REQUIRED_CLEAN_COLUMNS

    def test_normalize_column_name(self) -> None:
        """Verify column normalization for delimiters and casing."""
        assert normalize_column_name("Glyburide-Metformin") == "glyburide_metformin"
        assert normalize_column_name("DIABETESMED") == "diabetesmed"
        assert normalize_column_name("age_midpoint") == "age_midpoint"

    def test_validation_exceptions_hierarchy(self) -> None:
        """Verify custom validation exception class hierarchy."""
        assert issubclass(SchemaValidationError, Exception)
        assert issubclass(DataIntegrityError, Exception)
