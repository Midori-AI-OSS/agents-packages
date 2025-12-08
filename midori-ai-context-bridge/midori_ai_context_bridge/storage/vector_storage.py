"""Vector storage wrapper for context bridge.

This module provides a wrapper around ChromaVectorStore that maintains
the context-bridge API while using vector-manager for storage.
"""

from typing import Any
from typing import Optional

from midori_ai_vector_manager import ChromaVectorStore

from ..config import ModelType

from .reasoning_entry import ReasoningEntry


class ChromaStorage:
    """ChromaDB-based storage for reasoning data using vector-manager.

    Provides wrapper around ChromaVectorStore to maintain backward
    compatibility with context-bridge API while using vector-manager
    for actual storage.
    """

    def __init__(self, collection_name: str = "context_bridge", persist_directory: Optional[str] = None) -> None:
        """Initialize ChromaDB storage using vector-manager.

        Args:
            collection_name: Name for the ChromaDB collection
            persist_directory: Optional directory for persistence.
                If None, uses default vector-manager path (~/.midoriai/vectorstore/chromadb/)
        """
        self._collection_name = collection_name
        if persist_directory is None:
            persist_directory = "default"
        self._store = ChromaVectorStore(collection_name=collection_name, persist_directory=persist_directory)

    async def store(self, session_id: str, text: str, model_type: ModelType, metadata: Optional[dict[str, Any]] = None) -> ReasoningEntry:
        """Store reasoning text with metadata.

        Args:
            session_id: Session identifier
            text: Reasoning text to store
            model_type: Type of model (preprocessing or working_awareness)
            metadata: Optional additional metadata

        Returns:
            ReasoningEntry containing the stored VectorEntry
        """
        store_metadata = {"session_id": session_id, "model_type": model_type.value}
        if metadata:
            store_metadata.update(metadata)
        vector_entry = await self._store.store(text=text, sender=None, metadata=store_metadata)
        reasoning_entry = ReasoningEntry(model_type=model_type)
        reasoning_entry.add_entry(vector_entry)
        return reasoning_entry

    def _extract_model_type(self, metadata: dict[str, Any]) -> ModelType:
        """Extract ModelType from VectorEntry metadata.

        Args:
            metadata: Metadata dictionary from VectorEntry

        Returns:
            ModelType enum value
        """
        model_type_str = metadata.get("model_type", ModelType.PREPROCESSING.value)
        return ModelType(model_type_str)

    async def get_entries_for_session(self, session_id: str, model_type: Optional[ModelType] = None, limit: int = 100) -> list[ReasoningEntry]:
        """Get entries for a session, optionally filtered by model type.

        Args:
            session_id: Session identifier to filter by
            model_type: Optional model type filter
            limit: Maximum number of entries to return

        Returns:
            List of ReasoningEntry objects
        """
        filters: dict[str, Any] = {"session_id": session_id}
        if model_type is not None:
            filters["model_type"] = model_type.value
        vector_entries = await self._store.query(filters=filters, limit=limit)
        reasoning_entries = []
        for vector_entry in vector_entries:
            model_type_enum = self._extract_model_type(vector_entry.metadata)
            reasoning_entry = ReasoningEntry(model_type=model_type_enum)
            reasoning_entry.add_entry(vector_entry)
            reasoning_entries.append(reasoning_entry)
        return reasoning_entries

    async def delete_entries(self, entry_ids: list[str]) -> int:
        """Delete entries by their IDs.

        Args:
            entry_ids: List of entry IDs to delete

        Returns:
            Number of entries deleted
        """
        if not entry_ids:
            return 0
        return await self._store.delete(entry_ids)

    async def get_all_entries(self, limit: int = 1000) -> list[ReasoningEntry]:
        """Get all entries in the storage.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of all ReasoningEntry objects
        """
        vector_entries = await self._store.query(filters={}, limit=limit)
        reasoning_entries = []
        for vector_entry in vector_entries:
            model_type_enum = self._extract_model_type(vector_entry.metadata)
            reasoning_entry = ReasoningEntry(model_type=model_type_enum)
            reasoning_entry.add_entry(vector_entry)
            reasoning_entries.append(reasoning_entry)
        return reasoning_entries

    async def count(self) -> int:
        """Return the total number of entries in storage.

        Returns:
            Total count of stored entries
        """
        return await self._store.count()

    async def clear(self) -> None:
        """Clear all entries from storage."""
        await self._store.clear()
