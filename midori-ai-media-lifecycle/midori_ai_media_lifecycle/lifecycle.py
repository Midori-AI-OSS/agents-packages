"""Main lifecycle manager for media objects."""

from datetime import datetime
from datetime import timezone

from pathlib import Path

from midori_ai_media_vault import MediaObject
from midori_ai_media_vault import MediaStorage

from .decay import DecayConfig
from .decay import get_parsing_probability
from .decay import is_aged_out
from .decay import should_parse


def utcnow() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class LifecycleManager:
    """Manages media object lifecycle with decay and cleanup operations.

    Provides methods to:
    - Check parsing probability and aged-out status
    - Mark media as loaded or parsed
    - Clean up aged-out media from storage
    """

    def __init__(self, storage: MediaStorage, config: DecayConfig | None = None) -> None:
        """Initialize lifecycle manager.

        Args:
            storage: MediaStorage instance for persistence
            config: Decay configuration (uses defaults if None)
        """
        self.storage = storage
        self.config = config if config is not None else DecayConfig()

    def get_parsing_probability(self, media: MediaObject) -> float:
        """Get parsing probability for a media object.

        Args:
            media: The media object to check

        Returns:
            Probability as float from 0.0 to 1.0
        """
        return get_parsing_probability(media.metadata.time_saved, self.config)

    def should_parse(self, media: MediaObject) -> bool:
        """Determine probabilistically whether to parse media.

        Args:
            media: The media object to check

        Returns:
            True if should parse, False otherwise
        """
        return should_parse(media.metadata.time_saved, self.config)

    def is_aged_out(self, media: MediaObject) -> bool:
        """Check if media has aged out and should be cleaned up.

        Args:
            media: The media object to check

        Returns:
            True if aged out, False otherwise
        """
        return is_aged_out(media.metadata.time_saved, self.config)

    async def mark_loaded(self, media: MediaObject) -> MediaObject:
        """Mark media as loaded and persist the update.

        Updates time_loaded to current time and saves to storage.

        Args:
            media: The media object to update

        Returns:
            Updated MediaObject with new time_loaded
        """
        media.metadata.time_loaded = utcnow()
        await self.storage.save(media)
        return media

    async def mark_parsed(self, media: MediaObject) -> MediaObject:
        """Mark media as parsed and persist the update.

        Updates time_parsed to current time and saves to storage.

        Args:
            media: The media object to update

        Returns:
            Updated MediaObject with new time_parsed
        """
        media.metadata.time_parsed = utcnow()
        await self.storage.save(media)
        return media

    async def cleanup_aged_media(self) -> list[str]:
        """Remove all aged-out media from storage.

        Iterates through all media and deletes those that have aged out.

        Returns:
            List of deleted media IDs
        """
        deleted_ids: list[str] = []
        media_ids = await self.storage.list_all()
        for media_id in media_ids:
            try:
                media = await self.storage.load(media_id)
                if self.is_aged_out(media):
                    await self.storage.delete(media_id)
                    deleted_ids.append(media_id)
            except FileNotFoundError:
                continue
        return deleted_ids

    async def get_media_status(self, media_id: str) -> dict[str, object]:
        """Get status information for a media object.

        Args:
            media_id: The media ID to check

        Returns:
            Dict with status info (probability, aged_out, times, etc.)

        Raises:
            FileNotFoundError: If media doesn't exist
        """
        media = await self.storage.load(media_id)
        probability = self.get_parsing_probability(media)
        aged_out = self.is_aged_out(media)
        return {
            "media_id": media_id,
            "probability": probability,
            "aged_out": aged_out,
            "time_saved": media.metadata.time_saved,
            "time_loaded": media.metadata.time_loaded,
            "time_parsed": media.metadata.time_parsed,
        }


def create_lifecycle_manager(base_path: Path, config: DecayConfig | None = None) -> LifecycleManager:
    """Factory function to create a LifecycleManager with new storage.

    Args:
        base_path: Directory for media storage
        config: Decay configuration (uses defaults if None)

    Returns:
        Configured LifecycleManager instance
    """
    storage = MediaStorage(base_path=base_path)
    return LifecycleManager(storage=storage, config=config)
