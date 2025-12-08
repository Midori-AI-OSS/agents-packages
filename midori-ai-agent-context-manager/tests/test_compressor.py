"""Tests for memory compression functionality."""

import pytest

from midori_ai_agent_context_manager import CompressionConfig
from midori_ai_agent_context_manager import KNOWN_MODEL_CONTEXT_WINDOWS
from midori_ai_agent_context_manager import MemoryCompressor
from midori_ai_agent_context_manager import MemoryEntry
from midori_ai_agent_context_manager import MessageRole


class TestKnownModelContextWindows:
    """Tests for known model context windows."""

    def test_gpt_oss_models_have_131k(self) -> None:
        assert KNOWN_MODEL_CONTEXT_WINDOWS["gpt-oss-120b"] == 131
        assert KNOWN_MODEL_CONTEXT_WINDOWS["gpt-oss-20b"] == 131

    def test_only_gpt_oss_models_known(self) -> None:
        assert len(KNOWN_MODEL_CONTEXT_WINDOWS) == 2
        assert "gpt-oss-120b" in KNOWN_MODEL_CONTEXT_WINDOWS
        assert "gpt-oss-20b" in KNOWN_MODEL_CONTEXT_WINDOWS


class TestCompressionConfig:
    """Tests for CompressionConfig model."""

    def test_default_threshold_is_80_percent(self) -> None:
        config = CompressionConfig(context_window=100)
        assert config.compression_threshold == 0.8

    def test_get_context_window_from_explicit(self) -> None:
        config = CompressionConfig(context_window=50)
        assert config.get_context_window() == 50000

    def test_get_context_window_from_model_name(self) -> None:
        config = CompressionConfig(model_name="gpt-oss-120b")
        assert config.get_context_window() == 131000

    def test_get_context_window_explicit_overrides_model(self) -> None:
        config = CompressionConfig(model_name="gpt-oss-120b", context_window=50)
        assert config.get_context_window() == 50000

    def test_get_context_window_unknown_model_raises(self) -> None:
        config = CompressionConfig(model_name="unknown-model-xyz")
        with pytest.raises(ValueError, match="Unknown model"):
            config.get_context_window()

    def test_get_context_window_no_config_raises(self) -> None:
        config = CompressionConfig()
        with pytest.raises(ValueError, match="Either model_name or context_window must be set"):
            config.get_context_window()

    def test_get_token_threshold(self) -> None:
        config = CompressionConfig(context_window=100, compression_threshold=0.8)
        assert config.get_token_threshold() == 80000

    def test_get_token_threshold_custom(self) -> None:
        config = CompressionConfig(context_window=100, compression_threshold=0.5)
        assert config.get_token_threshold() == 50000

    def test_threshold_validation_min(self) -> None:
        with pytest.raises(ValueError):
            CompressionConfig(context_window=100, compression_threshold=0.05)

    def test_threshold_validation_max(self) -> None:
        with pytest.raises(ValueError):
            CompressionConfig(context_window=100, compression_threshold=1.5)

    def test_default_summary_prompt(self) -> None:
        config = CompressionConfig(context_window=100)
        assert config.summary_prompt == "What do you remember about our chat?"

    def test_custom_summary_prompt(self) -> None:
        config = CompressionConfig(context_window=100, summary_prompt="Summarize our conversation")
        assert config.summary_prompt == "Summarize our conversation"


class TestMemoryCompressor:
    """Tests for MemoryCompressor class."""

    @staticmethod
    async def mock_summarizer(text: str) -> str:
        return f"Summary of conversation with {len(text)} chars"

    def test_count_tokens(self) -> None:
        config = CompressionConfig(context_window=100)
        compressor = MemoryCompressor(config=config, summarizer=self.mock_summarizer)
        assert compressor.count_tokens("test") == 1
        assert compressor.count_tokens("hello world") == 2

    def test_count_memory_tokens(self) -> None:
        config = CompressionConfig(context_window=100)
        compressor = MemoryCompressor(config=config, summarizer=self.mock_summarizer)
        entries = [MemoryEntry(role=MessageRole.USER, content="Hello world"), MemoryEntry(role=MessageRole.ASSISTANT, content="Hi there")]
        token_count = compressor.count_memory_tokens(entries)
        assert token_count == 4

    def test_should_compress_below_threshold(self) -> None:
        config = CompressionConfig(context_window=100, compression_threshold=0.8)
        compressor = MemoryCompressor(config=config, summarizer=self.mock_summarizer)
        entries = [MemoryEntry(role=MessageRole.USER, content="Hello")]
        assert compressor.should_compress(entries) is False

    def test_should_compress_above_threshold(self) -> None:
        config = CompressionConfig(context_window=1, compression_threshold=0.8)
        compressor = MemoryCompressor(config=config, summarizer=self.mock_summarizer)
        large_content = "word " * 1000
        entries = [MemoryEntry(role=MessageRole.USER, content=large_content)]
        assert compressor.should_compress(entries) is True

    def test_should_compress_includes_system_context_tokens(self) -> None:
        """System context tokens should be counted when checking compression threshold."""
        config = CompressionConfig(context_window=1, compression_threshold=1.0)
        compressor = MemoryCompressor(config=config, summarizer=self.mock_summarizer)
        system_context = "You are helpful. " * 150
        entries = [MemoryEntry(role=MessageRole.USER, content="word " * 450)]
        memory_tokens = compressor.count_memory_tokens(entries)
        system_tokens = compressor.count_tokens(system_context)
        assert memory_tokens < 1000, f"Memory alone should be under threshold: {memory_tokens}"
        assert memory_tokens + system_tokens >= 1000, f"Memory + system should exceed threshold: {memory_tokens + system_tokens}"
        assert compressor.should_compress(entries) is False, "Without system_context, should NOT compress"
        assert compressor.should_compress(entries, system_context=system_context) is True, "With system_context, should compress"

    def test_should_compress_does_not_double_count_system_entry(self) -> None:
        """System context should NOT be double-counted if already in entries."""
        config = CompressionConfig(context_window=1, compression_threshold=1.0)
        compressor = MemoryCompressor(config=config, summarizer=self.mock_summarizer)
        system_context = "You are helpful. " * 50
        entries_with_system = [MemoryEntry(role=MessageRole.SYSTEM, content=system_context), MemoryEntry(role=MessageRole.USER, content="word " * 400)]
        should_compress_with_param = compressor.should_compress(entries_with_system, system_context=system_context)
        should_compress_without_param = compressor.should_compress(entries_with_system)
        assert should_compress_with_param == should_compress_without_param, "System context should NOT be double-counted when already in entries"

    def test_entries_have_system_context_detection(self) -> None:
        """Test detection of system context entry in entries list."""
        config = CompressionConfig(context_window=100)
        compressor = MemoryCompressor(config=config, summarizer=self.mock_summarizer)
        entries_with_system = [MemoryEntry(role=MessageRole.SYSTEM, content="System prompt"), MemoryEntry(role=MessageRole.USER, content="Hello")]
        entries_without_system = [MemoryEntry(role=MessageRole.USER, content="Hello")]
        entries_empty: list[MemoryEntry] = []
        assert compressor._entries_have_system_context(entries_with_system) is True
        assert compressor._entries_have_system_context(entries_without_system) is False
        assert compressor._entries_have_system_context(entries_empty) is False

    def test_build_conversation_text(self) -> None:
        config = CompressionConfig(context_window=100)
        compressor = MemoryCompressor(config=config, summarizer=self.mock_summarizer)
        entries = [MemoryEntry(role=MessageRole.USER, content="Hello"), MemoryEntry(role=MessageRole.ASSISTANT, content="Hi there!")]
        text = compressor.build_conversation_text(entries)
        assert "USER: Hello" in text
        assert "ASSISTANT: Hi there!" in text
        assert "Conversation History:" in text

    def test_build_conversation_text_with_system_context(self) -> None:
        config = CompressionConfig(context_window=100)
        compressor = MemoryCompressor(config=config, summarizer=self.mock_summarizer)
        entries = [MemoryEntry(role=MessageRole.USER, content="Hello")]
        text = compressor.build_conversation_text(entries, system_context="You are helpful.")
        assert "System Context: You are helpful." in text


@pytest.mark.asyncio
class TestMemoryCompressorAsync:
    """Async tests for MemoryCompressor."""

    @staticmethod
    async def mock_summarizer(text: str) -> str:
        return "This is a test summary of the conversation."

    async def test_compress_returns_three_entries(self) -> None:
        config = CompressionConfig(context_window=100)
        compressor = MemoryCompressor(config=config, summarizer=self.mock_summarizer)
        entries = [MemoryEntry(role=MessageRole.USER, content="Hello"), MemoryEntry(role=MessageRole.ASSISTANT, content="Hi!"), MemoryEntry(role=MessageRole.USER, content="How are you?"), MemoryEntry(role=MessageRole.ASSISTANT, content="I am well!")]
        compressed = await compressor.compress(entries, system_context="You are helpful.")
        assert len(compressed) == 3

    async def test_compress_format_system_user_assistant(self) -> None:
        config = CompressionConfig(context_window=100)
        compressor = MemoryCompressor(config=config, summarizer=self.mock_summarizer)
        entries = [MemoryEntry(role=MessageRole.USER, content="Hello")]
        compressed = await compressor.compress(entries, system_context="You are helpful.")
        assert compressed[0].role == "system"
        assert compressed[1].role == "user"
        assert compressed[2].role == "assistant"

    async def test_compress_preserves_system_context(self) -> None:
        config = CompressionConfig(context_window=100)
        compressor = MemoryCompressor(config=config, summarizer=self.mock_summarizer)
        entries = [MemoryEntry(role=MessageRole.USER, content="Hello")]
        compressed = await compressor.compress(entries, system_context="You are a helpful assistant.")
        assert compressed[0].content == "You are a helpful assistant."

    async def test_compress_user_message_is_summary_prompt(self) -> None:
        config = CompressionConfig(context_window=100, summary_prompt="Tell me what you remember")
        compressor = MemoryCompressor(config=config, summarizer=self.mock_summarizer)
        entries = [MemoryEntry(role=MessageRole.USER, content="Hello")]
        compressed = await compressor.compress(entries, system_context="You are helpful.")
        assert compressed[1].content == "Tell me what you remember"

    async def test_compress_assistant_message_is_summary(self) -> None:
        config = CompressionConfig(context_window=100)
        compressor = MemoryCompressor(config=config, summarizer=self.mock_summarizer)
        entries = [MemoryEntry(role=MessageRole.USER, content="Hello")]
        compressed = await compressor.compress(entries, system_context="You are helpful.")
        assert compressed[2].content == "This is a test summary of the conversation."

    async def test_compress_adds_metadata(self) -> None:
        config = CompressionConfig(context_window=100)
        compressor = MemoryCompressor(config=config, summarizer=self.mock_summarizer)
        entries = [MemoryEntry(role=MessageRole.USER, content="Hello"), MemoryEntry(role=MessageRole.ASSISTANT, content="Hi!")]
        compressed = await compressor.compress(entries, system_context="You are helpful.")
        assert compressed[2].metadata is not None
        assert compressed[2].metadata["compressed"] is True
        assert compressed[2].metadata["original_entry_count"] == 2

    async def test_compress_without_system_context(self) -> None:
        config = CompressionConfig(context_window=100)
        compressor = MemoryCompressor(config=config, summarizer=self.mock_summarizer)
        entries = [MemoryEntry(role=MessageRole.USER, content="Hello")]
        compressed = await compressor.compress(entries)
        assert len(compressed) == 2
        assert compressed[0].role == "user"
        assert compressed[1].role == "assistant"

    async def test_compress_if_needed_no_compression(self) -> None:
        config = CompressionConfig(context_window=100, compression_threshold=0.8)
        compressor = MemoryCompressor(config=config, summarizer=self.mock_summarizer)
        entries = [MemoryEntry(role=MessageRole.USER, content="Hello")]
        result, was_compressed = await compressor.compress_if_needed(entries)
        assert was_compressed is False
        assert result == entries

    async def test_compress_if_needed_with_compression(self) -> None:
        config = CompressionConfig(context_window=1, compression_threshold=0.8)
        compressor = MemoryCompressor(config=config, summarizer=self.mock_summarizer)
        large_content = "word " * 1000
        entries = [MemoryEntry(role=MessageRole.USER, content=large_content)]
        result, was_compressed = await compressor.compress_if_needed(entries, system_context="You are helpful.")
        assert was_compressed is True
        assert len(result) == 3

    async def test_compress_preserves_custom_metadata(self) -> None:
        config = CompressionConfig(context_window=100)
        compressor = MemoryCompressor(config=config, summarizer=self.mock_summarizer)
        entries = [MemoryEntry(role=MessageRole.USER, content="Hello")]
        compressed = await compressor.compress(entries, metadata={"session_id": "abc123"})
        assert compressed[-1].metadata["session_id"] == "abc123"
        assert compressed[-1].metadata["compressed"] is True
