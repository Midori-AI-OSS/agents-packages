"""Memory compression for automatic context window management."""

import tiktoken

from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from .models import MemoryEntry
from .models import MessageRole


KNOWN_MODEL_CONTEXT_WINDOWS: dict[str, int] = {
    "gpt-oss-120b": 131,
    "gpt-oss-20b": 131,
}

SummarizerCallable = Callable[[str], Awaitable[str]]


class CompressionConfig(BaseModel):
    """Configuration for memory compression behavior.

    Attributes:
        model_name: Name of the model (used to lookup context window from KNOWN_MODEL_CONTEXT_WINDOWS)
        context_window: Override context window size in thousands of tokens (k)
        compression_threshold: Ratio of context window at which compression triggers (default: 0.8 = 80%)
        summary_prompt: The prompt used to ask for memory summary
    """

    model_name: Optional[str] = Field(default=None, description="Model name for context window lookup")
    context_window: Optional[int] = Field(default=None, description="Override context window size in thousands of tokens (k)")
    compression_threshold: float = Field(default=0.8, ge=0.1, le=1.0, description="Ratio of context window to trigger compression")
    summary_prompt: str = Field(default="What do you remember about our chat?", description="User message prompt for summary request")

    def get_context_window(self) -> int:
        """Get the context window size, using model lookup or override.

        Returns:
            The context window size in tokens (converted from k)

        Raises:
            ValueError: If neither model_name nor context_window is set, or model is unknown
        """
        if self.context_window is not None:
            return self.context_window * 1000
        if self.model_name is not None:
            normalized_name = self.model_name.lower()
            if normalized_name in KNOWN_MODEL_CONTEXT_WINDOWS:
                return KNOWN_MODEL_CONTEXT_WINDOWS[normalized_name] * 1000
            raise ValueError(f"Unknown model '{self.model_name}'. Set context_window explicitly or use a known model from: {list(KNOWN_MODEL_CONTEXT_WINDOWS.keys())}")
        raise ValueError("Either model_name or context_window must be set")

    def get_token_threshold(self) -> int:
        """Get the token count threshold for triggering compression.

        Returns:
            The token count at which compression should trigger
        """
        return int(self.get_context_window() * self.compression_threshold)


class MemoryCompressor:
    """Handles automatic memory compression when context window limits are approached.

    The compressor uses a configurable threshold (default 80% of context window) to
    determine when to compress memory. When triggered, it uses a provided summarizer
    callable to generate a summary of the conversation history.

    Usage:
        async def my_summarizer(text: str) -> str:
            # Use your LLM to summarize
            return await llm.summarize(text)

        compressor = MemoryCompressor(
            config=CompressionConfig(model_name="gpt-oss-120b", compression_threshold=0.8),
            summarizer=my_summarizer
        )

        # Check and compress if needed
        if compressor.should_compress(memory_store):
            compressed = await compressor.compress(memory_store, system_context="You are helpful.")
    """

    def __init__(self, config: CompressionConfig, summarizer: SummarizerCallable) -> None:
        """Initialize the memory compressor.

        Args:
            config: Configuration for compression behavior
            summarizer: Async callable that takes text and returns a summary
        """
        self._config = config
        self._summarizer = summarizer
        self._encoder = tiktoken.get_encoding("o200k_base")

    @property
    def config(self) -> CompressionConfig:
        """Return the compression configuration."""
        return self._config

    def count_tokens(self, text: str) -> int:
        """Count tokens for a text string using tiktoken.

        Args:
            text: The text to count tokens for

        Returns:
            Exact token count
        """
        return len(self._encoder.encode(text))

    def count_memory_tokens(self, entries: list[MemoryEntry]) -> int:
        """Count total tokens used by memory entries.

        Args:
            entries: List of memory entries to count

        Returns:
            Total token count
        """
        total = 0
        for entry in entries:
            total += self.count_tokens(entry.content)
            if entry.tool_calls:
                for tc in entry.tool_calls:
                    total += self.count_tokens(tc.name)
                    total += self.count_tokens(str(tc.args))
                    if tc.result:
                        total += self.count_tokens(tc.result)
        return total

    def _entries_have_system_context(self, entries: list[MemoryEntry]) -> bool:
        """Check if entries already contain a system context entry.

        Args:
            entries: List of memory entries to check

        Returns:
            True if entries contain a SYSTEM role entry (typically from prior compression)
        """
        return bool(entries) and entries[0].role == MessageRole.SYSTEM

    def should_compress(self, entries: list[MemoryEntry], system_context: Optional[str] = None) -> bool:
        """Check if memory should be compressed based on token count.

        The system_context tokens are included in the count only if the entries
        do not already contain a SYSTEM entry (to avoid double-counting after
        a previous compression).

        Args:
            entries: List of memory entries to check
            system_context: Optional system context to include in token count

        Returns:
            True if compression should be triggered
        """
        token_count = self.count_memory_tokens(entries)
        if system_context and not self._entries_have_system_context(entries):
            token_count += self.count_tokens(system_context)
        threshold = self._config.get_token_threshold()
        return token_count >= threshold

    def build_conversation_text(self, entries: list[MemoryEntry], system_context: Optional[str] = None) -> str:
        """Build a text representation of the conversation for summarization.

        Args:
            entries: List of memory entries
            system_context: Optional system context to include

        Returns:
            Formatted conversation text
        """
        parts: list[str] = []
        if system_context:
            parts.append(f"System Context: {system_context}")
            parts.append("")
        parts.append("Conversation History:")
        for entry in entries:
            role = str(entry.role).upper()
            parts.append(f"{role}: {entry.content}")
            if entry.tool_calls:
                for tc in entry.tool_calls:
                    parts.append(f"  [Tool: {tc.name}] {tc.result or 'pending'}")
        return "\n".join(parts)

    async def compress(self, entries: list[MemoryEntry], system_context: Optional[str] = None, metadata: Optional[dict[str, Any]] = None) -> list[MemoryEntry]:
        """Compress memory entries into a summarized format.

        The output format is:
        1. System message (with original system context)
        2. User message asking "What do you remember about our chat?"
        3. Assistant message with the generated summary

        Args:
            entries: List of memory entries to compress
            system_context: Optional system context to preserve
            metadata: Optional metadata to attach to the summary entry

        Returns:
            List of 3 compressed memory entries (system, user, assistant)
        """
        conversation_text = self.build_conversation_text(entries, system_context)
        summarization_prompt = f"Please summarize the following conversation, capturing the key topics, decisions, and important details that should be remembered for future context:\n\n{conversation_text}"
        summary = await self._summarizer(summarization_prompt)
        compressed_entries: list[MemoryEntry] = []
        if system_context:
            compressed_entries.append(MemoryEntry(role=MessageRole.SYSTEM, content=system_context))
        compressed_entries.append(MemoryEntry(role=MessageRole.USER, content=self._config.summary_prompt))
        summary_metadata = metadata.copy() if metadata else {}
        summary_metadata["compressed"] = True
        summary_metadata["original_entry_count"] = len(entries)
        compressed_entries.append(MemoryEntry(role=MessageRole.ASSISTANT, content=summary, metadata=summary_metadata))
        return compressed_entries

    async def compress_if_needed(self, entries: list[MemoryEntry], system_context: Optional[str] = None, metadata: Optional[dict[str, Any]] = None) -> tuple[list[MemoryEntry], bool]:
        """Compress memory entries if threshold is exceeded.

        Args:
            entries: List of memory entries to potentially compress
            system_context: Optional system context to preserve
            metadata: Optional metadata to attach to the summary entry

        Returns:
            Tuple of (entries, was_compressed) where entries are either original or compressed
        """
        if self.should_compress(entries, system_context):
            compressed = await self.compress(entries, system_context, metadata)
            return compressed, True
        return entries, False
