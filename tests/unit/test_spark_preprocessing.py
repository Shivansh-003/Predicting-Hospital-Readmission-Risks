"""PySpark DataFrame unit tests for preprocessing operations."""

from typing import Any

import pytest

try:
    from pyspark.sql import Row, SparkSession

    from src.preprocessing.cleaner import (
        filter_invalid_demographics,
        filter_terminal_discharges,
        replace_missing_tokens,
    )
    from src.preprocessing.encoder import (
        encode_age_midpoint,
        encode_diabetes_med_flag,
        encode_insulin_flag,
        encode_medication_change_flag,
        encode_readmission_target,
    )
    from src.preprocessing.validators import (
        DataIntegrityError,
        SchemaValidationError,
        validate_age_range,
        validate_input_columns,
        validate_target_values,
    )

    HAS_PYSPARK = True
except ImportError:
    HAS_PYSPARK = False


@pytest.fixture(scope="session")
def spark() -> Any:
    """Session-scoped SparkSession fixture for unit testing."""
    if not HAS_PYSPARK:
        pytest.skip("PySpark is not installed in the test environment.")

    spark_session = (
        SparkSession.builder.appName("UnitTestPreprocessing")
        .master("local[1]")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield spark_session
    spark_session.stop()


@pytest.mark.skipif(not HAS_PYSPARK, reason="PySpark is not available")
class TestSparkCleaner:
    """Test PySpark cleaner transformations on small deterministic DataFrames."""

    def test_filter_terminal_discharges(self, spark: Any) -> None:
        """Verify removal of expired (11, 19, 20, 21) and hospice (13, 14) encounters."""
        data = [
            Row(encounter_id=1, discharge_disposition_id=1),  # Home (Keep)
            Row(encounter_id=2, discharge_disposition_id=11),  # Expired (Drop)
            Row(encounter_id=3, discharge_disposition_id=13),  # Hospice (Drop)
            Row(encounter_id=4, discharge_disposition_id=3),  # SNF (Keep)
            Row(encounter_id=5, discharge_disposition_id=19),  # Expired at home (Drop)
        ]
        df = spark.createDataFrame(data)
        result_df = filter_terminal_discharges(df)
        remaining_ids = [r.encounter_id for r in result_df.collect()]

        assert remaining_ids == [1, 4]

    def test_filter_invalid_demographics(self, spark: Any) -> None:
        """Verify removal of records with unknown or missing gender."""
        data = [
            Row(encounter_id=1, gender="Female"),
            Row(encounter_id=2, gender="Male"),
            Row(encounter_id=3, gender="Unknown/Invalid"),
            Row(encounter_id=4, gender=None),
        ]
        df = spark.createDataFrame(data)
        result_df = filter_invalid_demographics(df)
        remaining_ids = [r.encounter_id for r in result_df.collect()]

        assert remaining_ids == [1, 2]

    def test_replace_missing_tokens(self, spark: Any) -> None:
        """Verify replacement of '?' with NULL in string columns."""
        data = [
            Row(encounter_id=1, race="Caucasian", medical_specialty="Cardiology"),
            Row(encounter_id=2, race="?", medical_specialty="?"),
            Row(encounter_id=3, race="AfricanAmerican", medical_specialty="?"),
        ]
        df = spark.createDataFrame(data)
        result_df = replace_missing_tokens(df, missing_token="?")
        rows = {r.encounter_id: (r.race, r.medical_specialty) for r in result_df.collect()}

        assert rows[1] == ("Caucasian", "Cardiology")
        assert rows[2] == (None, None)
        assert rows[3] == ("AfricanAmerican", None)


@pytest.mark.skipif(not HAS_PYSPARK, reason="PySpark is not available")
class TestSparkEncoder:
    """Test PySpark encoder transformations."""

    def test_encode_age_midpoint(self, spark: Any) -> None:
        """Verify age interval bracket conversion to midpoint values."""
        data = [
            Row(encounter_id=1, age="[0-10)"),
            Row(encounter_id=2, age="[50-60)"),
            Row(encounter_id=3, age="[90-100)"),
            Row(encounter_id=4, age="20-30"),
        ]
        df = spark.createDataFrame(data)
        result_df = encode_age_midpoint(df)
        midpoints = {r.encounter_id: r.age_midpoint for r in result_df.collect()}

        assert midpoints[1] == 5
        assert midpoints[2] == 55
        assert midpoints[3] == 95
        assert midpoints[4] == 25

    def test_encode_insulin_flag(self, spark: Any) -> None:
        """Verify insulin status binary flag derivation."""
        data = [
            Row(encounter_id=1, insulin="No"),
            Row(encounter_id=2, insulin="Up"),
            Row(encounter_id=3, insulin="Steady"),
            Row(encounter_id=4, insulin="Down"),
        ]
        df = spark.createDataFrame(data)
        result_df = encode_insulin_flag(df)
        flags = {r.encounter_id: r.insulin_flag for r in result_df.collect()}

        assert flags[1] == 0
        assert flags[2] == 1
        assert flags[3] == 1
        assert flags[4] == 1

    def test_encode_medication_change_flag(self, spark: Any) -> None:
        """Verify medication change binary flag derivation."""
        data = [
            Row(encounter_id=1, change="Ch"),
            Row(encounter_id=2, change="No"),
        ]
        df = spark.createDataFrame(data)
        result_df = encode_medication_change_flag(df)
        flags = {r.encounter_id: r.medication_change_flag for r in result_df.collect()}

        assert flags[1] == 1
        assert flags[2] == 0

    def test_encode_diabetes_med_flag(self, spark: Any) -> None:
        """Verify diabetes medication prescribed binary flag."""
        data = [
            Row(encounter_id=1, diabetesMed="Yes"),
            Row(encounter_id=2, diabetesMed="No"),
        ]
        df = spark.createDataFrame(data)
        result_df = encode_diabetes_med_flag(df)
        flags = {r.encounter_id: r.diabetes_med_flag for r in result_df.collect()}

        assert flags[1] == 1
        assert flags[2] == 0

    def test_encode_readmission_target(self, spark: Any) -> None:
        """Verify 30-day readmission target encoding."""
        data = [
            Row(encounter_id=1, readmitted="<30"),
            Row(encounter_id=2, readmitted=">30"),
            Row(encounter_id=3, readmitted="NO"),
        ]
        df = spark.createDataFrame(data)
        result_df = encode_readmission_target(df)
        targets = {r.encounter_id: r.readmission_target for r in result_df.collect()}

        assert targets[1] == 1
        assert targets[2] == 0
        assert targets[3] == 0


@pytest.mark.skipif(not HAS_PYSPARK, reason="PySpark is not available")
class TestSparkValidators:
    """Test PySpark validation functions and error raising."""

    def test_validate_target_values_success(self, spark: Any) -> None:
        """Verify successful target distribution validation."""
        data = [
            Row(readmission_target=0),
            Row(readmission_target=1),
            Row(readmission_target=0),
        ]
        df = spark.createDataFrame(data)
        dist = validate_target_values(df)

        assert dist == {0: 2, 1: 1}

    def test_validate_target_values_failure_on_invalid_val(self, spark: Any) -> None:
        """Verify DataIntegrityError on non-binary target value."""
        data = [
            Row(readmission_target=0),
            Row(readmission_target=2),  # Invalid
        ]
        df = spark.createDataFrame(data)
        with pytest.raises(DataIntegrityError):
            validate_target_values(df)

    def test_validate_age_range_failure_out_of_bounds(self, spark: Any) -> None:
        """Verify DataIntegrityError on impossible age value."""
        data = [
            Row(age_midpoint=55),
            Row(age_midpoint=150),  # Out of range
        ]
        df = spark.createDataFrame(data)
        with pytest.raises(DataIntegrityError):
            validate_age_range(df, min_age=0, max_age=120)

    def test_validate_input_columns_failure_on_missing(self, spark: Any) -> None:
        """Verify SchemaValidationError on missing required columns."""
        data = [Row(col_a="foo", col_b="bar")]
        df = spark.createDataFrame(data)
        with pytest.raises(SchemaValidationError):
            validate_input_columns(df, expected_columns=["col_a", "col_c"])
