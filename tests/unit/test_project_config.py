"""Tests for project configuration loading and integrity."""

from pathlib import Path

import pytest

from src.utils.config import get_project_root, load_config


def test_get_project_root() -> None:
    """Verify that get_project_root returns a valid directory containing config."""
    root = get_project_root()
    assert root.is_dir()
    assert (root / "config" / "config.yaml").exists()


def test_load_default_config() -> None:
    """Verify that load_config successfully loads the default YAML configuration."""
    config = load_config()

    assert isinstance(config, dict)
    assert "project" in config
    assert "data" in config
    assert "models" in config
    assert "outputs" in config
    assert "logging" in config

    assert config["project"]["name"] == "hospital-readmission-ai"
    assert config["project"]["version"] == "2.0.0"
    assert config["project"]["environment"] == "development"

    assert config["data"]["raw_dir"] == "data/raw"
    assert config["data"]["processed_dir"] == "data/processed"
    assert config["data"]["sample_dir"] == "data/sample"

    assert config["models"]["output_dir"] == "models"
    assert config["outputs"]["output_dir"] == "outputs"
    assert config["logging"]["level"] == "INFO"


def test_load_config_with_explicit_path() -> None:
    """Verify loading config with explicit Path and str paths."""
    config_path = get_project_root() / "config" / "config.yaml"
    config_from_path = load_config(config_path)
    config_from_str = load_config(str(config_path))
    assert config_from_path == config_from_str
    assert config_from_path["project"]["name"] == "hospital-readmission-ai"


def test_load_config_nonexistent_file() -> None:
    """Verify that load_config raises FileNotFoundError for missing paths."""
    with pytest.raises(FileNotFoundError):
        load_config(Path("nonexistent_path/config.yaml"))


def test_load_config_invalid_yaml(tmp_path: Path) -> None:
    """Verify that load_config raises ValueError for non-dict YAML files."""
    invalid_file = tmp_path / "invalid.yaml"
    invalid_file.write_text("just a string, not a dict", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid or empty configuration file"):
        load_config(invalid_file)
