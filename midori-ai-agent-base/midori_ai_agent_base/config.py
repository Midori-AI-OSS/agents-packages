"""Configuration loader for the Midori AI agent base.

This module looks for a `config.toml` file in this package's
ancestor directories and returns agent-related configuration.

Config precedence used by the agent factory:
  1. explicit arguments passed to `get_agent_from_config`
  2. values present in `config.toml` under `[midori_ai_agent_base]`
  3. module defaults defined here

Supports layered configs for per-backend overrides:
  - `[midori_ai_agent_base]` for base settings
  - `[midori_ai_agent_base.langchain]`, `[midori_ai_agent_base.openai]`
    for backend-specific overrides
"""

import tomllib as _toml

from dataclasses import dataclass
from dataclasses import field

from pathlib import Path

from typing import Any
from typing import Dict
from typing import Optional


@dataclass
class ReasoningEffortConfig:
    """Configuration for LRM reasoning effort from TOML.

    Attributes:
        effort: The reasoning effort level ("none", "minimal", "low", "medium", "high").
        generate_summary: How to generate summaries ("auto", "concise", "detailed").
        summary: The summary type ("auto", "concise", "detailed").
    """

    effort: Optional[str] = None
    generate_summary: Optional[str] = None
    summary: Optional[str] = None


@dataclass
class AgentConfig:
    """Configuration for agent backends loaded from TOML.

    Attributes:
        backend: The backend type ("langchain", "openai").
        model: Model name to use.
        api_key: API key for authentication.
        base_url: Base URL for the API endpoint.
        reasoning_effort: Optional reasoning effort configuration.
        extra: Additional key-value pairs from the config file.
    """

    backend: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    reasoning_effort: Optional[ReasoningEffortConfig] = None
    extra: Dict[str, Any] = field(default_factory=dict)


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


def _parse_reasoning_effort(section: Dict[str, Any]) -> Optional[ReasoningEffortConfig]:
    """Parse reasoning_effort subsection from config.

    Args:
        section: The agent config section dict

    Returns:
        ReasoningEffortConfig if any reasoning fields present, else None
    """
    reasoning_data = section.get("reasoning_effort")

    if reasoning_data is None or not isinstance(reasoning_data, dict):
        return None

    return ReasoningEffortConfig(effort=reasoning_data.get("effort"), generate_summary=reasoning_data.get("generate_summary"), summary=reasoning_data.get("summary"))


def _parse_agent_section(section: Dict[str, Any]) -> AgentConfig:
    """Parse an agent config section into an AgentConfig dataclass.

    Args:
        section: Dict from the TOML section

    Returns:
        AgentConfig with values from section
    """
    known_keys = {"backend", "model", "api_key", "base_url", "reasoning_effort"}
    extra = {k: v for k, v in section.items() if k not in known_keys and not isinstance(v, dict)}

    return AgentConfig(backend=section.get("backend"), model=section.get("model"), api_key=section.get("api_key"), base_url=section.get("base_url"), reasoning_effort=_parse_reasoning_effort(section), extra=extra)


def load_agent_config(backend: Optional[str] = None) -> AgentConfig:
    """Load agent-related config from the TOML file.

    Loads base settings from `[midori_ai_agent_base]` section, then merges
    backend-specific overrides from `[midori_ai_agent_base.<backend>]` if
    a backend is specified.

    Args:
        backend: Optional backend name to load specific overrides for.
            If provided, values from `[midori_ai_agent_base.<backend>]`
            will override the base settings.

    Returns:
        AgentConfig with merged values. Fields default to None if missing.
    """
    path = _find_config_file()

    if path is None:
        return AgentConfig()

    try:
        with path.open("rb") as f:
            data = _toml.load(f)
    except Exception:
        return AgentConfig()

    section = data.get("midori_ai_agent_base")

    if section is None or not isinstance(section, dict):
        return AgentConfig()

    base_config = _parse_agent_section(section)

    if backend is None:
        return base_config

    backend_section = section.get(backend)

    if backend_section is None or not isinstance(backend_section, dict):
        return base_config

    backend_config = _parse_agent_section(backend_section)

    return _merge_configs(base_config, backend_config)


def _merge_configs(base: AgentConfig, override: AgentConfig) -> AgentConfig:
    """Merge two AgentConfigs, with override values taking precedence.

    Args:
        base: Base configuration
        override: Override configuration (non-None values win)

    Returns:
        New AgentConfig with merged values
    """
    merged_reasoning = None

    if base.reasoning_effort is not None or override.reasoning_effort is not None:
        base_re = base.reasoning_effort or ReasoningEffortConfig()
        over_re = override.reasoning_effort or ReasoningEffortConfig()
        merged_reasoning = ReasoningEffortConfig(effort=over_re.effort if over_re.effort is not None else base_re.effort, generate_summary=over_re.generate_summary if over_re.generate_summary is not None else base_re.generate_summary, summary=over_re.summary if over_re.summary is not None else base_re.summary)

    merged_extra = {**base.extra, **override.extra}

    return AgentConfig(backend=override.backend if override.backend is not None else base.backend, model=override.model if override.model is not None else base.model, api_key=override.api_key if override.api_key is not None else base.api_key, base_url=override.base_url if override.base_url is not None else base.base_url, reasoning_effort=merged_reasoning, extra=merged_extra)
