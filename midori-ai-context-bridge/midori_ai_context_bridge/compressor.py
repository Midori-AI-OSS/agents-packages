"""Compressor for summarizing prior reasoning context.

This module provides utilities for summarizing reasoning
data before injection into new prompts.
"""

from typing import Optional


class ContextCompressor:
    """Compresses and summarizes reasoning context.

    The compressor takes a list of reasoning texts and creates
    a condensed summary suitable for injection into prompts.
    """

    def __init__(self, max_tokens: int = 500) -> None:
        """Initialize the compressor.

        Args:
            max_tokens: Maximum tokens for the compressed output
        """
        self._max_tokens = max_tokens

    @property
    def max_tokens(self) -> int:
        """Return the maximum token limit."""
        return self._max_tokens

    async def compress(self, texts: list[str], separator: str = "\n\n---\n\n") -> str:
        """Compress multiple reasoning texts into a summary.

        This is a simple implementation that truncates to fit the
        token limit. In production, this could use an LLM for
        intelligent summarization.

        Args:
            texts: List of reasoning texts to compress
            separator: Separator between texts

        Returns:
            Compressed summary string
        """
        if not texts:
            return ""
        combined = separator.join(texts)
        estimated_chars = self._max_tokens * 4
        if len(combined) > estimated_chars:
            combined = combined[:estimated_chars] + "..."
        return combined

    async def compress_with_labels(self, labeled_texts: list[tuple[str, str]], separator: str = "\n\n") -> str:
        """Compress texts with labels for context.

        Args:
            labeled_texts: List of (label, text) tuples
            separator: Separator between entries

        Returns:
            Compressed summary with labels
        """
        if not labeled_texts:
            return ""
        lines = []
        for label, text in labeled_texts:
            lines.append(f"[{label}]\n{text}")
        return await self.compress(lines, separator)

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Uses simple character-based estimation (4 chars ≈ 1 token).

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return len(text) // 4


def create_compressor(max_tokens: Optional[int] = None) -> ContextCompressor:
    """Factory function to create a ContextCompressor.

    Args:
        max_tokens: Optional max tokens (defaults to 500)

    Returns:
        Configured ContextCompressor instance
    """
    return ContextCompressor(max_tokens=max_tokens or 500)
