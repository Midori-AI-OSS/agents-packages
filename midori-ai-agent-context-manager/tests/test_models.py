"""Tests for memory entry models."""

from midori_ai_agent_context_manager import MemoryEntry
from midori_ai_agent_context_manager import MemorySnapshot
from midori_ai_agent_context_manager import MessageRole
from midori_ai_agent_context_manager import ToolCallEntry


class TestMessageRole:
    """Tests for MessageRole enum."""

    def test_user_role(self) -> None:
        assert MessageRole.USER == "user"
        assert MessageRole.USER.value == "user"

    def test_assistant_role(self) -> None:
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.ASSISTANT.value == "assistant"

    def test_system_role(self) -> None:
        assert MessageRole.SYSTEM == "system"
        assert MessageRole.SYSTEM.value == "system"

    def test_tool_role(self) -> None:
        assert MessageRole.TOOL == "tool"
        assert MessageRole.TOOL.value == "tool"


class TestToolCallEntry:
    """Tests for ToolCallEntry model."""

    def test_basic_tool_call(self) -> None:
        tool_call = ToolCallEntry(name="search", args={"query": "weather"})
        assert tool_call.name == "search"
        assert tool_call.args == {"query": "weather"}
        assert tool_call.result is None
        assert tool_call.call_id is None

    def test_tool_call_with_result(self) -> None:
        tool_call = ToolCallEntry(name="calculate", args={"expr": "2+2"}, result="4", call_id="call-123")
        assert tool_call.name == "calculate"
        assert tool_call.args == {"expr": "2+2"}
        assert tool_call.result == "4"
        assert tool_call.call_id == "call-123"

    def test_tool_call_default_args(self) -> None:
        tool_call = ToolCallEntry(name="get_time")
        assert tool_call.args == {}


class TestMemoryEntry:
    """Tests for MemoryEntry model."""

    def test_user_message(self) -> None:
        entry = MemoryEntry(role=MessageRole.USER, content="Hello")
        assert entry.role == "user"
        assert entry.content == "Hello"
        assert entry.timestamp > 0
        assert entry.tool_calls is None
        assert entry.metadata is None

    def test_assistant_message_with_tool_calls(self) -> None:
        tool_call = ToolCallEntry(name="search", args={"q": "test"})
        entry = MemoryEntry(role=MessageRole.ASSISTANT, content="I found:", tool_calls=[tool_call])
        assert entry.role == "assistant"
        assert entry.content == "I found:"
        assert len(entry.tool_calls) == 1
        assert entry.tool_calls[0].name == "search"

    def test_entry_with_metadata(self) -> None:
        entry = MemoryEntry(role=MessageRole.SYSTEM, content="System prompt", metadata={"source": "config"})
        assert entry.metadata == {"source": "config"}

    def test_entry_custom_timestamp(self) -> None:
        custom_time = 1000000.0
        entry = MemoryEntry(role=MessageRole.USER, content="Test", timestamp=custom_time)
        assert entry.timestamp == custom_time

    def test_entry_serialization(self) -> None:
        entry = MemoryEntry(role=MessageRole.USER, content="Hello")
        json_str = entry.model_dump_json()
        restored = MemoryEntry.model_validate_json(json_str)
        assert restored.role == entry.role
        assert restored.content == entry.content


class TestMemorySnapshot:
    """Tests for MemorySnapshot model."""

    def test_empty_snapshot(self) -> None:
        snapshot = MemorySnapshot(agent_id="test-agent")
        assert snapshot.agent_id == "test-agent"
        assert snapshot.entries == []
        assert snapshot.summary is None
        assert snapshot.created_at > 0
        assert snapshot.updated_at > 0
        assert snapshot.metadata is None
        assert snapshot.version == "1.0.0"

    def test_snapshot_with_entries(self) -> None:
        entries = [MemoryEntry(role=MessageRole.USER, content="Hi"), MemoryEntry(role=MessageRole.ASSISTANT, content="Hello!")]
        snapshot = MemorySnapshot(agent_id="test-agent", entries=entries)
        assert len(snapshot.entries) == 2
        assert snapshot.entries[0].content == "Hi"
        assert snapshot.entries[1].content == "Hello!"

    def test_snapshot_with_summary(self) -> None:
        snapshot = MemorySnapshot(agent_id="test-agent", summary="User discussed weather")
        assert snapshot.summary == "User discussed weather"

    def test_snapshot_serialization_roundtrip(self) -> None:
        entries = [MemoryEntry(role=MessageRole.USER, content="Test message", metadata={"key": "value"})]
        snapshot = MemorySnapshot(agent_id="test-agent", entries=entries, summary="Test summary", metadata={"version": "2.0"})
        json_str = snapshot.model_dump_json()
        restored = MemorySnapshot.model_validate_json(json_str)
        assert restored.agent_id == snapshot.agent_id
        assert len(restored.entries) == 1
        assert restored.entries[0].content == "Test message"
        assert restored.summary == "Test summary"
        assert restored.metadata == {"version": "2.0"}
