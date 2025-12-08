"""Async disk storage with Pydantic JSON serialization and system-stats encryption."""

import asyncio

from pathlib import Path

from cryptography.fernet import InvalidToken

from .models import MediaObject
from .models import MediaType
from .system_crypto import SystemCrypto


class StorageDecryptionError(Exception):
    """Raised when storage decryption fails due to system mismatch or corruption."""

    pass


class MediaStorage:
    """Persists MediaObjects to disk using Pydantic JSON serialization.

    Uses onion/layered encryption:
    1. Media content is encrypted with per-file random Fernet key (in MediaObject)
    2. The entire MediaObject JSON is encrypted with system-stats-derived key when saved

    This provides defense-in-depth: even if the storage files are copied to another
    system, they cannot be decrypted without matching system stats.

    Files are organized into type-specific subfolders (photo/, video/, audio/, text/)
    which enables fast list_by_type() operations without loading/decrypting each file.
    """

    def __init__(self, base_path: Path, system_key_iterations: int = 12) -> None:
        """Initialize storage with base directory path.

        Args:
            base_path: Directory where media files will be stored
            system_key_iterations: Number of hash iterations for system key derivation
        """
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._ensure_type_folders()
        self.system_crypto = SystemCrypto(iterations=system_key_iterations)

    def _ensure_type_folders(self) -> None:
        """Create subfolders for each media type."""
        for media_type in MediaType:
            type_folder = self.base_path / media_type.value
            type_folder.mkdir(parents=True, exist_ok=True)

    def _get_type_folder(self, media_type: MediaType) -> Path:
        """Get the folder path for a media type."""
        return self.base_path / media_type.value

    def _get_media_path(self, media_id: str, media_type: MediaType) -> Path:
        """Get the file path for a media ID within its type folder."""
        return self._get_type_folder(media_type) / f"{media_id}.media"

    def _find_media_path(self, media_id: str) -> tuple[Path, MediaType] | None:
        """Find media file across all type folders, returns path and type if found."""
        for media_type in MediaType:
            path = self._get_media_path(media_id, media_type)
            if path.exists():
                return path, media_type
        return None

    async def save(self, media: MediaObject) -> Path:
        """Save media object to disk with system-stats encryption.

        The MediaObject (which already contains encrypted content) is serialized
        to JSON and then encrypted again using system-stats-derived key.
        Files are stored in type-specific subfolders for fast list_by_type().

        Args:
            media: The MediaObject to persist

        Returns:
            Path to the saved file
        """
        file_path = self._get_media_path(media.id, media.media_type)
        json_data = media.model_dump_json()
        encrypted_json = self.system_crypto.encrypt(json_data.encode())
        await asyncio.to_thread(file_path.write_bytes, encrypted_json)
        return file_path

    async def load(self, media_id: str) -> MediaObject:
        """Load and validate media object from disk.

        Decrypts the file using system-stats-derived key, then validates
        the JSON as a MediaObject. Searches all type folders.

        Args:
            media_id: The unique identifier of the media

        Returns:
            The loaded and validated MediaObject

        Raises:
            FileNotFoundError: If the media file doesn't exist
            StorageDecryptionError: If decryption fails (wrong system or corrupted)
        """
        result = await asyncio.to_thread(self._find_media_path, media_id)
        if result is None:
            raise FileNotFoundError(f"Media '{media_id}' not found in any type folder")
        file_path, _ = result
        encrypted_data = await asyncio.to_thread(file_path.read_bytes)
        try:
            json_data = self.system_crypto.decrypt(encrypted_data).decode()
        except InvalidToken as e:
            raise StorageDecryptionError(f"Failed to decrypt media '{media_id}': file may be from a different system or corrupted") from e
        except UnicodeDecodeError as e:
            raise StorageDecryptionError(f"Failed to decode media '{media_id}': decrypted data is not valid UTF-8") from e
        return MediaObject.model_validate_json(json_data)

    async def delete(self, media_id: str) -> bool:
        """Delete a media object from disk.

        Searches all type folders for the media file.

        Args:
            media_id: The unique identifier of the media

        Returns:
            True if deleted, False if file didn't exist
        """
        result = await asyncio.to_thread(self._find_media_path, media_id)
        if result is None:
            return False
        file_path, _ = result
        await asyncio.to_thread(file_path.unlink)
        return True

    async def exists(self, media_id: str) -> bool:
        """Check if a media object exists.

        Searches all type folders for the media file.

        Args:
            media_id: The unique identifier of the media

        Returns:
            True if exists, False otherwise
        """
        result = await asyncio.to_thread(self._find_media_path, media_id)
        return result is not None

    async def list_all(self) -> list[str]:
        """List all media IDs in storage.

        Scans all type folders and returns unique media IDs.

        Returns:
            List of media IDs
        """
        def _list_files() -> list[str]:
            all_ids: list[str] = []
            for media_type in MediaType:
                type_folder = self._get_type_folder(media_type)
                all_ids.extend(f.stem for f in type_folder.glob("*.media"))
            return all_ids

        return await asyncio.to_thread(_list_files)

    async def list_by_type(self, media_type: MediaType) -> list[str]:
        """List all media IDs of a specific type.

        This method is optimized to simply list files in the type-specific folder,
        avoiding the need to load and decrypt each file to check its type.

        Args:
            media_type: Filter by this MediaType (PHOTO, VIDEO, AUDIO, TEXT)

        Returns:
            List of media IDs matching the type
        """
        def _list_type_folder() -> list[str]:
            type_folder = self._get_type_folder(media_type)
            return [f.stem for f in type_folder.glob("*.media")]

        return await asyncio.to_thread(_list_type_folder)
