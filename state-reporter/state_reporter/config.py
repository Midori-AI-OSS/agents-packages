"""Configuration loader for the Midori AI state reporter.

This module looks for a `config.toml` file in this package's
ancestor directories and returns reporter-related configuration.

Config precedence used by the reporter:
  1. explicit arguments passed to `StateReporter`
  2. values present in `config.toml` under `[state_reporter]`
  3. module defaults defined here
"""

from typing import Any
from typing import Dict
from typing import Optional

import tomli as _toml

from pathlib import Path

MAX_BACKOFF_SECONDS = 300
DEFAULT_HEARTBEAT_INTERVAL = 30
DEFAULT_LOGGING_SERVER_URL = "http://logging:8000"


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


def load_reporter_config() -> Dict[str, Any]:
    """Load reporter-related config from the TOML file.

    Returns a dict with optional keys: "logging_server_url", "heartbeat_interval",
    "max_backoff_seconds". If no file or the keys are missing, those keys are
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
    
    section = data.get("state_reporter", data)
    
    if not isinstance(section, dict):
        return cfg

    if "logging_server_url" in section:
        cfg["logging_server_url"] = section.get("logging_server_url")
    if "heartbeat_interval" in section:
        try:
            val = section.get("heartbeat_interval")
            if val is not None:
                cfg["heartbeat_interval"] = int(val)
        except Exception:
            pass
    if "max_backoff_seconds" in section:
        try:
            val = section.get("max_backoff_seconds")
            if val is not None:
                cfg["max_backoff_seconds"] = int(val)
        except Exception:
            pass

    return cfg
