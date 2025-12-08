"""Tests for memory store."""

import os
import tempfile

import pytest

from midori_ai_agent_context_manager import MemoryEntry
from midori_ai_agent_context_manager import MemorySnapshot
from midori_ai_agent_context_manager import MemoryStore
from midori_ai_agent_context_manager import MessageRole
from midori_ai_agent_context_manager import ToolCallEntry


class TestMemoryStoreInit:
    """Tests for MemoryStore initialization."""

    def test_init_with_agent_id(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        assert store.agent_id == "test-agent"
        assert len(store) == 0
        assert store.summary is None

    def test_init_with_max_entries(self) -> None:
        store = MemoryStore(agent_id="test-agent", max_entries=10)
        assert store._max_entries == 10


class TestMemoryStoreAddMessages:
    """Tests for adding messages to MemoryStore."""

    def test_add_user_message(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        entry = store.add_user_message("Hello!")
        assert len(store) == 1
        assert entry.role == "user"
        assert entry.content == "Hello!"

    def test_add_assistant_message(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        entry = store.add_assistant_message("Hi there!")
        assert len(store) == 1
        assert entry.role == "assistant"
        assert entry.content == "Hi there!"

    def test_add_assistant_message_with_tool_calls(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        tool_calls = [ToolCallEntry(name="search", args={"q": "test"}, result="found")]
        entry = store.add_assistant_message("Result:", tool_calls=tool_calls)
        assert entry.tool_calls is not None
        assert len(entry.tool_calls) == 1
        assert entry.tool_calls[0].name == "search"

    def test_add_system_message(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        entry = store.add_system_message("You are a helpful assistant")
        assert entry.role == "system"
        assert entry.content == "You are a helpful assistant"

    def test_add_tool_result(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        entry = store.add_tool_result("search", "Found 10 results", call_id="call-123")
        assert entry.role == "tool"
        assert entry.content == "Found 10 results"
        assert entry.tool_calls[0].name == "search"
        assert entry.tool_calls[0].call_id == "call-123"

    def test_add_entry_directly(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        entry = MemoryEntry(role=MessageRole.USER, content="Direct entry")
        store.add_entry(entry)
        assert len(store) == 1
        assert store.entries[0].content == "Direct entry"

    def test_add_message_with_metadata(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        entry = store.add_user_message("Test", metadata={"source": "discord"})
        assert entry.metadata == {"source": "discord"}


class TestMemoryStoreTrimming:
    """Tests for entry trimming behavior."""

    def test_trim_when_exceeds_max(self) -> None:
        store = MemoryStore(agent_id="test-agent", max_entries=3)
        store.add_user_message("Message 1")
        store.add_user_message("Message 2")
        store.add_user_message("Message 3")
        store.add_user_message("Message 4")
        assert len(store) == 3
        entries = store.entries
        assert entries[0].content == "Message 2"
        assert entries[2].content == "Message 4"

    def test_no_trim_without_max(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        for i in range(100):
            store.add_user_message(f"Message {i}")
        assert len(store) == 100


class TestMemoryStoreQueries:
    """Tests for querying entries."""

    def test_get_recent_entries(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        store.add_user_message("First")
        store.add_user_message("Second")
        store.add_user_message("Third")
        recent = store.get_recent_entries(2)
        assert len(recent) == 2
        assert recent[0].content == "Second"
        assert recent[1].content == "Third"

    def test_get_recent_entries_more_than_available(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        store.add_user_message("Only one")
        recent = store.get_recent_entries(10)
        assert len(recent) == 1

    def test_get_recent_entries_zero(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        store.add_user_message("Test")
        recent = store.get_recent_entries(0)
        assert len(recent) == 0

    def test_get_entries_since(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        entry1 = store.add_user_message("Old")
        timestamp = entry1.timestamp + 0.001
        entry2 = MemoryEntry(role=MessageRole.USER, content="New", timestamp=timestamp + 1)
        store.add_entry(entry2)
        filtered = store.get_entries_since(timestamp)
        assert len(filtered) == 1
        assert filtered[0].content == "New"


class TestMemoryStoreClear:
    """Tests for clearing memory."""

    def test_clear_removes_all_entries(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        store.add_user_message("Message 1")
        store.add_user_message("Message 2")
        store.summary = "Test summary"
        store.clear()
        assert len(store) == 0
        assert store.summary is None


class TestMemoryStoreMetadata:
    """Tests for metadata management."""

    def test_set_metadata(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        store.set_metadata("key", "value")
        assert store.metadata == {"key": "value"}

    def test_set_multiple_metadata(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        store.set_metadata("key1", "value1")
        store.set_metadata("key2", {"nested": True})
        assert store.metadata["key1"] == "value1"
        assert store.metadata["key2"] == {"nested": True}

    def test_metadata_is_copy(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        store.set_metadata("key", "value")
        meta = store.metadata
        meta["new_key"] = "new_value"
        assert "new_key" not in store.metadata


class TestMemoryStoreSummary:
    """Tests for summary management."""

    def test_set_summary(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        store.summary = "Conversation about weather"
        assert store.summary == "Conversation about weather"


class TestMemoryStoreSnapshot:
    """Tests for snapshot functionality."""

    def test_to_snapshot(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        store.add_user_message("Hello")
        store.add_assistant_message("Hi!")
        store.summary = "Greeting exchange"
        store.set_metadata("context", "test")
        snapshot = store.to_snapshot()
        assert snapshot.agent_id == "test-agent"
        assert len(snapshot.entries) == 2
        assert snapshot.summary == "Greeting exchange"
        assert snapshot.metadata == {"context": "test"}

    def test_from_snapshot(self) -> None:
        entries = [MemoryEntry(role=MessageRole.USER, content="Test")]
        snapshot = MemorySnapshot(agent_id="restored-agent", entries=entries, summary="Restored", metadata={"restored": True}, created_at=1000.0, updated_at=2000.0)
        store = MemoryStore(agent_id="temp")
        store.from_snapshot(snapshot)
        assert store.agent_id == "restored-agent"
        assert len(store) == 1
        assert store.summary == "Restored"
        assert store.metadata == {"restored": True}


class TestMemoryStoreIteration:
    """Tests for iteration support."""

    def test_len(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        assert len(store) == 0
        store.add_user_message("Test")
        assert len(store) == 1

    def test_iter(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        store.add_user_message("First")
        store.add_user_message("Second")
        contents = [entry.content for entry in store]
        assert contents == ["First", "Second"]


@pytest.mark.asyncio
class TestMemoryStorePersistence:
    """Async tests for file persistence."""

    async def test_save_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "memory.json")
            store1 = MemoryStore(agent_id="test-agent")
            store1.add_user_message("Hello")
            store1.add_assistant_message("Hi there!")
            store1.summary = "Greeting"
            await store1.save(file_path)
            store2 = MemoryStore(agent_id="different")
            loaded = await store2.load(file_path)
            assert loaded is True
            assert store2.agent_id == "test-agent"
            assert len(store2) == 2
            assert store2.summary == "Greeting"

    async def test_load_nonexistent_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "nonexistent.json")
            store = MemoryStore(agent_id="test-agent")
            loaded = await store.load(file_path)
            assert loaded is False
            assert len(store) == 0

    async def test_save_creates_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "nested", "dir", "memory.json")
            store = MemoryStore(agent_id="test-agent")
            store.add_user_message("Test")
            await store.save(file_path)
            assert os.path.exists(file_path)

    async def test_save_remembers_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "memory.json")
            store = MemoryStore(agent_id="test-agent")
            store.add_user_message("First")
            await store.save(file_path)
            store.add_user_message("Second")
            await store.save()
            store2 = MemoryStore(agent_id="temp")
            await store2.load(file_path)
            assert len(store2) == 2

    async def test_save_without_path_raises(self) -> None:
        store = MemoryStore(agent_id="test-agent")
        with pytest.raises(ValueError, match="No file path specified"):
            await store.save()

    async def test_load_sets_path_for_save(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "memory.json")
            store1 = MemoryStore(agent_id="test-agent")
            store1.add_user_message("Original")
            await store1.save(file_path)
            store2 = MemoryStore(agent_id="temp")
            await store2.load(file_path)
            store2.add_user_message("Updated")
            await store2.save()
            store3 = MemoryStore(agent_id="temp")
            await store3.load(file_path)
            assert len(store3) == 2
