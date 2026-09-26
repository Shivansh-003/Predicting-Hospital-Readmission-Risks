"""Tests for Hive clinical feature views definition and contracts."""

from src.utils.config import get_project_root


def test_feature_views_file_exists() -> None:
    """Verify that hive/feature_views.hql exists and is non-empty."""
    views_path = get_project_root() / "hive" / "feature_views.hql"
    assert views_path.is_file()
    assert views_path.stat().st_size > 0


def test_init_script_exists() -> None:
    """Verify that scripts/init_feature_views.ps1 exists."""
    script_path = get_project_root() / "scripts" / "init_feature_views.ps1"
    assert script_path.is_file()
    assert script_path.stat().st_size > 0


def test_feature_views_ddl_structure() -> None:
    """Verify key DDL statements and view specifications in feature_views.hql."""
    views_path = get_project_root() / "hive" / "feature_views.hql"
    content = views_path.read_text(encoding="utf-8")

    assert "CREATE DATABASE IF NOT EXISTS readmission;" in content
    assert "USE readmission;" in content

    # 1. age_bin_view
    assert "CREATE VIEW IF NOT EXISTS readmission.age_bin_view" in content
    assert "age_category" in content
    assert "is_senior" in content
    assert "is_geriatric" in content

    # 2. stay_category_view
    assert "CREATE VIEW IF NOT EXISTS readmission.stay_category_view" in content
    assert "stay_category" in content
    assert "is_long_stay" in content
    assert "is_short_stay" in content

    # 3. diagnosis_group_view
    assert "CREATE VIEW IF NOT EXISTS readmission.diagnosis_group_view" in content
    assert "primary_diagnosis_group" in content
    assert "secondary_diagnosis_group" in content
    assert "additional_diagnosis_group" in content
    assert "has_diabetes_diagnosis" in content
    assert "has_circulatory_diagnosis" in content
    assert "has_respiratory_diagnosis" in content
    assert "has_digestive_diagnosis" in content
    assert "has_genitourinary_diagnosis" in content

    # 4. prior_admission_view
    assert "CREATE VIEW IF NOT EXISTS readmission.prior_admission_view" in content
    assert "total_prior_visits" in content
    assert "has_prior_inpatient" in content
    assert "has_prior_emergency" in content
    assert "has_prior_outpatient" in content
    assert "has_prior_visits" in content
    assert "utilization_tier" in content
    assert "inpatient_frequency_tier" in content

    # 5. patient_features_view
    assert "CREATE VIEW IF NOT EXISTS readmission.patient_features_view" in content
    assert "INNER JOIN readmission.age_bin_view" in content
    assert "INNER JOIN readmission.stay_category_view" in content
    assert "INNER JOIN readmission.diagnosis_group_view" in content
    assert "INNER JOIN readmission.prior_admission_view" in content
    assert "readmission_target" in content
