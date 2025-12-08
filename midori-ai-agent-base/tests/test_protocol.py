"""Tests for the midori-ai-agent-base package."""

import pytest

from midori_ai_agent_base import AgentPayload
from midori_ai_agent_base import AgentResponse
from midori_ai_agent_base import MemoryEntryData
from midori_ai_agent_base import ReasoningEffort
from midori_ai_agent_base import MidoriAiAgentProtocol


class TestReasoningEffort:
    """Tests for ReasoningEffort dataclass."""

    def test_default_values(self) -> None:
        reasoning = ReasoningEffort()
        assert reasoning.effort == "low"
        assert reasoning.generate_summary == "auto"
        assert reasoning.summary == "auto"

    def test_custom_effort_level(self) -> None:
        reasoning = ReasoningEffort(effort="high")
        assert reasoning.effort == "high"
        assert reasoning.generate_summary == "auto"
        assert reasoning.summary == "auto"

    def test_all_effort_levels(self) -> None:
        for level in ["none", "minimal", "low", "medium", "high"]:
            reasoning = ReasoningEffort(effort=level)
            assert reasoning.effort == level

    def test_custom_summary_types(self) -> None:
        reasoning = ReasoningEffort(effort="medium", generate_summary="detailed", summary="concise")
        assert reasoning.effort == "medium"
        assert reasoning.generate_summary == "detailed"
        assert reasoning.summary == "concise"


class TestMemoryEntryData:
    """Tests for MemoryEntryData dataclass."""

    def test_basic_entry(self) -> None:
        entry = MemoryEntryData(role="user", content="Hello")
        assert entry.role == "user"
        assert entry.content == "Hello"
        assert entry.timestamp is None
        assert entry.tool_calls is None
        assert entry.metadata is None

    def test_entry_with_all_fields(self) -> None:
        entry = MemoryEntryData(role="assistant", content="Response", timestamp=1234567890.0, tool_calls=[{"name": "search", "args": {"q": "test"}}], metadata={"source": "test"})
        assert entry.role == "assistant"
        assert entry.content == "Response"
        assert entry.timestamp == 1234567890.0
        assert entry.tool_calls is not None
        assert len(entry.tool_calls) == 1
        assert entry.metadata == {"source": "test"}


class TestAgentPayload:
    """Tests for AgentPayload dataclass."""

    def test_basic_payload(self) -> None:
        payload = AgentPayload(
            user_message="Hello",
            thinking_blob="Thinking...",
            system_context="You are an AI",
            user_profile={"name": "Test"},
            tools_available=["search", "calculate"],
            session_id="session-123",
        )
        assert payload.user_message == "Hello"
        assert payload.thinking_blob == "Thinking..."
        assert payload.system_context == "You are an AI"
        assert payload.user_profile == {"name": "Test"}
        assert payload.tools_available == ["search", "calculate"]
        assert payload.session_id == "session-123"
        assert payload.metadata is None
        assert payload.reasoning_effort is None
        assert payload.memory is None

    def test_payload_with_metadata(self) -> None:
        metadata = {"source": "discord", "timestamp": 12345}
        payload = AgentPayload(
            user_message="Hello",
            thinking_blob="",
            system_context="",
            user_profile={},
            tools_available=[],
            session_id="session-456",
            metadata=metadata,
        )
        assert payload.metadata == metadata

    def test_payload_with_reasoning_effort(self) -> None:
        reasoning = ReasoningEffort(effort="high", generate_summary="detailed", summary="detailed")
        payload = AgentPayload(
            user_message="Complex task",
            thinking_blob="",
            system_context="You are an AI",
            user_profile={},
            tools_available=[],
            session_id="session-789",
            reasoning_effort=reasoning,
        )
        assert payload.reasoning_effort is not None
        assert payload.reasoning_effort.effort == "high"
        assert payload.reasoning_effort.generate_summary == "detailed"
        assert payload.reasoning_effort.summary == "detailed"

    def test_payload_with_memory(self) -> None:
        memory = [MemoryEntryData(role="user", content="First message"), MemoryEntryData(role="assistant", content="First response")]
        payload = AgentPayload(
            user_message="Second message",
            thinking_blob="",
            system_context="",
            user_profile={},
            tools_available=[],
            session_id="session-mem",
            memory=memory,
        )
        assert payload.memory is not None
        assert len(payload.memory) == 2
        assert payload.memory[0].role == "user"
        assert payload.memory[1].content == "First response"


class TestAgentResponse:
    """Tests for AgentResponse dataclass."""

    def test_basic_response(self) -> None:
        response = AgentResponse(thinking="I am thinking", response="Hello!")
        assert response.thinking == "I am thinking"
        assert response.response == "Hello!"
        assert response.code is None
        assert response.tool_calls is None
        assert response.metadata is None

    def test_response_with_code(self) -> None:
        response = AgentResponse(thinking="Writing code", response="Here is code", code="print('hello')")
        assert response.code == "print('hello')"

    def test_response_with_tool_calls(self) -> None:
        tool_calls = [{"name": "search", "args": {"query": "weather"}}]
        response = AgentResponse(thinking="Using tools", response="Result", tool_calls=tool_calls)
        assert response.tool_calls == tool_calls

    def test_response_with_metadata(self) -> None:
        metadata = {"tokens_used": 100}
        response = AgentResponse(thinking="", response="", metadata=metadata)
        assert response.metadata == metadata


class TestMidoriAiAgentProtocol:
    """Tests for MidoriAiAgentProtocol ABC."""

    def test_protocol_is_abstract(self) -> None:
        with pytest.raises(TypeError):
            MidoriAiAgentProtocol()

    def test_protocol_requires_all_methods(self) -> None:
        class IncompleteAgent(MidoriAiAgentProtocol):
            async def invoke(self, payload: AgentPayload) -> AgentResponse:
                return AgentResponse(thinking="", response="")

        with pytest.raises(TypeError):
            IncompleteAgent()

    def test_complete_implementation(self) -> None:
        class CompleteAgent(MidoriAiAgentProtocol):
            async def invoke(self, payload: AgentPayload) -> AgentResponse:
                return AgentResponse(thinking="thinking", response="response")

            async def invoke_with_tools(self, payload: AgentPayload, tools: list) -> AgentResponse:
                return AgentResponse(thinking="thinking", response="response")

            async def get_context_window(self) -> int:
                return 128000

            async def supports_streaming(self) -> bool:
                return True

        agent = CompleteAgent()
        assert agent is not None


@pytest.mark.asyncio
class TestMidoriAiAgentProtocolAsync:
    """Async tests for MidoriAiAgentProtocol implementations."""

    async def test_invoke_returns_response(self) -> None:
        class TestAgent(MidoriAiAgentProtocol):
            async def invoke(self, payload: AgentPayload) -> AgentResponse:
                return AgentResponse(thinking=f"Processing: {payload.user_message}", response=f"Echo: {payload.user_message}")

            async def invoke_with_tools(self, payload: AgentPayload, tools: list) -> AgentResponse:
                return AgentResponse(thinking="", response="")

            async def get_context_window(self) -> int:
                return 128000

            async def supports_streaming(self) -> bool:
                return True

        agent = TestAgent()
        payload = AgentPayload(user_message="test", thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="s1")
        response = await agent.invoke(payload)
        assert response.thinking == "Processing: test"
        assert response.response == "Echo: test"

    async def test_get_context_window(self) -> None:
        class TestAgent(MidoriAiAgentProtocol):
            async def invoke(self, payload: AgentPayload) -> AgentResponse:
                return AgentResponse(thinking="", response="")

            async def invoke_with_tools(self, payload: AgentPayload, tools: list) -> AgentResponse:
                return AgentResponse(thinking="", response="")

            async def get_context_window(self) -> int:
                return 200000

            async def supports_streaming(self) -> bool:
                return False

        agent = TestAgent()
        context_window = await agent.get_context_window()
        assert context_window == 200000

    async def test_supports_streaming(self) -> None:
        class StreamingAgent(MidoriAiAgentProtocol):
            async def invoke(self, payload: AgentPayload) -> AgentResponse:
                return AgentResponse(thinking="", response="")

            async def invoke_with_tools(self, payload: AgentPayload, tools: list) -> AgentResponse:
                return AgentResponse(thinking="", response="")

            async def get_context_window(self) -> int:
                return 128000

            async def supports_streaming(self) -> bool:
                return True

        agent = StreamingAgent()
        can_stream = await agent.supports_streaming()
        assert can_stream is True
