"""Tests for Hive schema definition and data ingestion contracts."""

from src.utils.config import get_project_root


def test_hive_schema_file_exists() -> None:
    """Verify that hive/schema.hql exists and is non-empty."""
    schema_path = get_project_root() / "hive" / "schema.hql"
    assert schema_path.is_file()
    assert schema_path.stat().st_size > 0


def test_hive_schema_ddl_structure() -> None:
    """Verify key DDL statements and external table specifications in schema.hql."""
    schema_path = get_project_root() / "hive" / "schema.hql"
    content = schema_path.read_text(encoding="utf-8")

    assert "CREATE DATABASE IF NOT EXISTS readmission;" in content
    assert "USE readmission;" in content
    assert "CREATE EXTERNAL TABLE IF NOT EXISTS readmission.patient_records" in content
    assert "LOCATION 'hdfs:///readmission/raw/'" in content
    assert 'TBLPROPERTIES ("skip.header.line.count"="1")' in content

    # Key columns check
    assert "encounter_id BIGINT" in content
    assert "patient_nbr BIGINT" in content
    assert "time_in_hospital INT" in content
    assert "readmitted STRING" in content
