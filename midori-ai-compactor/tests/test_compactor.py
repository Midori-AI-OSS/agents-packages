"""Tests for the midori-ai-compactor package."""

import pytest

from unittest.mock import patch
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

from midori_ai_compactor import ThinkingCompactor
from midori_ai_compactor import CompactorConfig
from midori_ai_compactor import load_compactor_config
from midori_ai_compactor import DEFAULT_CONSOLIDATION_PROMPT
from midori_ai_compactor import build_consolidation_prompt
from midori_ai_compactor import format_outputs_for_prompt


class TestCompactorConfig:
    """Tests for CompactorConfig dataclass."""

    def test_default_values(self) -> None:
        config = CompactorConfig()
        assert config.custom_prompt is None

    def test_custom_prompt(self) -> None:
        config = CompactorConfig(custom_prompt="Custom: {outputs}")
        assert config.custom_prompt == "Custom: {outputs}"


class TestLoadCompactorConfig:
    """Tests for load_compactor_config function."""

    def test_returns_default_when_no_file(self) -> None:
        with patch("midori_ai_compactor.config._find_config_file", return_value=None):
            config = load_compactor_config()
            assert config.custom_prompt is None

    def test_returns_default_when_no_section(self) -> None:
        mock_path = MagicMock()
        mock_path.open = MagicMock()

        with patch("midori_ai_compactor.config._find_config_file", return_value=mock_path):
            with patch("midori_ai_compactor.config._toml.load", return_value={}):
                config = load_compactor_config()
                assert config.custom_prompt is None


class TestPromptFormatting:
    """Tests for prompt formatting functions."""

    def test_format_outputs_single(self) -> None:
        outputs = ["First analysis"]
        result = format_outputs_for_prompt(outputs)
        assert "--- Output 1 ---" in result
        assert "First analysis" in result

    def test_format_outputs_multiple(self) -> None:
        outputs = ["Analysis 1", "Analysis 2", "Analysis 3"]
        result = format_outputs_for_prompt(outputs)
        assert "--- Output 1 ---" in result
        assert "--- Output 2 ---" in result
        assert "--- Output 3 ---" in result
        assert "Analysis 1" in result
        assert "Analysis 2" in result
        assert "Analysis 3" in result

    def test_format_outputs_preserves_content(self) -> None:
        outputs = ["## Markdown Header\n- List item 1\n- List item 2"]
        result = format_outputs_for_prompt(outputs)
        assert "## Markdown Header" in result
        assert "- List item 1" in result
        assert "- List item 2" in result

    def test_format_outputs_multilingual(self) -> None:
        outputs = ["English analysis", "분석 내용", "Análisis en español"]
        result = format_outputs_for_prompt(outputs)
        assert "English analysis" in result
        assert "분석 내용" in result
        assert "Análisis en español" in result

    def test_build_consolidation_prompt_default(self) -> None:
        outputs = ["Output 1", "Output 2"]
        result = build_consolidation_prompt(outputs)
        assert "--- Output 1 ---" in result
        assert "--- Output 2 ---" in result
        assert "REASONING OUTPUTS TO CONSOLIDATE:" in result

    def test_build_consolidation_prompt_custom(self) -> None:
        outputs = ["Output 1", "Output 2"]
        custom = "Merge these:\n{outputs}\nDone."
        result = build_consolidation_prompt(outputs, custom)
        assert "Merge these:" in result
        assert "--- Output 1 ---" in result
        assert "Done." in result
        assert "REASONING OUTPUTS TO CONSOLIDATE:" not in result


class TestDefaultPrompt:
    """Tests for the default consolidation prompt."""

    def test_default_prompt_has_placeholder(self) -> None:
        assert "{outputs}" in DEFAULT_CONSOLIDATION_PROMPT

    def test_default_prompt_has_instructions(self) -> None:
        assert "INSTRUCTIONS:" in DEFAULT_CONSOLIDATION_PROMPT
        assert "CONSOLIDATED OUTPUT:" in DEFAULT_CONSOLIDATION_PROMPT


class TestThinkingCompactorInit:
    """Tests for ThinkingCompactor initialization."""

    def test_init_with_agent(self) -> None:
        mock_agent = MagicMock()

        with patch("midori_ai_compactor.compactor.MidoriAiLogger"):
            compactor = ThinkingCompactor(agent=mock_agent)
            assert compactor._agent == mock_agent
            assert compactor._config.custom_prompt is None

    def test_init_with_config(self) -> None:
        mock_agent = MagicMock()
        config = CompactorConfig(custom_prompt="Custom: {outputs}")

        with patch("midori_ai_compactor.compactor.MidoriAiLogger"):
            compactor = ThinkingCompactor(agent=mock_agent, config=config)
            assert compactor._config.custom_prompt == "Custom: {outputs}"


@pytest.mark.asyncio
class TestThinkingCompactorCompact:
    """Async tests for ThinkingCompactor.compact method."""

    async def test_compact_empty_list_returns_empty_string(self) -> None:
        mock_agent = MagicMock()

        with patch("midori_ai_compactor.compactor.MidoriAiLogger") as mock_logger_class:
            mock_logger = MagicMock()
            mock_logger.print = AsyncMock()
            mock_logger_class.return_value = mock_logger

            compactor = ThinkingCompactor(agent=mock_agent)
            result = await compactor.compact([])

            assert result == ""
            mock_agent.invoke.assert_not_called()

    async def test_compact_single_output_returns_as_is(self) -> None:
        mock_agent = MagicMock()

        with patch("midori_ai_compactor.compactor.MidoriAiLogger") as mock_logger_class:
            mock_logger = MagicMock()
            mock_logger.print = AsyncMock()
            mock_logger_class.return_value = mock_logger

            compactor = ThinkingCompactor(agent=mock_agent)
            result = await compactor.compact(["Single output"])

            assert result == "Single output"
            mock_agent.invoke.assert_not_called()

    async def test_compact_two_outputs(self) -> None:
        mock_agent = MagicMock()
        mock_response = MagicMock()
        mock_response.response = "Consolidated result"
        mock_agent.invoke = AsyncMock(return_value=mock_response)

        with patch("midori_ai_compactor.compactor.MidoriAiLogger") as mock_logger_class:
            mock_logger = MagicMock()
            mock_logger.print = AsyncMock()
            mock_logger_class.return_value = mock_logger

            compactor = ThinkingCompactor(agent=mock_agent)
            result = await compactor.compact(["Output 1", "Output 2"])

            assert result == "Consolidated result"
            mock_agent.invoke.assert_called_once()

    async def test_compact_four_outputs(self) -> None:
        mock_agent = MagicMock()
        mock_response = MagicMock()
        mock_response.response = "Four outputs consolidated"
        mock_agent.invoke = AsyncMock(return_value=mock_response)

        with patch("midori_ai_compactor.compactor.MidoriAiLogger") as mock_logger_class:
            mock_logger = MagicMock()
            mock_logger.print = AsyncMock()
            mock_logger_class.return_value = mock_logger

            compactor = ThinkingCompactor(agent=mock_agent)
            outputs = ["Output 1", "Output 2", "Output 3", "Output 4"]
            result = await compactor.compact(outputs)

            assert result == "Four outputs consolidated"
            mock_agent.invoke.assert_called_once()
            call_args = mock_agent.invoke.call_args
            payload = call_args[0][0]
            assert "--- Output 1 ---" in payload.user_message
            assert "--- Output 4 ---" in payload.user_message

    async def test_compact_many_outputs(self) -> None:
        mock_agent = MagicMock()
        mock_response = MagicMock()
        mock_response.response = "Many outputs consolidated"
        mock_agent.invoke = AsyncMock(return_value=mock_response)

        with patch("midori_ai_compactor.compactor.MidoriAiLogger") as mock_logger_class:
            mock_logger = MagicMock()
            mock_logger.print = AsyncMock()
            mock_logger_class.return_value = mock_logger

            compactor = ThinkingCompactor(agent=mock_agent)
            outputs = [f"Output {i}" for i in range(1, 11)]
            result = await compactor.compact(outputs)

            assert result == "Many outputs consolidated"
            mock_agent.invoke.assert_called_once()

    async def test_compact_mixed_languages(self) -> None:
        mock_agent = MagicMock()
        mock_response = MagicMock()
        mock_response.response = "Multilingual consolidated"
        mock_agent.invoke = AsyncMock(return_value=mock_response)

        with patch("midori_ai_compactor.compactor.MidoriAiLogger") as mock_logger_class:
            mock_logger = MagicMock()
            mock_logger.print = AsyncMock()
            mock_logger_class.return_value = mock_logger

            compactor = ThinkingCompactor(agent=mock_agent)
            outputs = ["English analysis", "분석 내용 (Korean)", "Análisis (Spanish)"]
            result = await compactor.compact(outputs)

            assert result == "Multilingual consolidated"
            call_args = mock_agent.invoke.call_args
            payload = call_args[0][0]
            assert "English analysis" in payload.user_message
            assert "분석 내용" in payload.user_message
            assert "Análisis" in payload.user_message

    async def test_compact_with_custom_prompt(self) -> None:
        mock_agent = MagicMock()
        mock_response = MagicMock()
        mock_response.response = "Custom prompt result"
        mock_agent.invoke = AsyncMock(return_value=mock_response)
        config = CompactorConfig(custom_prompt="Merge:\n{outputs}\nEnd.")

        with patch("midori_ai_compactor.compactor.MidoriAiLogger") as mock_logger_class:
            mock_logger = MagicMock()
            mock_logger.print = AsyncMock()
            mock_logger_class.return_value = mock_logger

            compactor = ThinkingCompactor(agent=mock_agent, config=config)
            result = await compactor.compact(["A", "B"])

            assert result == "Custom prompt result"
            call_args = mock_agent.invoke.call_args
            payload = call_args[0][0]
            assert "Merge:" in payload.user_message
            assert "End." in payload.user_message

    async def test_compact_payload_structure(self) -> None:
        mock_agent = MagicMock()
        mock_response = MagicMock()
        mock_response.response = "Result"
        mock_agent.invoke = AsyncMock(return_value=mock_response)

        with patch("midori_ai_compactor.compactor.MidoriAiLogger") as mock_logger_class:
            mock_logger = MagicMock()
            mock_logger.print = AsyncMock()
            mock_logger_class.return_value = mock_logger

            compactor = ThinkingCompactor(agent=mock_agent)
            await compactor.compact(["X", "Y"])

            call_args = mock_agent.invoke.call_args
            payload = call_args[0][0]

            assert payload.thinking_blob == ""
            assert payload.system_context == ""
            assert payload.user_profile == {}
            assert payload.tools_available == []
            assert payload.session_id == "compactor-session"


@pytest.mark.asyncio
class TestThinkingCompactorLogging:
    """Tests for logging in ThinkingCompactor."""

    async def test_compact_logs_debug_messages(self) -> None:
        mock_agent = MagicMock()
        mock_response = MagicMock()
        mock_response.response = "Result"
        mock_agent.invoke = AsyncMock(return_value=mock_response)

        with patch("midori_ai_compactor.compactor.MidoriAiLogger") as mock_logger_class:
            mock_logger = MagicMock()
            mock_logger.print = AsyncMock()
            mock_logger_class.return_value = mock_logger

            compactor = ThinkingCompactor(agent=mock_agent)
            await compactor.compact(["A", "B"])

            assert mock_logger.print.call_count >= 2
            first_call = mock_logger.print.call_args_list[0]
            assert first_call[1].get("mode") == "debug"
