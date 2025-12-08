"""Tests for async storage."""

import pytest

from pathlib import Path

from midori_ai_media_vault import MediaCrypto
from midori_ai_media_vault import MediaMetadata
from midori_ai_media_vault import MediaObject
from midori_ai_media_vault import MediaStorage
from midori_ai_media_vault import MediaType


def create_test_media(media_id: str = "test-media", media_type: MediaType = MediaType.PHOTO) -> MediaObject:
    """Create a test MediaObject."""
    content = b"test content"
    encrypted, key, hash_str = MediaCrypto.encrypt(content)
    metadata = MediaMetadata(content_hash=hash_str)
    return MediaObject(
        id=media_id,
        media_type=media_type,
        metadata=metadata,
        user_id="user-123",
        encrypted_content=encrypted,
        encryption_key=key,
        content_integrity_hash=hash_str,
    )


class TestMediaStorage:
    """Tests for MediaStorage class."""

    def test_init_creates_directory(self, tmp_path: Path) -> None:
        storage_path = tmp_path / "media"
        assert not storage_path.exists()
        MediaStorage(base_path=storage_path)
        assert storage_path.exists()

    def test_init_existing_directory(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        assert storage.base_path == tmp_path

    def test_init_creates_type_subfolders(self, tmp_path: Path) -> None:
        """Verify type-specific subfolders are created on init."""
        storage_path = tmp_path / "media"
        MediaStorage(base_path=storage_path)
        for media_type in MediaType:
            type_folder = storage_path / media_type.value
            assert type_folder.exists(), f"Type folder '{media_type.value}' should exist"
            assert type_folder.is_dir(), f"Type folder '{media_type.value}' should be a directory"


@pytest.mark.asyncio
class TestMediaStorageAsync:
    """Async tests for MediaStorage."""

    async def test_save_creates_file(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        media = create_test_media()
        file_path = await storage.save(media)
        assert file_path.exists()
        assert file_path.suffix == ".media"

    async def test_save_stores_in_type_folder(self, tmp_path: Path) -> None:
        """Verify files are saved in the correct type-specific folder."""
        storage = MediaStorage(base_path=tmp_path)
        for media_type in MediaType:
            media = create_test_media(f"{media_type.value}-test", media_type)
            file_path = await storage.save(media)
            expected_folder = tmp_path / media_type.value
            assert file_path.parent == expected_folder, f"File should be in '{media_type.value}' folder"
            assert file_path.name == f"{media_type.value}-test.media"

    async def test_save_and_load(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        media = create_test_media("save-load-test")
        await storage.save(media)
        loaded = await storage.load("save-load-test")
        assert loaded.id == media.id
        assert loaded.media_type == media.media_type
        assert loaded.user_id == media.user_id
        assert loaded.encrypted_content == media.encrypted_content
        assert loaded.encryption_key == media.encryption_key
        assert loaded.content_integrity_hash == media.content_integrity_hash

    async def test_load_missing_raises(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        with pytest.raises(FileNotFoundError):
            await storage.load("nonexistent")

    async def test_delete_existing(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        media = create_test_media("delete-test")
        await storage.save(media)
        assert await storage.exists("delete-test")
        deleted = await storage.delete("delete-test")
        assert deleted is True
        assert not await storage.exists("delete-test")

    async def test_delete_missing(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        deleted = await storage.delete("nonexistent")
        assert deleted is False

    async def test_exists_true(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        media = create_test_media("exists-test")
        await storage.save(media)
        assert await storage.exists("exists-test") is True

    async def test_exists_false(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        assert await storage.exists("nonexistent") is False

    async def test_list_all_empty(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        ids = await storage.list_all()
        assert ids == []

    async def test_list_all_with_media(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        await storage.save(create_test_media("media-1"))
        await storage.save(create_test_media("media-2"))
        await storage.save(create_test_media("media-3"))
        ids = await storage.list_all()
        assert set(ids) == {"media-1", "media-2", "media-3"}

    async def test_full_roundtrip_with_decryption(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        original_content = b"secret data to store"
        encrypted, key, hash_str = MediaCrypto.encrypt(original_content)
        metadata = MediaMetadata(content_hash=hash_str)
        media = MediaObject(
            id="roundtrip-test",
            media_type=MediaType.TEXT,
            metadata=metadata,
            user_id="user",
            encrypted_content=encrypted,
            encryption_key=key,
            content_integrity_hash=hash_str,
        )
        await storage.save(media)
        loaded = await storage.load("roundtrip-test")
        decrypted = MediaCrypto.decrypt(loaded.encrypted_content, loaded.encryption_key, loaded.content_integrity_hash)
        assert decrypted == original_content

    async def test_list_by_type_empty(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        ids = await storage.list_by_type(MediaType.PHOTO)
        assert ids == []

    async def test_list_by_type_returns_matching(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        await storage.save(create_test_media("photo-1", MediaType.PHOTO))
        await storage.save(create_test_media("photo-2", MediaType.PHOTO))
        await storage.save(create_test_media("video-1", MediaType.VIDEO))
        ids = await storage.list_by_type(MediaType.PHOTO)
        assert set(ids) == {"photo-1", "photo-2"}

    async def test_list_by_type_returns_only_requested_type(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        await storage.save(create_test_media("audio-1", MediaType.AUDIO))
        await storage.save(create_test_media("text-1", MediaType.TEXT))
        await storage.save(create_test_media("video-1", MediaType.VIDEO))
        await storage.save(create_test_media("photo-1", MediaType.PHOTO))
        audio_ids = await storage.list_by_type(MediaType.AUDIO)
        assert audio_ids == ["audio-1"]
        text_ids = await storage.list_by_type(MediaType.TEXT)
        assert text_ids == ["text-1"]
        video_ids = await storage.list_by_type(MediaType.VIDEO)
        assert video_ids == ["video-1"]
        photo_ids = await storage.list_by_type(MediaType.PHOTO)
        assert photo_ids == ["photo-1"]

    async def test_list_by_type_no_match(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        await storage.save(create_test_media("photo-1", MediaType.PHOTO))
        await storage.save(create_test_media("photo-2", MediaType.PHOTO))
        ids = await storage.list_by_type(MediaType.VIDEO)
        assert ids == []

    async def test_list_by_type_all_media_types(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        for media_type in MediaType:
            await storage.save(create_test_media(f"{media_type.value}-test", media_type))
        for media_type in MediaType:
            ids = await storage.list_by_type(media_type)
            assert ids == [f"{media_type.value}-test"]
