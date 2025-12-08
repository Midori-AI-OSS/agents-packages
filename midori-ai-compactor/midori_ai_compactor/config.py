"""Configuration loader for the Midori AI compactor.

This module looks for a `config.toml` file in this package's
ancestor directories and returns compactor-related configuration.
"""

import tomllib as _toml

from dataclasses import dataclass

from pathlib import Path

from typing import Optional


@dataclass
class CompactorConfig:
    """Configuration for the compactor loaded from TOML.

    Attributes:
        custom_prompt: Optional custom prompt template for consolidation.
            Use {outputs} placeholder for the formatted outputs.
    """

    custom_prompt: Optional[str] = None


def _find_config_file(name: str = "config.toml") -> Optional[Path]:
    """Search upward from this file for a TOML config file and return its Path.

    Returns None if no config file is found.
    """
    here = Path(__file__).resolve()

    for parent in (here, *here.parents):
        candidate = parent / name

        if candidate.exists():
            return candidate

    return None


def load_compactor_config() -> CompactorConfig:
    """Load compactor-related config from the TOML file.

    Loads settings from `[midori_ai_compactor]` section.

    Returns:
        CompactorConfig with loaded values. Fields default to None if missing.
    """
    path = _find_config_file()

    if path is None:
        return CompactorConfig()

    try:
        with path.open("rb") as f:
            data = _toml.load(f)
    except Exception:
        return CompactorConfig()

    section = data.get("midori_ai_compactor")

    if section is None or not isinstance(section, dict):
        return CompactorConfig()

    return CompactorConfig(custom_prompt=section.get("custom_prompt"))
