"""Configuration loading and validation utility."""

from pathlib import Path
from typing import Any

import yaml


def get_project_root() -> Path:
    """Return the root directory of the project."""
    return Path(__file__).resolve().parent.parent.parent


def load_config(config_path: Path | str | None = None) -> dict[str, Any]:
    """Load configuration from a YAML file.

    Args:
        config_path: Optional path to the configuration YAML file.
            Defaults to '<project_root>/config/config.yaml'.

    Returns:
        dict[str, Any]: Parsed configuration dictionary.

    Raises:
        FileNotFoundError: If the specified config file does not exist.
        ValueError: If the config file is empty or invalid.
    """
    if config_path is None:
        target_path = get_project_root() / "config" / "config.yaml"
    else:
        target_path = Path(config_path)

    if not target_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {target_path}")

    with open(target_path, encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    if not isinstance(config_data, dict):
        raise ValueError(f"Invalid or empty configuration file: {target_path}")

    return config_data
