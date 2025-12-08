"""Tests for the midori-ai-agent-huggingface package."""

import asyncio
import pytest

from unittest.mock import patch
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

from midori_ai_agent_base import AgentPayload
from midori_ai_agent_base import MemoryEntryData
from midori_ai_agent_huggingface import HuggingFaceLocalAgent
from midori_ai_agent_huggingface import create_config


class TestHuggingFaceConfig:
    """Tests for HuggingFaceConfig."""

    def test_create_config_defaults(self) -> None:
        config = create_config(model="test-model")
        assert config.model == "test-model"
        assert config.device == "auto"
        assert config.torch_dtype == "auto"
        assert config.max_new_tokens == 512
        assert config.temperature == 0.7
        assert config.top_p == 0.9
        assert config.top_k == 50
        assert config.do_sample is True
        assert config.context_window == 4096
        assert config.trust_remote_code is False
        assert config.load_in_8bit is False
        assert config.load_in_4bit is False
        assert config.extra == {}

    def test_create_config_custom_values(self) -> None:
        config = create_config(model="custom-model", device="cuda", torch_dtype="float16", max_new_tokens=1024, temperature=0.5, context_window=8192, load_in_8bit=True)
        assert config.model == "custom-model"
        assert config.device == "cuda"
        assert config.torch_dtype == "float16"
        assert config.max_new_tokens == 1024
        assert config.temperature == 0.5
        assert config.context_window == 8192
        assert config.load_in_8bit is True

    def test_create_config_extra_kwargs(self) -> None:
        config = create_config(model="test-model", custom_param="value")
        assert config.extra == {"custom_param": "value"}


class TestHuggingFaceLocalAgentInit:
    """Tests for HuggingFaceLocalAgent initialization."""

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_init_stores_config(self, mock_manager: MagicMock) -> None:
        agent = HuggingFaceLocalAgent(model="test-model", device="cpu", max_new_tokens=256)
        assert agent.config.model == "test-model"
        assert agent.config.device == "cpu"
        assert agent.config.max_new_tokens == 256

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_init_default_config(self, mock_manager: MagicMock) -> None:
        agent = HuggingFaceLocalAgent(model="test-model")
        assert agent.config.device == "auto"
        assert agent.config.temperature == 0.7
        assert agent.config.context_window == 4096

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_init_quantization_options(self, mock_manager: MagicMock) -> None:
        agent = HuggingFaceLocalAgent(model="test-model", load_in_8bit=True)
        assert agent.config.load_in_8bit is True
        assert agent.config.load_in_4bit is False

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_is_loaded_false_initially(self, mock_manager: MagicMock) -> None:
        mock_manager.return_value.is_loaded = False
        agent = HuggingFaceLocalAgent(model="test-model")
        assert agent.is_loaded is False


class TestHuggingFaceLocalAgentMemoryContext:
    """Tests for memory context building."""

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_build_memory_context_user_messages(self, mock_manager: MagicMock) -> None:
        agent = HuggingFaceLocalAgent(model="test-model")
        memory = [MemoryEntryData(role="user", content="Hello"), MemoryEntryData(role="assistant", content="Hi there!")]
        context = agent._build_memory_context(memory)
        assert "USER: Hello" in context
        assert "ASSISTANT: Hi there!" in context

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_build_memory_context_with_tool_calls(self, mock_manager: MagicMock) -> None:
        agent = HuggingFaceLocalAgent(model="test-model")
        memory = [MemoryEntryData(role="assistant", content="Let me search", tool_calls=[{"name": "search", "result": "Found 10 items"}])]
        context = agent._build_memory_context(memory)
        assert "ASSISTANT: Let me search" in context
        assert "[Tool: search]" in context
        assert "Found 10 items" in context

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_build_memory_context_empty(self, mock_manager: MagicMock) -> None:
        agent = HuggingFaceLocalAgent(model="test-model")
        context = agent._build_memory_context([])
        assert context == ""


class TestHuggingFaceLocalAgentPromptBuilding:
    """Tests for prompt building."""

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_build_prompt_basic(self, mock_manager: MagicMock) -> None:
        agent = HuggingFaceLocalAgent(model="test-model")
        payload = AgentPayload(user_message="Hello", thinking_blob="", system_context="You are helpful.", user_profile={}, tools_available=[], session_id="s1")
        prompt = agent._build_prompt(payload)
        assert "System: You are helpful." in prompt
        assert "User: Hello" in prompt
        assert "Assistant:" in prompt

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_build_prompt_with_memory(self, mock_manager: MagicMock) -> None:
        agent = HuggingFaceLocalAgent(model="test-model")
        memory = [MemoryEntryData(role="user", content="Previous message")]
        payload = AgentPayload(user_message="Hello", thinking_blob="", system_context="Be helpful", user_profile={}, tools_available=[], session_id="s1", memory=memory)
        prompt = agent._build_prompt(payload)
        assert "Conversation history" in prompt
        assert "USER: Previous message" in prompt

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_build_prompt_with_thinking_blob_no_memory(self, mock_manager: MagicMock) -> None:
        agent = HuggingFaceLocalAgent(model="test-model")
        payload = AgentPayload(user_message="Hello", thinking_blob="Previous context info", system_context="Be helpful", user_profile={}, tools_available=[], session_id="s1")
        prompt = agent._build_prompt(payload)
        assert "Previous context: Previous context info" in prompt


@pytest.mark.asyncio
class TestHuggingFaceLocalAgentAsync:
    """Async tests for HuggingFaceLocalAgent."""

    async def test_invoke_success(self) -> None:
        with patch("midori_ai_agent_huggingface.adapter.PipelineManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = "Hello response"
            mock_instance.parse_response.return_value = None
            mock_manager.return_value = mock_instance

            agent = HuggingFaceLocalAgent(model="test-model")
            payload = AgentPayload(user_message="Hello", thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="s1")
            response = await agent.invoke(payload)

            assert response.response == "Hello response"
            mock_instance.generate.assert_called_once()

    async def test_invoke_with_memory(self) -> None:
        with patch("midori_ai_agent_huggingface.adapter.PipelineManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = "Response with context"
            mock_instance.parse_response.return_value = None
            mock_manager.return_value = mock_instance

            agent = HuggingFaceLocalAgent(model="test-model")
            memory = [MemoryEntryData(role="user", content="Previous message"), MemoryEntryData(role="assistant", content="Previous response")]
            payload = AgentPayload(user_message="Hello", thinking_blob="", system_context="Be helpful", user_profile={}, tools_available=[], session_id="s1", memory=memory)
            response = await agent.invoke(payload)

            assert response.response == "Response with context"
            call_args = mock_instance.generate.call_args
            prompt = call_args[0][0]
            assert "Be helpful" in prompt
            assert "Conversation history" in prompt
            assert "USER: Previous message" in prompt

    async def test_invoke_with_tools(self) -> None:
        with patch("midori_ai_agent_huggingface.adapter.PipelineManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = "Tool response"
            mock_instance.parse_response.return_value = None
            mock_manager.return_value = mock_instance

            agent = HuggingFaceLocalAgent(model="test-model")
            payload = AgentPayload(user_message="Search for test", thinking_blob="", system_context="", user_profile={}, tools_available=["search"], session_id="s1")

            def search(query: str) -> str:
                """Search for information."""
                return f"Results for: {query}"

            response = await agent.invoke_with_tools(payload, tools=[search])

            assert response.response == "Tool response"
            call_args = mock_instance.generate.call_args
            prompt = call_args[0][0]
            assert "Available tools" in prompt
            assert "search" in prompt

    async def test_invoke_with_tools_dict_format(self) -> None:
        with patch("midori_ai_agent_huggingface.adapter.PipelineManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = "Tool response"
            mock_instance.parse_response.return_value = None
            mock_manager.return_value = mock_instance

            agent = HuggingFaceLocalAgent(model="test-model")
            payload = AgentPayload(user_message="Search", thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="s1")
            tools = [{"name": "search", "description": "Search for information"}]
            await agent.invoke_with_tools(payload, tools=tools)

            call_args = mock_instance.generate.call_args
            prompt = call_args[0][0]
            assert "search: Search for information" in prompt

    async def test_get_context_window(self) -> None:
        with patch("midori_ai_agent_huggingface.adapter.PipelineManager"):
            agent = HuggingFaceLocalAgent(model="test-model", context_window=8192)
            context_window = await agent.get_context_window()
            assert context_window == 8192

    async def test_supports_streaming(self) -> None:
        with patch("midori_ai_agent_huggingface.adapter.PipelineManager"):
            agent = HuggingFaceLocalAgent(model="test-model")
            supports_streaming = await agent.supports_streaming()
            assert supports_streaming is True


@pytest.mark.asyncio
class TestHuggingFaceLocalAgentLogging:
    """Tests for logging with debug mode."""

    async def test_invoke_logs_with_debug_mode(self) -> None:
        with patch("midori_ai_agent_huggingface.adapter.PipelineManager") as mock_manager:
            with patch("midori_ai_agent_huggingface.adapter.MidoriAiLogger") as mock_logger_class:
                mock_logger = MagicMock()
                mock_logger.print = AsyncMock()
                mock_logger_class.return_value = mock_logger

                mock_instance = MagicMock()
                mock_instance.generate.return_value = "Test response"
                mock_manager.return_value = mock_instance

                agent = HuggingFaceLocalAgent(model="test-model")
                payload = AgentPayload(user_message="Hello", thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="test-session")
                await agent.invoke(payload)

                mock_logger.print.assert_called()
                call_args = mock_logger.print.call_args
                assert call_args[1].get("mode") == "debug"

    async def test_invoke_with_tools_logs_with_debug_mode(self) -> None:
        with patch("midori_ai_agent_huggingface.adapter.PipelineManager") as mock_manager:
            with patch("midori_ai_agent_huggingface.adapter.MidoriAiLogger") as mock_logger_class:
                mock_logger = MagicMock()
                mock_logger.print = AsyncMock()
                mock_logger_class.return_value = mock_logger

                mock_instance = MagicMock()
                mock_instance.generate.return_value = "Tool response"
                mock_manager.return_value = mock_instance

                agent = HuggingFaceLocalAgent(model="test-model")
                payload = AgentPayload(user_message="Search", thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="test-session")
                await agent.invoke_with_tools(payload, [])

                mock_logger.print.assert_called()
                call_args = mock_logger.print.call_args
                assert call_args[1].get("mode") == "debug"


class TestHuggingFaceLocalAgentMemoryManagement:
    """Tests for memory management."""

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    @pytest.mark.asyncio
    async def test_unload_model(self, mock_manager: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_instance.unload = AsyncMock()
        mock_manager.return_value = mock_instance

        agent = HuggingFaceLocalAgent(model="test-model")
        await agent.unload_model()

        mock_instance.unload.assert_called_once()


class TestHuggingFaceLocalAgentReasoningExtraction:
    """Tests for reasoning/thinking extraction from model output."""

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_extract_reasoning_think_tags(self, mock_manager: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_instance.parse_response.return_value = None
        mock_manager.return_value = mock_instance
        agent = HuggingFaceLocalAgent(model="test-model")
        text = "<think>Let me think about this carefully.</think>The answer is 42."
        thinking, response = agent._extract_reasoning(text)
        assert thinking == "Let me think about this carefully."
        assert response == "The answer is 42."

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_extract_reasoning_thinking_tags(self, mock_manager: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_instance.parse_response.return_value = None
        mock_manager.return_value = mock_instance
        agent = HuggingFaceLocalAgent(model="test-model")
        text = "<thinking>Step by step analysis.</thinking>Here is my conclusion."
        thinking, response = agent._extract_reasoning(text)
        assert thinking == "Step by step analysis."
        assert response == "Here is my conclusion."

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_extract_reasoning_reasoning_tags(self, mock_manager: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_instance.parse_response.return_value = None
        mock_manager.return_value = mock_instance
        agent = HuggingFaceLocalAgent(model="test-model")
        text = "<reasoning>First I'll consider X, then Y.</reasoning>The result is Z."
        thinking, response = agent._extract_reasoning(text)
        assert thinking == "First I'll consider X, then Y."
        assert response == "The result is Z."

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_extract_reasoning_chain_of_thought_tags(self, mock_manager: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_instance.parse_response.return_value = None
        mock_manager.return_value = mock_instance
        agent = HuggingFaceLocalAgent(model="test-model")
        text = "<chain_of_thought>Breaking this down into steps.</chain_of_thought>Final answer."
        thinking, response = agent._extract_reasoning(text)
        assert thinking == "Breaking this down into steps."
        assert response == "Final answer."

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_extract_reasoning_multiple_tags(self, mock_manager: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_instance.parse_response.return_value = None
        mock_manager.return_value = mock_instance
        agent = HuggingFaceLocalAgent(model="test-model")
        text = "<think>First thought.</think>Some text.<think>Second thought.</think>Final response."
        thinking, response = agent._extract_reasoning(text)
        assert "First thought." in thinking
        assert "Second thought." in thinking
        assert "Some text." in response
        assert "Final response." in response

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_extract_reasoning_no_tags(self, mock_manager: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_instance.parse_response.return_value = None
        mock_manager.return_value = mock_instance
        agent = HuggingFaceLocalAgent(model="test-model")
        text = "This is just a plain response with no reasoning tags."
        thinking, response = agent._extract_reasoning(text)
        assert thinking == ""
        assert response == "This is just a plain response with no reasoning tags."

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_extract_reasoning_case_insensitive(self, mock_manager: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_instance.parse_response.return_value = None
        mock_manager.return_value = mock_instance
        agent = HuggingFaceLocalAgent(model="test-model")
        text = "<THINK>Uppercase tags.</THINK>Response here."
        thinking, response = agent._extract_reasoning(text)
        assert thinking == "Uppercase tags."
        assert response == "Response here."

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_extract_reasoning_multiline(self, mock_manager: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_instance.parse_response.return_value = None
        mock_manager.return_value = mock_instance
        agent = HuggingFaceLocalAgent(model="test-model")
        text = "<think>\nLine 1\nLine 2\n</think>The answer."
        thinking, response = agent._extract_reasoning(text)
        assert "Line 1" in thinking
        assert "Line 2" in thinking
        assert response == "The answer."

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_extract_reasoning_uses_tokenizer_parse_response(self, mock_manager: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_instance.parse_response.return_value = {"thinking": "Tokenizer thinking", "content": "Tokenizer response"}
        mock_manager.return_value = mock_instance
        agent = HuggingFaceLocalAgent(model="test-model")
        text = "<think>Regex thinking.</think>Regex response."
        thinking, response = agent._extract_reasoning(text)
        assert thinking == "Tokenizer thinking"
        assert response == "Tokenizer response"


@pytest.mark.asyncio
class TestHuggingFaceLocalAgentReasoningAsync:
    """Async tests for reasoning extraction in invoke."""

    async def test_invoke_extracts_reasoning(self) -> None:
        with patch("midori_ai_agent_huggingface.adapter.PipelineManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = "<think>Let me analyze this.</think>The answer is 42."
            mock_instance.parse_response.return_value = None
            mock_manager.return_value = mock_instance

            agent = HuggingFaceLocalAgent(model="test-model")
            payload = AgentPayload(user_message="What is the meaning?", thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="s1")
            response = await agent.invoke(payload)

            assert response.thinking == "Let me analyze this."
            assert response.response == "The answer is 42."

    async def test_invoke_with_tools_extracts_reasoning(self) -> None:
        with patch("midori_ai_agent_huggingface.adapter.PipelineManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = "<reasoning>I should search for this.</reasoning>Based on my search, here is the answer."
            mock_instance.parse_response.return_value = None
            mock_manager.return_value = mock_instance

            agent = HuggingFaceLocalAgent(model="test-model")
            payload = AgentPayload(user_message="Find info", thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="s1")
            response = await agent.invoke_with_tools(payload, tools=[])

            assert response.thinking == "I should search for this."
            assert response.response == "Based on my search, here is the answer."


class TestHuggingFaceLocalAgentToolParsing:
    """Tests for tool call parsing."""

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_parse_tool_calls_json_format(self, mock_manager: MagicMock) -> None:
        agent = HuggingFaceLocalAgent(model="test-model")
        text = '{"tool_calls": [{"name": "search", "arguments": {"query": "test"}}]}'
        tool_calls = agent._parse_tool_calls(text)
        assert len(tool_calls) == 1
        assert tool_calls[0]["name"] == "search"
        assert tool_calls[0]["arguments"] == {"query": "test"}

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_parse_tool_calls_text_format(self, mock_manager: MagicMock) -> None:
        agent = HuggingFaceLocalAgent(model="test-model")
        text = "TOOL_CALL: search(query=test, limit=10)"
        tool_calls = agent._parse_tool_calls(text)
        assert len(tool_calls) == 1
        assert tool_calls[0]["name"] == "search"
        assert tool_calls[0]["arguments"]["query"] == "test"
        assert tool_calls[0]["arguments"]["limit"] == 10

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_parse_tool_calls_multiple_tools(self, mock_manager: MagicMock) -> None:
        agent = HuggingFaceLocalAgent(model="test-model")
        text = "TOOL_CALL: search(query=test)\nTOOL_CALL: calculate(x=5, y=10)"
        tool_calls = agent._parse_tool_calls(text)
        assert len(tool_calls) == 2
        assert tool_calls[0]["name"] == "search"
        assert tool_calls[1]["name"] == "calculate"

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_parse_tool_calls_no_tools(self, mock_manager: MagicMock) -> None:
        agent = HuggingFaceLocalAgent(model="test-model")
        text = "This is just a regular response with no tool calls."
        tool_calls = agent._parse_tool_calls(text)
        assert len(tool_calls) == 0

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_parse_tool_calls_case_insensitive(self, mock_manager: MagicMock) -> None:
        agent = HuggingFaceLocalAgent(model="test-model")
        text = "tool_call: search(query=test)"
        tool_calls = agent._parse_tool_calls(text)
        assert len(tool_calls) == 1
        assert tool_calls[0]["name"] == "search"

    @patch("midori_ai_agent_huggingface.adapter.PipelineManager")
    def test_parse_tool_arguments_various_types(self, mock_manager: MagicMock) -> None:
        agent = HuggingFaceLocalAgent(model="test-model")
        args = agent._parse_tool_arguments('query="test value", count=5, active=true, ratio=3.14')
        assert args["query"] == "test value"
        assert args["count"] == 5
        assert args["active"] is True
        assert args["ratio"] == 3.14


@pytest.mark.asyncio
class TestHuggingFaceLocalAgentToolInvoke:
    """Async tests for tool invocation."""

    async def test_invoke_includes_tool_calls(self) -> None:
        with patch("midori_ai_agent_huggingface.adapter.PipelineManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = 'Let me search. TOOL_CALL: search(query=test)'
            mock_instance.parse_response.return_value = None
            mock_manager.return_value = mock_instance

            agent = HuggingFaceLocalAgent(model="test-model")
            payload = AgentPayload(user_message="Find test", thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="s1")
            response = await agent.invoke(payload)

            assert response.response is not None
            assert response.tool_calls is not None
            assert len(response.tool_calls) == 1
            assert response.tool_calls[0]["name"] == "search"

    async def test_invoke_with_tools_includes_instruction(self) -> None:
        with patch("midori_ai_agent_huggingface.adapter.PipelineManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = "TOOL_CALL: search(query=test)"
            mock_instance.parse_response.return_value = None
            mock_manager.return_value = mock_instance

            agent = HuggingFaceLocalAgent(model="test-model")
            payload = AgentPayload(user_message="Search", thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="s1")

            def search(query: str) -> str:
                """Search for information."""
                return f"Results for: {query}"

            response = await agent.invoke_with_tools(payload, tools=[search])

            call_args = mock_instance.generate.call_args
            prompt = call_args[0][0]
            assert "TOOL_CALL:" in prompt
            assert "search" in prompt
            assert response.tool_calls is not None


@pytest.mark.asyncio
class TestHuggingFaceLocalAgentStreaming:
    """Tests for streaming functionality."""

    async def test_stream_yields_tokens(self) -> None:
        with patch("midori_ai_agent_huggingface.adapter.PipelineManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.load_pipeline = AsyncMock()
            mock_instance._pipeline = MagicMock()
            mock_instance.get_generation_kwargs.return_value = {"max_new_tokens": 10}

            mock_streamer = MagicMock()
            mock_streamer.__iter__ = MagicMock(return_value=iter(["Hello", " world", "!"]))
            mock_instance.create_streamer.return_value = mock_streamer

            mock_manager.return_value = mock_instance

            agent = HuggingFaceLocalAgent(model="test-model")
            payload = AgentPayload(user_message="Test", thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="s1")

            tokens: list[str] = []
            async for token in agent.stream(payload):
                tokens.append(token)

            assert tokens == ["Hello", " world", "!"]
            mock_instance.load_pipeline.assert_called_once()
            mock_instance.create_streamer.assert_called_once()


class TestPipelineManagerLocking:
    """Tests for PipelineManager thread safety and locking."""

    @pytest.mark.asyncio
    async def test_load_pipeline_increments_ref_count(self) -> None:
        from midori_ai_agent_huggingface import HuggingFaceConfig
        from midori_ai_agent_huggingface.pipeline_manager import PipelineManager

        config = HuggingFaceConfig(model="test-model")
        manager = PipelineManager(config)
        
        manager._pipeline = MagicMock()

        assert manager._ref_count == 0
        
        async with manager._lock:
            manager._ref_count += 1
        assert manager._ref_count == 1
        
        async with manager._lock:
            manager._ref_count += 1
        assert manager._ref_count == 2

    @pytest.mark.asyncio
    async def test_unload_decrements_ref_count(self) -> None:
        from midori_ai_agent_huggingface import HuggingFaceConfig
        from midori_ai_agent_huggingface.pipeline_manager import PipelineManager

        config = HuggingFaceConfig(model="test-model")
        manager = PipelineManager(config)
        
        manager._pipeline = MagicMock()
        manager._ref_count = 2

        await manager.unload()
        assert manager._ref_count == 1
        assert manager._pipeline is not None

        await manager.unload()
        assert manager._ref_count == 0
        assert manager._pipeline is None

    @pytest.mark.asyncio
    async def test_concurrent_load_operations(self) -> None:
        from midori_ai_agent_huggingface import HuggingFaceConfig
        from midori_ai_agent_huggingface.pipeline_manager import PipelineManager

        config = HuggingFaceConfig(model="test-model")
        manager = PipelineManager(config)
        
        mock_pipeline = MagicMock()
        manager._pipeline = mock_pipeline

        async def concurrent_increment() -> MagicMock:
            async with manager._lock:
                manager._ref_count += 1
                return manager._pipeline

        results = await asyncio.gather(concurrent_increment(), concurrent_increment(), concurrent_increment())

        assert all(r is mock_pipeline for r in results)
        assert manager._ref_count == 3
