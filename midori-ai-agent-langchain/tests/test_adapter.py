"""Tests for the midori-ai-agent-langchain package."""

import pytest

from unittest.mock import patch
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

from midori_ai_agent_base import AgentPayload
from midori_ai_agent_base import MemoryEntryData
from midori_ai_agent_langchain import LangchainAgent


class TestLangchainAgentInit:
    """Tests for LangchainAgent initialization."""

    def test_init_creates_model(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI") as mock_chat:
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
            mock_chat.assert_called_once()
            assert agent._context_window == 128000

    def test_init_custom_context_window(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI"):
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000", context_window=200000)
            assert agent._context_window == 200000

    def test_init_use_responses_api_default_true(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI") as mock_chat:
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
            assert agent._use_responses_api is True
            call_kwargs = mock_chat.call_args.kwargs
            assert call_kwargs.get("use_responses_api") is True

    def test_init_use_responses_api_false(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI") as mock_chat:
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000", use_responses_api=False)
            assert agent._use_responses_api is False
            call_kwargs = mock_chat.call_args.kwargs
            assert call_kwargs.get("use_responses_api") is False


class TestLangchainAgentMessageBuilding:
    """Tests for message building."""

    def test_build_messages_basic(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI"):
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
            payload = AgentPayload(user_message="Hello", thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="s1")
            messages = agent._build_messages(payload)
            assert len(messages) == 1
            assert messages[0].content == "Hello"

    def test_build_messages_with_system_context(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI"):
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
            payload = AgentPayload(user_message="Hello", thinking_blob="", system_context="You are helpful", user_profile={}, tools_available=[], session_id="s1")
            messages = agent._build_messages(payload)
            assert len(messages) == 2
            assert messages[0].content == "You are helpful"
            assert messages[1].content == "Hello"

    def test_build_messages_with_thinking_blob(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI"):
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
            payload = AgentPayload(user_message="Hello", thinking_blob="Previous thinking", system_context="System", user_profile={}, tools_available=[], session_id="s1")
            messages = agent._build_messages(payload)
            assert len(messages) == 3
            assert messages[0].content == "System"
            assert messages[1].content == "Previous thinking"
            assert messages[2].content == "Hello"

    def test_build_messages_with_memory(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI"):
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
            memory = [MemoryEntryData(role="user", content="First message"), MemoryEntryData(role="assistant", content="First response"), MemoryEntryData(role="user", content="Second message")]
            payload = AgentPayload(user_message="Hello", thinking_blob="", system_context="System", user_profile={}, tools_available=[], session_id="s1", memory=memory)
            messages = agent._build_messages(payload)
            assert len(messages) == 5
            assert messages[0].content == "System"
            assert messages[1].content == "First message"
            assert messages[2].content == "First response"
            assert messages[3].content == "Second message"
            assert messages[4].content == "Hello"

    def test_build_messages_memory_overrides_thinking_blob(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI"):
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
            memory = [MemoryEntryData(role="user", content="Memory message")]
            payload = AgentPayload(user_message="Hello", thinking_blob="This should be ignored", system_context="System", user_profile={}, tools_available=[], session_id="s1", memory=memory)
            messages = agent._build_messages(payload)
            assert len(messages) == 3
            assert messages[1].content == "Memory message"

    def test_build_messages_with_memory_preserves_system_context(self) -> None:
        """Regression test: verify system_context is preserved as SystemMessage when memory entries are present."""
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI"):
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
            memory = [MemoryEntryData(role="user", content="Hello my name is Luna"), MemoryEntryData(role="assistant", content="Hi Luna!")]
            custom_prompt = "You are a rude assistant. Deeply think on this request."
            payload = AgentPayload(user_message="What is my name?", thinking_blob="", system_context=custom_prompt, user_profile={}, tools_available=[], session_id="s1", memory=memory)
            messages = agent._build_messages(payload)
            assert len(messages) == 4
            assert messages[0].__class__.__name__ == "SystemMessage"
            assert messages[0].content == custom_prompt
            assert "rude assistant" in messages[0].content


class TestLangchainAgentMemoryConversion:
    """Tests for memory entry to message conversion."""

    def test_memory_entry_to_message_user(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI"):
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
            entry = MemoryEntryData(role="user", content="User message")
            msg = agent._memory_entry_to_message(entry)
            assert msg is not None
            assert msg.content == "User message"
            assert msg.__class__.__name__ == "HumanMessage"

    def test_memory_entry_to_message_assistant(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI"):
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
            entry = MemoryEntryData(role="assistant", content="Assistant message")
            msg = agent._memory_entry_to_message(entry)
            assert msg is not None
            assert msg.content == "Assistant message"
            assert msg.__class__.__name__ == "AIMessage"

    def test_memory_entry_to_message_system(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI"):
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
            entry = MemoryEntryData(role="system", content="System message")
            msg = agent._memory_entry_to_message(entry)
            assert msg is not None
            assert msg.content == "System message"
            assert msg.__class__.__name__ == "SystemMessage"

    def test_memory_entry_to_message_tool(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI"):
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
            entry = MemoryEntryData(role="tool", content="Tool result", tool_calls=[{"name": "search", "call_id": "call-123"}])
            msg = agent._memory_entry_to_message(entry)
            assert msg is not None
            assert msg.content == "Tool result"
            assert msg.__class__.__name__ == "ToolMessage"

    def test_memory_entry_to_message_unknown_returns_none(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI"):
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
            entry = MemoryEntryData(role="unknown_role", content="Some message")
            msg = agent._memory_entry_to_message(entry)
            assert msg is None


@pytest.mark.asyncio
class TestLangchainAgentAsync:
    """Async tests for LangchainAgent."""

    async def test_invoke_success(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI") as mock_chat:
            mock_model = MagicMock()
            mock_result = MagicMock()
            mock_result.text.return_value = "Hello response"
            mock_result.content = "Hello response"
            mock_model.ainvoke = AsyncMock(return_value=mock_result)
            mock_chat.return_value = mock_model

            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
            payload = AgentPayload(user_message="Hello", thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="s1")
            response = await agent.invoke(payload)

            assert response.response == "Hello response"
            mock_model.ainvoke.assert_called_once()

    async def test_invoke_with_tools_success(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI") as mock_chat:
            mock_model = MagicMock()
            mock_bound_model = MagicMock()
            mock_result = MagicMock()
            mock_result.text.return_value = "Tool response"
            mock_result.content = "Tool response"
            mock_result.tool_calls = [{"name": "search", "args": {"query": "test"}}]
            mock_bound_model.ainvoke = AsyncMock(return_value=mock_result)
            mock_model.bind_tools = MagicMock(return_value=mock_bound_model)
            mock_chat.return_value = mock_model

            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
            payload = AgentPayload(user_message="Search for test", thinking_blob="", system_context="", user_profile={}, tools_available=["search"], session_id="s1")
            tools = [{"name": "search", "description": "Search tool"}]
            response = await agent.invoke_with_tools(payload, tools)

            assert response.response == "Tool response"
            assert response.tool_calls is not None
            assert len(response.tool_calls) == 1
            assert response.tool_calls[0]["name"] == "search"
            mock_model.bind_tools.assert_called_once_with(tools)

    async def test_get_context_window(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI"):
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000", context_window=256000)
            context_window = await agent.get_context_window()
            assert context_window == 256000

    async def test_supports_streaming(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI"):
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
            supports_streaming = await agent.supports_streaming()
            assert supports_streaming is True


class TestLangchainAgentReasoning:
    """Tests for reasoning configuration."""

    def test_apply_reasoning_with_responses_api(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI") as mock_chat:
            mock_model = MagicMock()
            mock_bound = MagicMock()
            mock_model.bind = MagicMock(return_value=mock_bound)
            mock_chat.return_value = mock_model
            from midori_ai_agent_base import ReasoningEffort
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000", use_responses_api=True)
            reasoning = ReasoningEffort(effort="low", summary="auto")
            result = agent._apply_reasoning(mock_model, reasoning)
            mock_model.bind.assert_called_once()
            call_kwargs = mock_model.bind.call_args.kwargs
            assert "reasoning" in call_kwargs
            assert call_kwargs["reasoning"]["effort"] == "low"
            assert call_kwargs["reasoning"]["summary"] == "auto"
            assert result == mock_bound

    def test_apply_reasoning_without_responses_api(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI") as mock_chat:
            mock_model = MagicMock()
            mock_chat.return_value = mock_model
            from midori_ai_agent_base import ReasoningEffort
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000", use_responses_api=False)
            reasoning = ReasoningEffort(effort="low", summary="auto")
            result = agent._apply_reasoning(mock_model, reasoning)
            mock_model.bind.assert_not_called()
            assert result == mock_model

    def test_apply_reasoning_none(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI") as mock_chat:
            mock_model = MagicMock()
            mock_chat.return_value = mock_model
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
            result = agent._apply_reasoning(mock_model, None)
            mock_model.bind.assert_not_called()
            assert result == mock_model


class TestLangchainAgentResponseParsing:
    """Tests for response parsing with structured content."""

    def test_parse_response_simple_string(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI"):
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
            mock_result = MagicMock()
            mock_result.content = "Simple text response"
            response = agent._parse_response(mock_result)
            assert response.thinking == ""
            assert response.response == "Simple text response"

    def test_parse_response_structured_with_reasoning(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI"):
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
            mock_result = MagicMock()
            mock_result.content = [{"type": "reasoning", "content": [{"text": "I should think about this."}]}, {"type": "text", "text": "Here is my response."}]
            response = agent._parse_response(mock_result)
            assert response.thinking == "I should think about this."
            assert response.response == "Here is my response."

    def test_parse_response_no_reasoning_leaves_thinking_empty(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI"):
            agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
            mock_result = MagicMock()
            mock_result.content = [{"type": "text", "text": "Just a response with no reasoning."}]
            response = agent._parse_response(mock_result)
            assert response.thinking == ""
            assert response.response == "Just a response with no reasoning."


@pytest.mark.asyncio
class TestLangchainAgentLogging:
    """Tests for logging with debug mode."""

    async def test_invoke_logs_with_debug_mode(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI") as mock_chat:
            with patch("midori_ai_agent_langchain.adapter.MidoriAiLogger") as mock_logger_class:
                mock_logger = MagicMock()
                mock_logger.print = AsyncMock()
                mock_logger_class.return_value = mock_logger
                mock_model = MagicMock()
                mock_result = MagicMock()
                mock_result.content = "Test response"
                mock_model.ainvoke = AsyncMock(return_value=mock_result)
                mock_chat.return_value = mock_model

                agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
                payload = AgentPayload(user_message="Hello", thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="test-session")
                await agent.invoke(payload)

                mock_logger.print.assert_called()
                call_args = mock_logger.print.call_args
                assert call_args[1].get("mode") == "debug"

    async def test_invoke_with_tools_logs_with_debug_mode(self) -> None:
        with patch("midori_ai_agent_langchain.adapter.ChatOpenAI") as mock_chat:
            with patch("midori_ai_agent_langchain.adapter.MidoriAiLogger") as mock_logger_class:
                mock_logger = MagicMock()
                mock_logger.print = AsyncMock()
                mock_logger_class.return_value = mock_logger
                mock_model = MagicMock()
                mock_bound_model = MagicMock()
                mock_result = MagicMock()
                mock_result.content = "Tool response"
                mock_result.tool_calls = []
                mock_bound_model.ainvoke = AsyncMock(return_value=mock_result)
                mock_model.bind_tools = MagicMock(return_value=mock_bound_model)
                mock_chat.return_value = mock_model

                agent = LangchainAgent(model="test-model", api_key="test-key", base_url="http://test:8000")
                payload = AgentPayload(user_message="Search", thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="test-session")
                await agent.invoke_with_tools(payload, [])

                mock_logger.print.assert_called()
                call_args = mock_logger.print.call_args
                assert call_args[1].get("mode") == "debug"
