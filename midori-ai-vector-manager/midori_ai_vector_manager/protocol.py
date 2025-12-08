"""Abstract protocol for vector storage backends."""

from abc import ABC
from abc import abstractmethod

from typing import Any
from typing import Optional

from .enums import SenderType
from .models import VectorEntry


class VectorStoreProtocol(ABC):
    """Abstract protocol for vector storage backends.

    IMPORTANT: All methods MUST be async-friendly. Use async/await throughout.
    """

    @abstractmethod
    async def store(self, text: str, sender: Optional[SenderType] = None, metadata: Optional[dict[str, Any]] = None) -> VectorEntry:
        """Store text with optional sender and metadata, return the created entry.

        Args:
            text: The text content to store
            sender: Optional sender type (USER, MODEL, SYSTEM) for reranking
            metadata: Optional additional metadata

        Returns:
            The created VectorEntry
        """
        ...

    @abstractmethod
    async def get_by_id(self, entry_id: str) -> Optional[VectorEntry]:
        """Get a single entry by ID.

        Args:
            entry_id: The unique identifier of the entry

        Returns:
            The VectorEntry if found, None otherwise
        """
        ...

    @abstractmethod
    async def query(self, filters: dict[str, Any], limit: int = 100) -> list[VectorEntry]:
        """Query entries matching filters.

        Args:
            filters: Metadata filters to apply
            limit: Maximum number of entries to return

        Returns:
            List of matching VectorEntry objects
        """
        ...

    @abstractmethod
    async def search_similar(self, query_text: str, limit: int = 10) -> list[VectorEntry]:
        """Semantic similarity search.

        Args:
            query_text: Text to search for similar entries
            limit: Maximum number of entries to return

        Returns:
            List of VectorEntry objects ranked by similarity
        """
        ...

    @abstractmethod
    async def delete(self, entry_ids: list[str]) -> int:
        """Delete entries by IDs.

        Args:
            entry_ids: List of entry IDs to delete

        Returns:
            Number of entries deleted
        """
        ...

    @abstractmethod
    async def count(self) -> int:
        """Return total entry count.

        Returns:
            Total number of entries in the store
        """
        ...

    @abstractmethod
    async def clear(self) -> None:
        """Clear all entries from the store."""
        ...
