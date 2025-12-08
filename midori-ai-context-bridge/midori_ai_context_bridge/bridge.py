"""Main ContextBridge class for persistent thinking cache.

This module provides the primary interface for storing and retrieving
reasoning data with time-based memory decay.
"""

from typing import Optional

from midori_ai_logger import MidoriAiLogger

from .compressor import ContextCompressor
from .compressor import create_compressor

from .config import BridgeConfig
from .config import ModelType

from .corruption import MemoryCorruptor

from .storage import ChromaStorage
from .storage import ReasoningEntry


_logger = MidoriAiLogger(None, name="ContextBridge")


class ContextBridge:
    """Persistent thinking cache with ChromaDB storage and time-based decay.

    The ContextBridge provides a caching layer for reasoning models that:
    - Stores reasoning data in ChromaDB vector storage
    - Applies time-based memory corruption for older data
    - Supports different decay rates for preprocessing vs working awareness
    - Automatically cleans up data older than the removal threshold

    Usage:
        bridge = ContextBridge(max_tokens_per_summary=500)

        # Store reasoning after model inference
        await bridge.store_reasoning(
            session_id="username:discordid",
            text="reasoning output...",
            model_type=ModelType.PREPROCESSING
        )

        # Get prior reasoning before model inference
        context = await bridge.get_prior_reasoning(
            session_id="username:discordid",
            model_type=ModelType.PREPROCESSING
        )
    """

    def __init__(self, max_tokens_per_summary: int = 500, config: Optional[BridgeConfig] = None, persist_directory: Optional[str] = None) -> None:
        """Initialize the ContextBridge.

        Args:
            max_tokens_per_summary: Maximum tokens for compressed context
            config: Optional BridgeConfig (defaults created if None)
            persist_directory: Optional directory for ChromaDB persistence
        """
        self._config = config or BridgeConfig(max_tokens_per_summary=max_tokens_per_summary)
        self._storage = ChromaStorage(collection_name=self._config.chroma_collection_name, persist_directory=persist_directory)
        self._compressor = create_compressor(max_tokens=self._config.max_tokens_per_summary)
        self._corruptors = {ModelType.PREPROCESSING: MemoryCorruptor(self._config.get_decay_config(ModelType.PREPROCESSING)), ModelType.WORKING_AWARENESS: MemoryCorruptor(self._config.get_decay_config(ModelType.WORKING_AWARENESS))}

    @property
    def config(self) -> BridgeConfig:
        """Return the bridge configuration."""
        return self._config

    @property
    def storage(self) -> ChromaStorage:
        """Return the underlying ChromaDB storage."""
        return self._storage

    @property
    def compressor(self) -> ContextCompressor:
        """Return the context compressor."""
        return self._compressor

    def get_corruptor(self, model_type: ModelType) -> MemoryCorruptor:
        """Get the corruptor for a specific model type.

        Args:
            model_type: The model type

        Returns:
            MemoryCorruptor configured for that model type
        """
        return self._corruptors[model_type]

    async def store_reasoning(self, session_id: str, text: str, model_type: ModelType, metadata: Optional[dict] = None) -> ReasoningEntry:
        """Store reasoning text with timestamp.

        Args:
            session_id: Session identifier (e.g., "username:discordid")
            text: The reasoning text to store
            model_type: Type of model (PREPROCESSING or WORKING_AWARENESS)
            metadata: Optional additional metadata

        Returns:
            The created ReasoningEntry
        """
        entry = await self._storage.store(session_id=session_id, text=text, model_type=model_type, metadata=metadata)
        await _logger.print(f"Stored reasoning for session {session_id}, model_type={model_type.value}", mode="debug")
        return entry

    async def get_prior_reasoning(self, session_id: str, model_type: ModelType, include_corrupted: bool = True) -> str:
        """Get prior reasoning for a session with optional corruption.

        Retrieves stored reasoning, applies time-based corruption,
        removes expired entries, and returns compressed context.

        Args:
            session_id: Session identifier
            model_type: Type of model to get context for
            include_corrupted: Whether to include corrupted text (default True)

        Returns:
            Compressed context string, empty if no prior reasoning
        """
        entries = await self._storage.get_entries_for_session(session_id=session_id, model_type=model_type)
        if not entries:
            return ""
        corruptor = self.get_corruptor(model_type)
        entries_to_remove = []
        processed_texts = []
        for entry in entries:
            age = entry.age_minutes
            corrupted, should_remove = corruptor.process_text(entry.text, age)
            if should_remove:
                entries_to_remove.append(entry.id)
                await _logger.print(f"Marking entry {entry.id} for removal (age={age:.1f}m)", mode="debug")
            elif corrupted and include_corrupted:
                processed_texts.append(corrupted)
        if entries_to_remove:
            await self._storage.delete_entries(entries_to_remove)
            await _logger.print(f"Removed {len(entries_to_remove)} expired entries", mode="debug")
        if not processed_texts:
            return ""
        return await self._compressor.compress(processed_texts)

    async def cleanup_expired(self) -> int:
        """Clean up all expired entries across all sessions.

        Returns:
            Number of entries removed
        """
        all_entries = await self._storage.get_all_entries()
        entries_to_remove = []
        for entry in all_entries:
            corruptor = self.get_corruptor(entry.model_type)
            if corruptor.should_remove(entry.age_minutes):
                entries_to_remove.append(entry.id)
        if entries_to_remove:
            await self._storage.delete_entries(entries_to_remove)
            await _logger.print(f"Cleanup removed {len(entries_to_remove)} expired entries", mode="debug")
        return len(entries_to_remove)

    async def get_session_stats(self, session_id: str) -> dict:
        """Get statistics for a session's stored reasoning.

        Args:
            session_id: Session identifier

        Returns:
            Dict with counts and age statistics
        """
        preprocessing_entries = await self._storage.get_entries_for_session(session_id, ModelType.PREPROCESSING)
        working_entries = await self._storage.get_entries_for_session(session_id, ModelType.WORKING_AWARENESS)
        preprocessing_count = len(preprocessing_entries)
        working_awareness_count = len(working_entries)
        total_count = preprocessing_count + working_awareness_count
        oldest_preprocessing_age = min((e.age_minutes for e in preprocessing_entries), default=0)
        oldest_working_age = min((e.age_minutes for e in working_entries), default=0)
        return {"session_id": session_id, "preprocessing_count": preprocessing_count, "working_awareness_count": working_awareness_count, "total_count": total_count, "oldest_preprocessing_age_minutes": oldest_preprocessing_age, "oldest_working_age_minutes": oldest_working_age}

    async def clear_session(self, session_id: str) -> int:
        """Clear all entries for a session.

        Args:
            session_id: Session identifier

        Returns:
            Number of entries removed
        """
        entries = await self._storage.get_entries_for_session(session_id)
        if not entries:
            return 0
        entry_ids = [e.id for e in entries]
        await self._storage.delete_entries(entry_ids)
        await _logger.print(f"Cleared {len(entry_ids)} entries for session {session_id}", mode="debug")
        return len(entry_ids)

    async def count(self) -> int:
        """Return total number of stored entries.

        Returns:
            Total count of entries
        """
        return await self._storage.count()
