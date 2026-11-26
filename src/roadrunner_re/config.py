"""Locating and reading config files.

Every physical parameter lives in ``config/*.yaml`` (ADR-0002); this
module is the one place that knows where that directory is.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "config"


class ConfigError(ValueError):
    """A config file is missing something the ADRs require."""


def load_yaml(path: str | Path) -> Any:
    """Read one YAML file; a relative path is relative to ``config/``."""
    path = Path(path)
    if not path.is_absolute():
        path = CONFIG_DIR / path
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)
