"""Spark container test runner for preprocessing unit tests."""

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


def run_tests() -> None:
    print("============================================================")
    print("Running PySpark Preprocessing Unit Tests inside Spark Cluster")
    print("============================================================")

    spark = (
        SparkSession.builder.appName("PreprocessingUnitTests")
        .master("spark://spark-master:7077")
        .config("spark.driver.host", "spark-master")
        .config("spark.driver.bindAddress", "0.0.0.0")
        .getOrCreate()
    )

    passed = 0
    total = 0

    def assert_test(condition: bool, test_name: str) -> None:
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f" [PASS] {test_name}")
        else:
            print(f" [FAIL] {test_name}")
            raise AssertionError(f"Test failed: {test_name}")

    # 1. Test Terminal Discharges Filtering
    data = [
        Row(encounter_id=1, discharge_disposition_id=1),  # Keep
        Row(encounter_id=2, discharge_disposition_id=11),  # Drop
        Row(encounter_id=3, discharge_disposition_id=13),  # Drop
        Row(encounter_id=4, discharge_disposition_id=3),  # Keep
        Row(encounter_id=5, discharge_disposition_id=19),  # Drop
    ]
    df = spark.createDataFrame(data)
    res = [r.encounter_id for r in filter_terminal_discharges(df).collect()]
    assert_test(res == [1, 4], "filter_terminal_discharges removes expired and hospice cases")

    # 2. Test Invalid Demographics Filtering
    data = [
        Row(encounter_id=1, gender="Female"),
        Row(encounter_id=2, gender="Male"),
        Row(encounter_id=3, gender="Unknown/Invalid"),
        Row(encounter_id=4, gender=None),
    ]
    df = spark.createDataFrame(data)
    res = [r.encounter_id for r in filter_invalid_demographics(df).collect()]
    assert_test(res == [1, 2], "filter_invalid_demographics removes unknown and null gender")

    # 3. Test Replace Missing Tokens
    data = [
        Row(encounter_id=1, race="Caucasian", medical_specialty="Cardiology"),
        Row(encounter_id=2, race="?", medical_specialty="?"),
        Row(encounter_id=3, race="AfricanAmerican", medical_specialty="?"),
    ]
    df = spark.createDataFrame(data)
    res_clean = replace_missing_tokens(df, missing_token="?")
    rows = {r.encounter_id: (r.race, r.medical_specialty) for r in res_clean.collect()}
    assert_test(
        rows[1] == ("Caucasian", "Cardiology")
        and rows[2] == (None, None)
        and rows[3] == ("AfricanAmerican", None),
        "replace_missing_tokens converts '?' to SQL NULL",
    )

    # 4. Test Age Midpoint Conversion
    data = [
        Row(encounter_id=1, age="[0-10)"),
        Row(encounter_id=2, age="[50-60)"),
        Row(encounter_id=3, age="[90-100)"),
        Row(encounter_id=4, age="20-30"),
    ]
    df = spark.createDataFrame(data)
    res_age = {r.encounter_id: r.age_midpoint for r in encode_age_midpoint(df).collect()}
    assert_test(
        res_age[1] == 5 and res_age[2] == 55 and res_age[3] == 95 and res_age[4] == 25,
        "encode_age_midpoint computes generic midpoints accurately",
    )

    # 5. Test Insulin Flag
    data = [
        Row(encounter_id=1, insulin="No"),
        Row(encounter_id=2, insulin="Up"),
        Row(encounter_id=3, insulin="Steady"),
        Row(encounter_id=4, insulin="Down"),
    ]
    df = spark.createDataFrame(data)
    res_ins = {r.encounter_id: r.insulin_flag for r in encode_insulin_flag(df).collect()}
    assert_test(
        res_ins[1] == 0 and res_ins[2] == 1 and res_ins[3] == 1 and res_ins[4] == 1,
        "encode_insulin_flag derives binary flag for active insulin regimens",
    )

    # 6. Test Medication Change Flag
    data = [
        Row(encounter_id=1, change="Ch"),
        Row(encounter_id=2, change="No"),
    ]
    df = spark.createDataFrame(data)
    res_ch = {
        r.encounter_id: r.medication_change_flag
        for r in encode_medication_change_flag(df).collect()
    }
    assert_test(
        res_ch[1] == 1 and res_ch[2] == 0,
        "encode_medication_change_flag derives 1 for Ch and 0 for No",
    )

    # 7. Test Diabetes Medication Flag
    data = [
        Row(encounter_id=1, diabetesMed="Yes"),
        Row(encounter_id=2, diabetesMed="No"),
    ]
    df = spark.createDataFrame(data)
    res_dm = {r.encounter_id: r.diabetes_med_flag for r in encode_diabetes_med_flag(df).collect()}
    assert_test(
        res_dm[1] == 1 and res_dm[2] == 0, "encode_diabetes_med_flag derives 1 for Yes and 0 for No"
    )

    # 8. Test Target Encoding
    data = [
        Row(encounter_id=1, readmitted="<30"),
        Row(encounter_id=2, readmitted=">30"),
        Row(encounter_id=3, readmitted="NO"),
    ]
    df = spark.createDataFrame(data)
    res_tgt = {
        r.encounter_id: r.readmission_target for r in encode_readmission_target(df).collect()
    }
    assert_test(
        res_tgt[1] == 1 and res_tgt[2] == 0 and res_tgt[3] == 0,
        "encode_readmission_target maps <30 to 1, and >30/NO to 0",
    )

    # 9. Test Target Validation
    data = [Row(readmission_target=0), Row(readmission_target=1), Row(readmission_target=0)]
    df = spark.createDataFrame(data)
    dist = validate_target_values(df)
    assert_test(
        dist == {0: 2, 1: 1}, "validate_target_values returns valid distribution dictionary"
    )

    # 10. Test Validation Failure on Invalid Target
    data_inv = [Row(readmission_target=0), Row(readmission_target=2)]
    df_inv = spark.createDataFrame(data_inv)
    try:
        validate_target_values(df_inv)
        assert_test(False, "validate_target_values must fail on invalid target value 2")
    except DataIntegrityError:
        assert_test(True, "validate_target_values correctly raises DataIntegrityError on value 2")

    # 11. Test Validation Failure on Age Out of Range
    data_age_inv = [Row(age_midpoint=55), Row(age_midpoint=150)]
    df_age_inv = spark.createDataFrame(data_age_inv)
    try:
        validate_age_range(df_age_inv, min_age=0, max_age=120)
        assert_test(False, "validate_age_range must fail on out of bounds age 150")
    except DataIntegrityError:
        assert_test(True, "validate_age_range correctly raises DataIntegrityError on age 150")

    # 12. Test Validation Failure on Missing Column
    data_missing = [Row(col_a="foo", col_b="bar")]
    df_missing = spark.createDataFrame(data_missing)
    try:
        validate_input_columns(df_missing, expected_columns=["col_a", "col_missing"])
        assert_test(False, "validate_input_columns must fail on missing column")
    except SchemaValidationError:
        assert_test(
            True, "validate_input_columns correctly raises SchemaValidationError on missing column"
        )

    print("\n============================================================")
    print(f"✔ ALL {passed}/{total} PYSPARK UNIT TESTS PASSED SUCCESSFULLY!")
    print("============================================================")
    spark.stop()


if __name__ == "__main__":
    run_tests()
