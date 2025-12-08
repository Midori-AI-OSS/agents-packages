"""Tests for the midori-ai-vector-manager package."""

import pytest
import time

from pathlib import Path

from midori_ai_vector_manager import ChromaVectorStore
from midori_ai_vector_manager import DEFAULT_PERSIST_PATH
from midori_ai_vector_manager import SenderType
from midori_ai_vector_manager import VectorEntry
from midori_ai_vector_manager import VectorStoreProtocol


class TestSenderType:
    """Tests for SenderType enum."""

    def test_values(self) -> None:
        assert SenderType.USER.value == "user"
        assert SenderType.MODEL.value == "model"
        assert SenderType.SYSTEM.value == "system"

    def test_string_enum(self) -> None:
        assert str(SenderType.USER) == "SenderType.USER"
        assert SenderType.USER == "user"


class TestVectorEntry:
    """Tests for VectorEntry model."""

    def test_basic_entry(self) -> None:
        entry = VectorEntry(id="test-id", text="Hello world", timestamp=1234567890.0)
        assert entry.id == "test-id"
        assert entry.text == "Hello world"
        assert entry.timestamp == 1234567890.0
        assert entry.sender is None
        assert entry.metadata == {}

    def test_entry_with_sender(self) -> None:
        entry = VectorEntry(id="test-id", text="Hello world", timestamp=1234567890.0, sender=SenderType.USER)
        assert entry.sender == SenderType.USER

    def test_entry_with_metadata(self) -> None:
        entry = VectorEntry(id="test-id", text="Hello world", timestamp=1234567890.0, metadata={"session_id": "user123"})
        assert entry.metadata == {"session_id": "user123"}

    def test_age_minutes_property(self) -> None:
        entry = VectorEntry(id="test-id", text="Test", timestamp=time.time() - 120)
        age = entry.age_minutes
        assert 1.9 < age < 2.1

    def test_to_chromadb_metadata(self) -> None:
        entry = VectorEntry(id="test-id", text="Hello", timestamp=1234567890.0, sender=SenderType.USER, metadata={"key": "value"})
        meta = entry.to_chromadb_metadata()
        assert meta["timestamp"] == 1234567890.0
        assert meta["sender"] == "user"
        assert meta["key"] == "value"

    def test_to_chromadb_metadata_no_sender(self) -> None:
        entry = VectorEntry(id="test-id", text="Hello", timestamp=1234567890.0, metadata={"key": "value"})
        meta = entry.to_chromadb_metadata()
        assert meta["timestamp"] == 1234567890.0
        assert "sender" not in meta
        assert meta["key"] == "value"


class TestVectorStoreProtocol:
    """Tests for VectorStoreProtocol ABC."""

    def test_protocol_is_abstract(self) -> None:
        with pytest.raises(TypeError):
            VectorStoreProtocol()

    def test_protocol_requires_all_methods(self) -> None:
        class IncompleteStore(VectorStoreProtocol):
            async def store(self, text, sender=None, metadata=None):
                return VectorEntry(id="test", text=text, timestamp=0.0)

        with pytest.raises(TypeError):
            IncompleteStore()


class TestChromaVectorStore:
    """Tests for ChromaVectorStore implementation."""

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self) -> None:
        store = ChromaVectorStore(collection_name="test_store", persist_directory=None)
        await store.clear()
        entry = await store.store(text="Test text", sender=SenderType.USER, metadata={"key": "value"})
        assert entry.text == "Test text"
        assert entry.sender == SenderType.USER
        assert entry.metadata == {"key": "value"}
        assert entry.id is not None
        await store.clear()

    @pytest.mark.asyncio
    async def test_get_by_id(self) -> None:
        store = ChromaVectorStore(collection_name="test_get_by_id", persist_directory=None)
        await store.clear()
        entry = await store.store(text="Find me", sender=SenderType.MODEL)
        retrieved = await store.get_by_id(entry.id)
        assert retrieved is not None
        assert retrieved.id == entry.id
        assert retrieved.text == "Find me"
        assert retrieved.sender == SenderType.MODEL
        await store.clear()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self) -> None:
        store = ChromaVectorStore(collection_name="test_not_found", persist_directory=None)
        await store.clear()
        result = await store.get_by_id("nonexistent-id")
        assert result is None
        await store.clear()

    @pytest.mark.asyncio
    async def test_query_by_metadata(self) -> None:
        store = ChromaVectorStore(collection_name="test_query", persist_directory=None)
        await store.clear()
        await store.store(text="Entry 1", metadata={"session_id": "user123"})
        await store.store(text="Entry 2", metadata={"session_id": "user123"})
        await store.store(text="Entry 3", metadata={"session_id": "user456"})
        results = await store.query(filters={"session_id": "user123"})
        assert len(results) == 2
        for entry in results:
            assert entry.metadata.get("session_id") == "user123"
        await store.clear()

    @pytest.mark.asyncio
    async def test_search_similar(self) -> None:
        store = ChromaVectorStore(collection_name="test_search", persist_directory=None)
        await store.clear()
        await store.store(text="The quick brown fox jumps over the lazy dog")
        await store.store(text="A fast auburn animal leaps above a sleepy canine")
        await store.store(text="Python is a programming language")
        results = await store.search_similar(query_text="fast fox jumping", limit=2)
        assert len(results) == 2
        await store.clear()

    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        store = ChromaVectorStore(collection_name="test_delete", persist_directory=None)
        await store.clear()
        entry = await store.store(text="To be deleted")
        count_before = await store.count()
        assert count_before == 1
        deleted = await store.delete([entry.id])
        assert deleted == 1
        count_after = await store.count()
        assert count_after == 0
        await store.clear()

    @pytest.mark.asyncio
    async def test_delete_empty_list(self) -> None:
        store = ChromaVectorStore(collection_name="test_delete_empty", persist_directory=None)
        await store.clear()
        deleted = await store.delete([])
        assert deleted == 0
        await store.clear()

    @pytest.mark.asyncio
    async def test_count(self) -> None:
        store = ChromaVectorStore(collection_name="test_count", persist_directory=None)
        await store.clear()
        assert await store.count() == 0
        await store.store(text="Entry 1")
        await store.store(text="Entry 2")
        assert await store.count() == 2
        await store.clear()

    @pytest.mark.asyncio
    async def test_clear(self) -> None:
        store = ChromaVectorStore(collection_name="test_clear", persist_directory=None)
        await store.clear()
        await store.store(text="Entry 1")
        await store.store(text="Entry 2")
        assert await store.count() == 2
        await store.clear()
        assert await store.count() == 0

    @pytest.mark.asyncio
    async def test_sender_types(self) -> None:
        store = ChromaVectorStore(collection_name="test_sender", persist_directory=None)
        await store.clear()
        await store.store(text="User message", sender=SenderType.USER)
        await store.store(text="Model response", sender=SenderType.MODEL)
        await store.store(text="System message", sender=SenderType.SYSTEM)
        all_entries = await store.query(filters={}, limit=100)
        assert len(all_entries) == 3
        senders = {e.sender for e in all_entries}
        assert senders == {SenderType.USER, SenderType.MODEL, SenderType.SYSTEM}
        await store.clear()

    @pytest.mark.asyncio
    async def test_entries_sorted_by_timestamp(self) -> None:
        store = ChromaVectorStore(collection_name="test_sorted", persist_directory=None)
        await store.clear()
        await store.store(text="First")
        await store.store(text="Second")
        await store.store(text="Third")
        results = await store.query(filters={}, limit=100)
        assert len(results) == 3
        timestamps = [e.timestamp for e in results]
        assert timestamps == sorted(timestamps)
        await store.clear()

    @pytest.mark.asyncio
    async def test_disable_time_gating(self) -> None:
        store = ChromaVectorStore(collection_name="test_long_term", persist_directory=None, disable_time_gating=True)
        await store.clear()
        entry = await store.store(text="Long term knowledge", sender=SenderType.SYSTEM, metadata={"type": "permanent"})
        assert entry.timestamp == 0.0
        assert "-" not in entry.id
        assert len(entry.id) == 32
        retrieved = await store.get_by_id(entry.id)
        assert retrieved is not None
        assert retrieved.timestamp == 0.0
        assert retrieved.text == "Long term knowledge"
        await store.clear()

    @pytest.mark.asyncio
    async def test_time_gating_default_behavior(self) -> None:
        store = ChromaVectorStore(collection_name="test_default", persist_directory=None)
        await store.clear()
        entry = await store.store(text="Short term memory")
        assert entry.timestamp > 0.0
        assert "-" in entry.id
        await store.clear()

    @pytest.mark.asyncio
    async def test_disable_time_gating_multiple_entries(self) -> None:
        store = ChromaVectorStore(collection_name="test_multiple_long_term", persist_directory=None, disable_time_gating=True)
        await store.clear()
        entry1 = await store.store(text="Knowledge 1", metadata={"category": "science"})
        entry2 = await store.store(text="Knowledge 2", metadata={"category": "history"})
        entry3 = await store.store(text="Knowledge 3", metadata={"category": "science"})
        assert entry1.timestamp == 0.0
        assert entry2.timestamp == 0.0
        assert entry3.timestamp == 0.0
        all_entries = await store.query(filters={}, limit=100)
        assert len(all_entries) == 3
        science_entries = await store.query(filters={"category": "science"}, limit=100)
        assert len(science_entries) == 2
        await store.clear()


class TestDefaultPersistPath:
    """Tests for default persistence path configuration."""

    def test_default_path_structure(self) -> None:
        expected = Path.home() / ".midoriai" / "vectorstore"
        assert DEFAULT_PERSIST_PATH == expected
