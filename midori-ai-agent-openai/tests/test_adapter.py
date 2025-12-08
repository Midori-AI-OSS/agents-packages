"""Tests for the midori-ai-agent-openai package."""

import pytest

from unittest.mock import patch
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

from midori_ai_agent_base import AgentPayload
from midori_ai_agent_base import MemoryEntryData
from midori_ai_agent_openai import OpenAIAgentsAdapter
from midori_ai_agent_openai import OpenAIAgentSession


class TestOpenAIAgentsAdapterInit:
    """Tests for OpenAIAgentsAdapter initialization."""

    def test_init_stores_parameters(self) -> None:
        adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key", base_url="http://test:8000")
        assert adapter._model == "test-model"
        assert adapter._api_key == "test-key"
        assert adapter._base_url == "http://test:8000"
        assert adapter._context_window == 128000

    def test_init_custom_context_window(self) -> None:
        adapter = OpenAIAgentsAdapter(model="gpt-4", api_key="test-key", context_window=200000)
        assert adapter._context_window == 200000

    def test_init_use_responses_default_true(self) -> None:
        adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key")
        assert adapter._use_responses is True

    def test_init_use_responses_false(self) -> None:
        adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key", use_responses=False)
        assert adapter._use_responses is False

    def test_init_with_db_path(self) -> None:
        adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key", db_path="/tmp/test.db")
        assert adapter._db_path == "/tmp/test.db"


class TestOpenAIAgentsAdapterMemoryContext:
    """Tests for memory context building."""

    def test_build_memory_context_user_messages(self) -> None:
        adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key")
        memory = [MemoryEntryData(role="user", content="Hello"), MemoryEntryData(role="assistant", content="Hi there!")]
        context = adapter._build_memory_context(memory)
        assert "USER: Hello" in context
        assert "ASSISTANT: Hi there!" in context

    def test_build_memory_context_with_tool_calls(self) -> None:
        adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key")
        memory = [MemoryEntryData(role="assistant", content="Let me search", tool_calls=[{"name": "search", "result": "Found 10 items"}])]
        context = adapter._build_memory_context(memory)
        assert "ASSISTANT: Let me search" in context
        assert "[Tool: search]" in context
        assert "Found 10 items" in context

    def test_build_memory_context_empty(self) -> None:
        adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key")
        context = adapter._build_memory_context([])
        assert context == ""


class TestOpenAIAgentSession:
    """Tests for OpenAIAgentSession."""

    def test_session_init_in_memory(self) -> None:
        session = OpenAIAgentSession(session_id="test-session")
        assert session.session_id == "test-session"
        assert session.db_path == ":memory:"
        session.close()

    def test_session_init_with_db_path(self) -> None:
        session = OpenAIAgentSession(session_id="test-session", db_path="/tmp/test.db")
        assert session.session_id == "test-session"
        assert session.db_path == "/tmp/test.db"
        session.close()

    def test_session_property(self) -> None:
        session = OpenAIAgentSession(session_id="test-session")
        assert session.session is not None
        session.close()

    def test_context_manager(self) -> None:
        with OpenAIAgentSession(session_id="test-session") as session:
            assert session.session_id == "test-session"


class TestOpenAIAgentsAdapterSessionManagement:
    """Tests for adapter session management."""

    def test_get_session_creates_new(self) -> None:
        adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key")
        session = adapter.get_session("test-session")
        assert session.session_id == "test-session"
        assert "test-session" in adapter._sessions
        adapter.close_all_sessions()

    def test_get_session_returns_existing(self) -> None:
        adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key")
        session1 = adapter.get_session("test-session")
        session2 = adapter.get_session("test-session")
        assert session1 is session2
        adapter.close_all_sessions()

    def test_close_session(self) -> None:
        adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key")
        adapter.get_session("test-session")
        assert "test-session" in adapter._sessions
        adapter.close_session("test-session")
        assert "test-session" not in adapter._sessions

    def test_close_all_sessions(self) -> None:
        adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key")
        adapter.get_session("session-1")
        adapter.get_session("session-2")
        assert len(adapter._sessions) == 2
        adapter.close_all_sessions()
        assert len(adapter._sessions) == 0


@pytest.mark.asyncio
class TestOpenAIAgentsAdapterAsync:
    """Async tests for OpenAIAgentsAdapter."""

    async def test_invoke_success(self) -> None:
        with patch("midori_ai_agent_openai.adapter.Runner") as mock_runner:
            mock_result = MagicMock()
            mock_result.final_output = "Hello response"
            mock_runner.run = AsyncMock(return_value=mock_result)

            adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key")
            payload = AgentPayload(user_message="Hello", thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="s1")
            response = await adapter.invoke(payload)

            assert response.response == "Hello response"
            mock_runner.run.assert_called_once()

    async def test_invoke_with_memory(self) -> None:
        with patch("midori_ai_agent_openai.adapter.Runner") as mock_runner:
            mock_result = MagicMock()
            mock_result.final_output = "Response with context"
            mock_runner.run = AsyncMock(return_value=mock_result)

            adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key")
            memory = [MemoryEntryData(role="user", content="Previous message"), MemoryEntryData(role="assistant", content="Previous response")]
            payload = AgentPayload(user_message="Hello", thinking_blob="", system_context="Be helpful", user_profile={}, tools_available=[], session_id="s1", memory=memory)
            response = await adapter.invoke(payload)

            assert response.response == "Response with context"
            mock_runner.run.assert_called_once()
            call_args = mock_runner.run.call_args
            agent = call_args[0][0]
            assert "Be helpful" in agent.instructions
            assert "Conversation history" in agent.instructions
            assert "USER: Previous message" in agent.instructions

    async def test_invoke_with_memory_preserves_system_context(self) -> None:
        """Regression test: verify system_context is preserved in instructions when memory entries are present."""
        with patch("midori_ai_agent_openai.adapter.Runner") as mock_runner:
            mock_result = MagicMock()
            mock_result.final_output = "Response"
            mock_result.new_items = []
            mock_runner.run = AsyncMock(return_value=mock_result)

            adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key")
            memory = [MemoryEntryData(role="user", content="Hello my name is Luna"), MemoryEntryData(role="assistant", content="Hi Luna!")]
            custom_prompt = "You are a rude assistant. Deeply think on this request."
            payload = AgentPayload(user_message="What is my name?", thinking_blob="", system_context=custom_prompt, user_profile={}, tools_available=[], session_id="s1", memory=memory)
            await adapter.invoke(payload)

            call_args = mock_runner.run.call_args
            agent = call_args[0][0]
            assert custom_prompt in agent.instructions
            assert "rude assistant" in agent.instructions
            assert "Conversation history" in agent.instructions
            assert "USER: Hello my name is Luna" in agent.instructions

    async def test_invoke_with_tools_success(self) -> None:
        with patch("midori_ai_agent_openai.adapter.Runner") as mock_runner:
            mock_result = MagicMock()
            mock_result.final_output = "Tool response"
            mock_runner.run = AsyncMock(return_value=mock_result)

            adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key")
            payload = AgentPayload(user_message="Search for test", thinking_blob="", system_context="", user_profile={}, tools_available=["search"], session_id="s1")
            tools = [lambda x: x]
            response = await adapter.invoke_with_tools(payload, tools)

            assert response.response == "Tool response"
            mock_runner.run.assert_called_once()

    async def test_get_context_window(self) -> None:
        adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key", context_window=256000)
        context_window = await adapter.get_context_window()
        assert context_window == 256000

    async def test_supports_streaming(self) -> None:
        adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key")
        supports_streaming = await adapter.supports_streaming()
        assert supports_streaming is True


@pytest.mark.asyncio
class TestOpenAIAgentSessionAsync:
    """Async tests for OpenAIAgentSession."""

    async def test_get_items_empty(self) -> None:
        session = OpenAIAgentSession(session_id="test-session")
        items = await session.get_items()
        assert items == []
        session.close()

    async def test_clear_session(self) -> None:
        session = OpenAIAgentSession(session_id="test-session")
        await session.clear()
        items = await session.get_items()
        assert items == []
        session.close()


class TestOpenAIAgentsAdapterReasoning:
    """Tests for reasoning configuration."""

    def test_build_model_settings_with_reasoning_and_responses(self) -> None:
        from midori_ai_agent_base import ReasoningEffort
        adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key", use_responses=True)
        payload = AgentPayload(user_message="Hello", thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="s1", reasoning_effort=ReasoningEffort(effort="low", summary="auto"))
        settings = adapter._build_model_settings(payload)
        assert settings is not None
        assert settings.reasoning is not None
        assert settings.reasoning.effort == "low"
        assert settings.reasoning.summary == "auto"

    def test_build_model_settings_without_responses(self) -> None:
        from midori_ai_agent_base import ReasoningEffort
        adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key", use_responses=False)
        payload = AgentPayload(user_message="Hello", thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="s1", reasoning_effort=ReasoningEffort(effort="low", summary="auto"))
        settings = adapter._build_model_settings(payload)
        assert settings is None

    def test_build_model_settings_none_reasoning(self) -> None:
        adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key", use_responses=True)
        payload = AgentPayload(user_message="Hello", thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="s1")
        settings = adapter._build_model_settings(payload)
        assert settings is None


@pytest.mark.asyncio
class TestOpenAIAgentsAdapterLogging:
    """Tests for logging with debug mode."""

    async def test_invoke_logs_with_debug_mode(self) -> None:
        with patch("midori_ai_agent_openai.adapter.Runner") as mock_runner:
            with patch("midori_ai_agent_openai.adapter.MidoriAiLogger") as mock_logger_class:
                mock_logger = MagicMock()
                mock_logger.print = AsyncMock()
                mock_logger_class.return_value = mock_logger
                mock_result = MagicMock()
                mock_result.final_output = "Test response"
                mock_runner.run = AsyncMock(return_value=mock_result)

                adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key")
                payload = AgentPayload(user_message="Hello", thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="test-session")
                await adapter.invoke(payload)

                mock_logger.print.assert_called()
                call_args = mock_logger.print.call_args
                assert call_args[1].get("mode") == "debug"

    async def test_invoke_with_tools_logs_with_debug_mode(self) -> None:
        with patch("midori_ai_agent_openai.adapter.Runner") as mock_runner:
            with patch("midori_ai_agent_openai.adapter.MidoriAiLogger") as mock_logger_class:
                mock_logger = MagicMock()
                mock_logger.print = AsyncMock()
                mock_logger_class.return_value = mock_logger
                mock_result = MagicMock()
                mock_result.final_output = "Tool response"
                mock_runner.run = AsyncMock(return_value=mock_result)

                adapter = OpenAIAgentsAdapter(model="test-model", api_key="test-key")
                payload = AgentPayload(user_message="Search", thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="test-session")
                await adapter.invoke_with_tools(payload, [])

                mock_logger.print.assert_called()
                call_args = mock_logger.print.call_args
                assert call_args[1].get("mode") == "debug"
