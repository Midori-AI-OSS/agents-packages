"""Configuration loader for the Midori AI logger.

This module looks for a `config.toml` file in this package's
ancestor directories and returns logger-related configuration.

Config precedence used by the logger:
  1. explicit arguments passed to `midori_ai_logger`
  2. values present in `config.toml` under `[midori_ai_logger]`
  3. module defaults defined here
"""

from typing import Any
from typing import Dict
from typing import Optional

import tomli as _toml

from pathlib import Path


DEFAULT_LOGGER_SERVER_URL = ""
DEFAULT_REQUEST_TIMEOUT = 5
DEFAULT_LOG_LEVEL = "normal, debug, warn, error"


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


def load_logger_config() -> Dict[str, Any]:
    """Load logger-related config from the TOML file.

    Returns a dict with optional keys: "logger_server_url", "request_timeout",
    "log_level", "enabled". If no file or the keys are missing, those keys are
    omitted.
    """
    cfg: Dict[str, Any] = {}
    path = _find_config_file()
    if path is None:
        return cfg

    try:
        with path.open("rb") as f:
            data = _toml.load(f)
    except Exception:
        return cfg

    section = data.get("midori_ai_logger")

    if section is None or not isinstance(section, dict):
        return cfg

    if "logger_server_url" in section:
        cfg["logger_server_url"] = section.get("logger_server_url")
    if "request_timeout" in section:
        try:
            val = section.get("request_timeout")
            if val is not None:
                cfg["request_timeout"] = int(val)
        except Exception:
            pass
    if "log_level" in section:
        cfg["log_level"] = section.get("log_level")
    if "enabled" in section:
        cfg["enabled"] = bool(section.get("enabled"))

    return cfg
