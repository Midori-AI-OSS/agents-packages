"""Tests for the config module."""

import pytest


from pathlib import Path

from midori_ai_agent_base import AgentConfig
from midori_ai_agent_base import ReasoningEffortConfig
from midori_ai_agent_base import load_agent_config

from midori_ai_agent_base.config import _merge_configs
from midori_ai_agent_base.config import _parse_agent_section
from midori_ai_agent_base.config import _parse_reasoning_effort


class TestReasoningEffortConfig:
    """Tests for ReasoningEffortConfig dataclass."""

    def test_default_values(self) -> None:
        config = ReasoningEffortConfig()
        assert config.effort is None
        assert config.generate_summary is None
        assert config.summary is None

    def test_custom_values(self) -> None:
        config = ReasoningEffortConfig(effort="high", generate_summary="detailed", summary="concise")
        assert config.effort == "high"
        assert config.generate_summary == "detailed"
        assert config.summary == "concise"


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_default_values(self) -> None:
        config = AgentConfig()
        assert config.backend is None
        assert config.model is None
        assert config.api_key is None
        assert config.base_url is None
        assert config.reasoning_effort is None
        assert config.extra == {}

    def test_custom_values(self) -> None:
        reasoning = ReasoningEffortConfig(effort="medium")
        config = AgentConfig(backend="langchain", model="gpt-4", api_key="sk-test", base_url="https://api.example.com", reasoning_effort=reasoning, extra={"temperature": 0.7})
        assert config.backend == "langchain"
        assert config.model == "gpt-4"
        assert config.api_key == "sk-test"
        assert config.base_url == "https://api.example.com"
        assert config.reasoning_effort is not None
        assert config.reasoning_effort.effort == "medium"
        assert config.extra == {"temperature": 0.7}


class TestParseReasoningEffort:
    """Tests for _parse_reasoning_effort helper."""

    def test_no_reasoning_effort(self) -> None:
        section = {"backend": "langchain"}
        result = _parse_reasoning_effort(section)
        assert result is None

    def test_empty_reasoning_effort(self) -> None:
        section = {"reasoning_effort": {}}
        result = _parse_reasoning_effort(section)
        assert result is not None
        assert result.effort is None

    def test_full_reasoning_effort(self) -> None:
        section = {"reasoning_effort": {"effort": "high", "generate_summary": "detailed", "summary": "auto"}}
        result = _parse_reasoning_effort(section)
        assert result is not None
        assert result.effort == "high"
        assert result.generate_summary == "detailed"
        assert result.summary == "auto"

    def test_partial_reasoning_effort(self) -> None:
        section = {"reasoning_effort": {"effort": "low"}}
        result = _parse_reasoning_effort(section)
        assert result is not None
        assert result.effort == "low"
        assert result.generate_summary is None
        assert result.summary is None

    def test_invalid_reasoning_effort_type(self) -> None:
        section = {"reasoning_effort": "invalid"}
        result = _parse_reasoning_effort(section)
        assert result is None


class TestParseAgentSection:
    """Tests for _parse_agent_section helper."""

    def test_empty_section(self) -> None:
        section: dict = {}
        config = _parse_agent_section(section)
        assert config.backend is None
        assert config.model is None

    def test_full_section(self) -> None:
        section = {"backend": "openai", "model": "gpt-4", "api_key": "sk-test", "base_url": "https://api.openai.com/v1", "reasoning_effort": {"effort": "medium"}}
        config = _parse_agent_section(section)
        assert config.backend == "openai"
        assert config.model == "gpt-4"
        assert config.api_key == "sk-test"
        assert config.base_url == "https://api.openai.com/v1"
        assert config.reasoning_effort is not None
        assert config.reasoning_effort.effort == "medium"

    def test_extra_fields(self) -> None:
        section = {"backend": "langchain", "temperature": 0.7, "max_tokens": 1000}
        config = _parse_agent_section(section)
        assert config.backend == "langchain"
        assert config.extra == {"temperature": 0.7, "max_tokens": 1000}

    def test_nested_dicts_not_in_extra(self) -> None:
        section = {"backend": "langchain", "nested": {"key": "value"}}
        config = _parse_agent_section(section)
        assert "nested" not in config.extra


class TestMergeConfigs:
    """Tests for _merge_configs helper."""

    def test_merge_empty_configs(self) -> None:
        base = AgentConfig()
        override = AgentConfig()
        merged = _merge_configs(base, override)
        assert merged.backend is None
        assert merged.model is None

    def test_override_takes_precedence(self) -> None:
        base = AgentConfig(backend="langchain", model="gpt-3")
        override = AgentConfig(model="gpt-4")
        merged = _merge_configs(base, override)
        assert merged.backend == "langchain"
        assert merged.model == "gpt-4"

    def test_merge_extras(self) -> None:
        base = AgentConfig(extra={"a": 1, "b": 2})
        override = AgentConfig(extra={"b": 3, "c": 4})
        merged = _merge_configs(base, override)
        assert merged.extra == {"a": 1, "b": 3, "c": 4}

    def test_merge_reasoning_effort(self) -> None:
        base_re = ReasoningEffortConfig(effort="low", generate_summary="auto")
        base = AgentConfig(reasoning_effort=base_re)
        over_re = ReasoningEffortConfig(effort="high")
        override = AgentConfig(reasoning_effort=over_re)
        merged = _merge_configs(base, override)
        assert merged.reasoning_effort is not None
        assert merged.reasoning_effort.effort == "high"
        assert merged.reasoning_effort.generate_summary == "auto"

    def test_merge_none_reasoning_effort_to_some(self) -> None:
        base = AgentConfig()
        over_re = ReasoningEffortConfig(effort="medium")
        override = AgentConfig(reasoning_effort=over_re)
        merged = _merge_configs(base, override)
        assert merged.reasoning_effort is not None
        assert merged.reasoning_effort.effort == "medium"


class TestLoadAgentConfig:
    """Tests for load_agent_config function."""

    def test_no_config_file_returns_empty(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        from midori_ai_agent_base import config as config_module
        original_find = config_module._find_config_file

        def mock_find(name: str = "config.toml") -> None:
            return None

        monkeypatch.setattr(config_module, "_find_config_file", mock_find)
        config = load_agent_config()
        assert config.backend is None
        monkeypatch.setattr(config_module, "_find_config_file", original_find)


class TestLoadAgentConfigWithFile:
    """Tests for load_agent_config with actual TOML files."""

    def test_load_basic_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        config_content = """
[midori_ai_agent_base]
backend = "langchain"
model = "gpt-4"
api_key = "sk-test-key"
base_url = "https://api.example.com/v1"
"""
        config_file = tmp_path / "config.toml"
        config_file.write_text(config_content)

        from midori_ai_agent_base import config as config_module

        def mock_find(name: str = "config.toml") -> Path:
            return config_file

        monkeypatch.setattr(config_module, "_find_config_file", mock_find)
        config = load_agent_config()
        assert config.backend == "langchain"
        assert config.model == "gpt-4"
        assert config.api_key == "sk-test-key"
        assert config.base_url == "https://api.example.com/v1"

    def test_load_config_with_reasoning_effort(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        config_content = """
[midori_ai_agent_base]
backend = "openai"
model = "gpt-4"
api_key = "sk-test"

[midori_ai_agent_base.reasoning_effort]
effort = "high"
generate_summary = "detailed"
summary = "concise"
"""
        config_file = tmp_path / "config.toml"
        config_file.write_text(config_content)

        from midori_ai_agent_base import config as config_module

        def mock_find(name: str = "config.toml") -> Path:
            return config_file

        monkeypatch.setattr(config_module, "_find_config_file", mock_find)
        config = load_agent_config()
        assert config.reasoning_effort is not None
        assert config.reasoning_effort.effort == "high"
        assert config.reasoning_effort.generate_summary == "detailed"
        assert config.reasoning_effort.summary == "concise"

    def test_load_config_with_backend_override(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        config_content = """
[midori_ai_agent_base]
backend = "langchain"
model = "base-model"
api_key = "base-key"

[midori_ai_agent_base.openai]
model = "openai-model"
"""
        config_file = tmp_path / "config.toml"
        config_file.write_text(config_content)

        from midori_ai_agent_base import config as config_module

        def mock_find(name: str = "config.toml") -> Path:
            return config_file

        monkeypatch.setattr(config_module, "_find_config_file", mock_find)
        config = load_agent_config(backend="openai")
        assert config.backend == "langchain"
        assert config.model == "openai-model"
        assert config.api_key == "base-key"

    def test_load_config_no_section(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        config_content = """
[other_section]
key = "value"
"""
        config_file = tmp_path / "config.toml"
        config_file.write_text(config_content)

        from midori_ai_agent_base import config as config_module

        def mock_find(name: str = "config.toml") -> Path:
            return config_file

        monkeypatch.setattr(config_module, "_find_config_file", mock_find)
        config = load_agent_config()
        assert config.backend is None

    def test_load_config_with_extra_fields(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        config_content = """
[midori_ai_agent_base]
backend = "langchain"
model = "gpt-4"
api_key = "sk-test"
temperature = 0.7
max_tokens = 1000
"""
        config_file = tmp_path / "config.toml"
        config_file.write_text(config_content)

        from midori_ai_agent_base import config as config_module

        def mock_find(name: str = "config.toml") -> Path:
            return config_file

        monkeypatch.setattr(config_module, "_find_config_file", mock_find)
        config = load_agent_config()
        assert config.extra.get("temperature") == 0.7
        assert config.extra.get("max_tokens") == 1000


@pytest.mark.asyncio
class TestGetAgentFromConfig:
    """Tests for get_agent_from_config function."""

    async def test_missing_backend_raises(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        config_content = """
[midori_ai_agent_base]
model = "gpt-4"
api_key = "sk-test"
"""
        config_file = tmp_path / "config.toml"
        config_file.write_text(config_content)

        from midori_ai_agent_base import get_agent_from_config
        from midori_ai_agent_base import config as config_module

        def mock_find(name: str = "config.toml") -> Path:
            return config_file

        monkeypatch.setattr(config_module, "_find_config_file", mock_find)

        with pytest.raises(ValueError, match="backend is required"):
            await get_agent_from_config()

    async def test_missing_model_raises(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        config_content = """
[midori_ai_agent_base]
backend = "langchain"
api_key = "sk-test"
"""
        config_file = tmp_path / "config.toml"
        config_file.write_text(config_content)

        from midori_ai_agent_base import get_agent_from_config
        from midori_ai_agent_base import config as config_module

        def mock_find(name: str = "config.toml") -> Path:
            return config_file

        monkeypatch.setattr(config_module, "_find_config_file", mock_find)

        with pytest.raises(ValueError, match="model is required"):
            await get_agent_from_config()

    async def test_missing_api_key_raises(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        config_content = """
[midori_ai_agent_base]
backend = "langchain"
model = "gpt-4"
"""
        config_file = tmp_path / "config.toml"
        config_file.write_text(config_content)

        from midori_ai_agent_base import get_agent_from_config
        from midori_ai_agent_base import config as config_module

        def mock_find(name: str = "config.toml") -> Path:
            return config_file

        monkeypatch.setattr(config_module, "_find_config_file", mock_find)

        with pytest.raises(ValueError, match="api_key is required"):
            await get_agent_from_config()

    async def test_override_config_values(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        config_content = """
[midori_ai_agent_base]
backend = "langchain"
model = "gpt-3"
api_key = "config-key"
"""
        config_file = tmp_path / "config.toml"
        config_file.write_text(config_content)

        from midori_ai_agent_base import get_agent_from_config
        from midori_ai_agent_base import config as config_module

        def mock_find(name: str = "config.toml") -> Path:
            return config_file

        monkeypatch.setattr(config_module, "_find_config_file", mock_find)
        agent = await get_agent_from_config(model="gpt-4", api_key="override-key")
        assert agent is not None

    async def test_specific_config_path(self, tmp_path: Path) -> None:
        config_content = """
[midori_ai_agent_base]
backend = "langchain"
model = "gpt-4"
api_key = "sk-test"
base_url = "https://api.example.com"
"""
        config_file = tmp_path / "custom-config.toml"
        config_file.write_text(config_content)

        from midori_ai_agent_base import get_agent_from_config
        agent = await get_agent_from_config(config_path=config_file)
        assert agent is not None
