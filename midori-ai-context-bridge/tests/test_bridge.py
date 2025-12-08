"""Tests for the context bridge package."""

import pytest
import time


from midori_ai_context_bridge import BridgeConfig
from midori_ai_context_bridge import ChromaStorage
from midori_ai_context_bridge import ContextBridge
from midori_ai_context_bridge import ContextCompressor
from midori_ai_context_bridge import DecayConfig
from midori_ai_context_bridge import MemoryCorruptor
from midori_ai_context_bridge import ModelType
from midori_ai_context_bridge import ReasoningEntry


class TestDecayConfig:
    """Tests for DecayConfig dataclass."""

    def test_default_values(self) -> None:
        config = DecayConfig(decay_minutes=30)
        assert config.decay_minutes == 30
        assert config.removal_multiplier == 3.0
        assert config.corruption_intensity == 0.3

    def test_removal_minutes_property(self) -> None:
        config = DecayConfig(decay_minutes=30, removal_multiplier=3.0)
        assert config.removal_minutes == 90.0

    def test_custom_values(self) -> None:
        config = DecayConfig(decay_minutes=60, removal_multiplier=2.0, corruption_intensity=0.5)
        assert config.decay_minutes == 60
        assert config.removal_multiplier == 2.0
        assert config.corruption_intensity == 0.5
        assert config.removal_minutes == 120.0


class TestBridgeConfig:
    """Tests for BridgeConfig dataclass."""

    def test_default_values(self) -> None:
        config = BridgeConfig()
        assert config.max_tokens_per_summary == 500
        assert config.chroma_collection_name == "context_bridge"
        assert config.preprocessing_decay is not None
        assert config.working_awareness_decay is not None

    def test_default_decay_configs(self) -> None:
        config = BridgeConfig()
        assert config.preprocessing_decay.decay_minutes == 30
        assert config.working_awareness_decay.decay_minutes == 720

    def test_get_decay_config(self) -> None:
        config = BridgeConfig()
        preprocessing_config = config.get_decay_config(ModelType.PREPROCESSING)
        working_config = config.get_decay_config(ModelType.WORKING_AWARENESS)
        assert preprocessing_config.decay_minutes == 30
        assert working_config.decay_minutes == 720


class TestMemoryCorruptor:
    """Tests for MemoryCorruptor class."""

    def test_calculate_severity_fresh_data(self) -> None:
        config = DecayConfig(decay_minutes=30)
        corruptor = MemoryCorruptor(config)
        assert corruptor.calculate_severity(0) == 0.0
        assert corruptor.calculate_severity(15) == 0.0
        assert corruptor.calculate_severity(29) == 0.0

    def test_calculate_severity_at_decay_threshold(self) -> None:
        config = DecayConfig(decay_minutes=30)
        corruptor = MemoryCorruptor(config)
        assert corruptor.calculate_severity(30) == 0.0

    def test_calculate_severity_aging_data(self) -> None:
        config = DecayConfig(decay_minutes=30, removal_multiplier=3.0)
        corruptor = MemoryCorruptor(config)
        severity_60 = corruptor.calculate_severity(60)
        assert 0.4 < severity_60 < 0.6
        severity_75 = corruptor.calculate_severity(75)
        assert 0.7 < severity_75 < 0.8

    def test_calculate_severity_max(self) -> None:
        config = DecayConfig(decay_minutes=30, removal_multiplier=3.0)
        corruptor = MemoryCorruptor(config)
        assert corruptor.calculate_severity(90) == 1.0
        assert corruptor.calculate_severity(100) == 1.0

    def test_corrupt_text_no_corruption_for_fresh(self) -> None:
        config = DecayConfig(decay_minutes=30)
        corruptor = MemoryCorruptor(config, seed=42)
        text = "Hello world"
        result = corruptor.corrupt_text(text, 0)
        assert result == text
        result = corruptor.corrupt_text(text, 29)
        assert result == text

    def test_corrupt_text_some_corruption_for_aging(self) -> None:
        config = DecayConfig(decay_minutes=30, corruption_intensity=0.3)
        corruptor = MemoryCorruptor(config, seed=42)
        text = "Hello world this is a test"
        result = corruptor.corrupt_text(text, 60)
        assert result != text
        assert len(result) <= len(text) + 5

    def test_corrupt_text_reproducible_with_seed(self) -> None:
        config = DecayConfig(decay_minutes=30)
        corruptor1 = MemoryCorruptor(config, seed=42)
        corruptor2 = MemoryCorruptor(config, seed=42)
        text = "Hello world"
        result1 = corruptor1.corrupt_text(text, 60)
        result2 = corruptor2.corrupt_text(text, 60)
        assert result1 == result2

    def test_should_remove(self) -> None:
        config = DecayConfig(decay_minutes=30, removal_multiplier=3.0)
        corruptor = MemoryCorruptor(config)
        assert not corruptor.should_remove(0)
        assert not corruptor.should_remove(30)
        assert not corruptor.should_remove(89)
        assert corruptor.should_remove(90)
        assert corruptor.should_remove(100)

    def test_process_text_fresh(self) -> None:
        config = DecayConfig(decay_minutes=30)
        corruptor = MemoryCorruptor(config)
        text, should_remove = corruptor.process_text("Hello", 0)
        assert text == "Hello"
        assert not should_remove

    def test_process_text_removal(self) -> None:
        config = DecayConfig(decay_minutes=30, removal_multiplier=3.0)
        corruptor = MemoryCorruptor(config)
        text, should_remove = corruptor.process_text("Hello", 100)
        assert text is None
        assert should_remove


class TestContextCompressor:
    """Tests for ContextCompressor class."""

    @pytest.mark.asyncio
    async def test_compress_empty(self) -> None:
        compressor = ContextCompressor(max_tokens=500)
        result = await compressor.compress([])
        assert result == ""

    @pytest.mark.asyncio
    async def test_compress_single(self) -> None:
        compressor = ContextCompressor(max_tokens=500)
        result = await compressor.compress(["Hello world"])
        assert result == "Hello world"

    @pytest.mark.asyncio
    async def test_compress_multiple(self) -> None:
        compressor = ContextCompressor(max_tokens=500)
        result = await compressor.compress(["First", "Second", "Third"])
        assert "First" in result
        assert "Second" in result
        assert "Third" in result

    @pytest.mark.asyncio
    async def test_compress_truncation(self) -> None:
        compressor = ContextCompressor(max_tokens=10)
        long_text = "a" * 1000
        result = await compressor.compress([long_text])
        assert len(result) < len(long_text)
        assert result.endswith("...")

    @pytest.mark.asyncio
    async def test_compress_with_labels(self) -> None:
        compressor = ContextCompressor(max_tokens=500)
        labeled = [("Label1", "Text1"), ("Label2", "Text2")]
        result = await compressor.compress_with_labels(labeled)
        assert "[Label1]" in result
        assert "Text1" in result
        assert "[Label2]" in result
        assert "Text2" in result

    def test_estimate_tokens(self) -> None:
        compressor = ContextCompressor()
        assert compressor.estimate_tokens("test") == 1
        assert compressor.estimate_tokens("a" * 40) == 10


class TestChromaStorage:
    """Tests for ChromaStorage class."""

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self) -> None:
        storage = ChromaStorage(collection_name="test_storage")
        await storage.clear()
        entry = await storage.store(session_id="test:123", text="Test reasoning", model_type=ModelType.PREPROCESSING)
        assert entry.session_id == "test:123"
        assert entry.text == "Test reasoning"
        assert entry.model_type == ModelType.PREPROCESSING
        entries = await storage.get_entries_for_session("test:123")
        assert len(entries) == 1
        assert entries[0].text == "Test reasoning"
        await storage.clear()

    @pytest.mark.asyncio
    async def test_filter_by_model_type(self) -> None:
        storage = ChromaStorage(collection_name="test_filter")
        await storage.clear()
        await storage.store("test:123", "Preprocessing text", ModelType.PREPROCESSING)
        await storage.store("test:123", "Working text", ModelType.WORKING_AWARENESS)
        preprocessing = await storage.get_entries_for_session("test:123", ModelType.PREPROCESSING)
        working = await storage.get_entries_for_session("test:123", ModelType.WORKING_AWARENESS)
        assert len(preprocessing) == 1
        assert preprocessing[0].text == "Preprocessing text"
        assert len(working) == 1
        assert working[0].text == "Working text"
        await storage.clear()

    @pytest.mark.asyncio
    async def test_delete_entries(self) -> None:
        storage = ChromaStorage(collection_name="test_delete")
        await storage.clear()
        entry = await storage.store("test:123", "To delete", ModelType.PREPROCESSING)
        count_before = await storage.count()
        assert count_before == 1
        deleted = await storage.delete_entries([entry.id])
        assert deleted == 1
        count_after = await storage.count()
        assert count_after == 0
        await storage.clear()

    @pytest.mark.asyncio
    async def test_count(self) -> None:
        storage = ChromaStorage(collection_name="test_count")
        await storage.clear()
        assert await storage.count() == 0
        await storage.store("test:123", "Entry 1", ModelType.PREPROCESSING)
        await storage.store("test:123", "Entry 2", ModelType.PREPROCESSING)
        assert await storage.count() == 2
        await storage.clear()

    @pytest.mark.asyncio
    async def test_get_all_entries(self) -> None:
        storage = ChromaStorage(collection_name="test_all")
        await storage.clear()
        await storage.store("session1", "Entry 1", ModelType.PREPROCESSING)
        await storage.store("session2", "Entry 2", ModelType.WORKING_AWARENESS)
        entries = await storage.get_all_entries()
        assert len(entries) == 2
        await storage.clear()


class TestContextBridge:
    """Tests for ContextBridge class."""

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self) -> None:
        bridge = ContextBridge(max_tokens_per_summary=500)
        await bridge.storage.clear()
        await bridge.store_reasoning(session_id="user:456", text="Test reasoning output", model_type=ModelType.PREPROCESSING)
        context = await bridge.get_prior_reasoning(session_id="user:456", model_type=ModelType.PREPROCESSING)
        assert "Test reasoning output" in context
        await bridge.storage.clear()

    @pytest.mark.asyncio
    async def test_separate_model_types(self) -> None:
        bridge = ContextBridge(max_tokens_per_summary=500)
        await bridge.storage.clear()
        await bridge.store_reasoning("user:789", "Preprocessing data", ModelType.PREPROCESSING)
        await bridge.store_reasoning("user:789", "Working data", ModelType.WORKING_AWARENESS)
        preprocessing = await bridge.get_prior_reasoning("user:789", ModelType.PREPROCESSING)
        working = await bridge.get_prior_reasoning("user:789", ModelType.WORKING_AWARENESS)
        assert "Preprocessing data" in preprocessing
        assert "Working data" not in preprocessing
        assert "Working data" in working
        assert "Preprocessing data" not in working
        await bridge.storage.clear()

    @pytest.mark.asyncio
    async def test_get_session_stats(self) -> None:
        bridge = ContextBridge(max_tokens_per_summary=500)
        await bridge.storage.clear()
        await bridge.store_reasoning("user:stats", "Entry 1", ModelType.PREPROCESSING)
        await bridge.store_reasoning("user:stats", "Entry 2", ModelType.PREPROCESSING)
        await bridge.store_reasoning("user:stats", "Entry 3", ModelType.WORKING_AWARENESS)
        stats = await bridge.get_session_stats("user:stats")
        assert stats["session_id"] == "user:stats"
        assert stats["preprocessing_count"] == 2
        assert stats["working_awareness_count"] == 1
        assert stats["total_count"] == 3
        await bridge.storage.clear()

    @pytest.mark.asyncio
    async def test_clear_session(self) -> None:
        bridge = ContextBridge(max_tokens_per_summary=500)
        await bridge.storage.clear()
        await bridge.store_reasoning("user:clear", "Entry", ModelType.PREPROCESSING)
        await bridge.store_reasoning("user:keep", "Keep", ModelType.PREPROCESSING)
        removed = await bridge.clear_session("user:clear")
        assert removed == 1
        remaining = await bridge.count()
        assert remaining == 1
        await bridge.storage.clear()

    @pytest.mark.asyncio
    async def test_count(self) -> None:
        bridge = ContextBridge(max_tokens_per_summary=500)
        await bridge.storage.clear()
        assert await bridge.count() == 0
        await bridge.store_reasoning("user:count", "Entry", ModelType.PREPROCESSING)
        assert await bridge.count() == 1
        await bridge.storage.clear()

    @pytest.mark.asyncio
    async def test_custom_config(self) -> None:
        custom_config = BridgeConfig(max_tokens_per_summary=1000, preprocessing_decay=DecayConfig(decay_minutes=15), working_awareness_decay=DecayConfig(decay_minutes=120))
        bridge = ContextBridge(config=custom_config)
        assert bridge.config.max_tokens_per_summary == 1000
        assert bridge.config.preprocessing_decay.decay_minutes == 15
        assert bridge.config.working_awareness_decay.decay_minutes == 120
        await bridge.storage.clear()


class TestReasoningEntry:
    """Tests for ReasoningEntry dataclass."""

    def test_age_minutes_property(self) -> None:
        from midori_ai_vector_manager import VectorEntry

        reasoning_entry = ReasoningEntry(model_type=ModelType.PREPROCESSING)
        vector_entry = VectorEntry(id="test-id", text="Test", timestamp=time.time() - 120, sender=None, metadata={"session_id": "user:123"})
        reasoning_entry.add_entry(vector_entry)
        age = reasoning_entry.age_minutes
        assert 1.9 < age < 2.1
