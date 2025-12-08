"""Configuration for reranker thresholds and settings."""

from dataclasses import dataclass


@dataclass
class RerankerConfig:
    """Configuration for document reranking.

    Attributes:
        relevance_threshold: Base relevance threshold (default 0.2)
        similarity_threshold_mod: Per-query threshold modifier (default 0.0)
        max_items: Maximum number of items to process (default 50)
        enable_redundant_filter: Enable duplicate removal (default True)
        enable_relevance_filter: Enable relevance filtering (default True)
    """

    relevance_threshold: float = 0.2
    similarity_threshold_mod: float = 0.0
    max_items: int = 50
    enable_redundant_filter: bool = True
    enable_relevance_filter: bool = True

    @property
    def effective_threshold(self) -> float:
        """Calculate effective threshold as base + modifier."""
        return self.relevance_threshold + self.similarity_threshold_mod


DEFAULT_CONFIG = RerankerConfig()
