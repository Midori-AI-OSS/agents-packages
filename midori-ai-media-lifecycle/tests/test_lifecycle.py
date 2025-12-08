"""Tests for lifecycle manager."""

import pytest

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from pathlib import Path

from midori_ai_media_lifecycle import CleanupScheduler
from midori_ai_media_lifecycle import DecayConfig
from midori_ai_media_lifecycle import LifecycleManager
from midori_ai_media_lifecycle import create_lifecycle_manager

from midori_ai_media_vault import MediaCrypto
from midori_ai_media_vault import MediaMetadata
from midori_ai_media_vault import MediaObject
from midori_ai_media_vault import MediaStorage
from midori_ai_media_vault import MediaType


def create_test_media(media_id: str = "test-media", age_minutes: float = 0.0) -> MediaObject:
    """Create a test MediaObject with optional age."""
    content = b"test content"
    encrypted, key, hash_str = MediaCrypto.encrypt(content)
    time_saved = datetime.now(timezone.utc) - timedelta(minutes=age_minutes)
    metadata = MediaMetadata(content_hash=hash_str, time_saved=time_saved)
    return MediaObject(
        id=media_id,
        media_type=MediaType.PHOTO,
        metadata=metadata,
        user_id="user-123",
        encrypted_content=encrypted,
        encryption_key=key,
        content_integrity_hash=hash_str,
    )


class TestLifecycleManager:
    """Tests for LifecycleManager class."""

    def test_init_with_defaults(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        assert manager.storage == storage
        assert manager.config.full_probability_minutes == 35.0
        assert manager.config.zero_probability_minutes == 90.0

    def test_init_with_custom_config(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        config = DecayConfig(full_probability_minutes=10.0, zero_probability_minutes=60.0)
        manager = LifecycleManager(storage=storage, config=config)
        assert manager.config.full_probability_minutes == 10.0
        assert manager.config.zero_probability_minutes == 60.0

    def test_get_parsing_probability_fresh(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        media = create_test_media(age_minutes=0.0)
        probability = manager.get_parsing_probability(media)
        assert probability == 1.0

    def test_get_parsing_probability_aged(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        media = create_test_media(age_minutes=120.0)
        probability = manager.get_parsing_probability(media)
        assert probability == 0.0

    def test_should_parse_fresh(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        media = create_test_media(age_minutes=0.0)
        results = [manager.should_parse(media) for _ in range(10)]
        assert all(results)

    def test_should_parse_aged_out(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        media = create_test_media(age_minutes=120.0)
        results = [manager.should_parse(media) for _ in range(10)]
        assert not any(results)

    def test_is_aged_out_fresh(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        media = create_test_media(age_minutes=0.0)
        assert manager.is_aged_out(media) is False

    def test_is_aged_out_old(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        media = create_test_media(age_minutes=100.0)
        assert manager.is_aged_out(media) is True


class TestCreateLifecycleManager:
    """Tests for create_lifecycle_manager factory function."""

    def test_creates_manager_with_defaults(self, tmp_path: Path) -> None:
        manager = create_lifecycle_manager(base_path=tmp_path)
        assert manager.storage.base_path == tmp_path
        assert manager.config.full_probability_minutes == 35.0

    def test_creates_manager_with_config(self, tmp_path: Path) -> None:
        config = DecayConfig(full_probability_minutes=20.0, zero_probability_minutes=40.0)
        manager = create_lifecycle_manager(base_path=tmp_path, config=config)
        assert manager.config.full_probability_minutes == 20.0
        assert manager.config.zero_probability_minutes == 40.0

    def test_creates_directory(self, tmp_path: Path) -> None:
        storage_path = tmp_path / "new_storage"
        assert not storage_path.exists()
        create_lifecycle_manager(base_path=storage_path)
        assert storage_path.exists()


@pytest.mark.asyncio
class TestLifecycleManagerAsync:
    """Async tests for LifecycleManager."""

    async def test_mark_loaded(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        media = create_test_media("mark-loaded-test")
        await storage.save(media)
        assert media.metadata.time_loaded is None
        updated = await manager.mark_loaded(media)
        assert updated.metadata.time_loaded is not None
        loaded = await storage.load("mark-loaded-test")
        assert loaded.metadata.time_loaded is not None

    async def test_mark_parsed(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        media = create_test_media("mark-parsed-test")
        await storage.save(media)
        assert media.metadata.time_parsed is None
        updated = await manager.mark_parsed(media)
        assert updated.metadata.time_parsed is not None
        loaded = await storage.load("mark-parsed-test")
        assert loaded.metadata.time_parsed is not None

    async def test_cleanup_aged_media_empty(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        deleted = await manager.cleanup_aged_media()
        assert deleted == []

    async def test_cleanup_aged_media_removes_old(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        fresh = create_test_media("fresh-media", age_minutes=0.0)
        aged = create_test_media("aged-media", age_minutes=100.0)
        await storage.save(fresh)
        await storage.save(aged)
        deleted = await manager.cleanup_aged_media()
        assert deleted == ["aged-media"]
        assert await storage.exists("fresh-media")
        assert not await storage.exists("aged-media")

    async def test_cleanup_aged_media_multiple(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        await storage.save(create_test_media("fresh", age_minutes=0.0))
        await storage.save(create_test_media("aged-1", age_minutes=100.0))
        await storage.save(create_test_media("aged-2", age_minutes=120.0))
        await storage.save(create_test_media("aged-3", age_minutes=150.0))
        deleted = await manager.cleanup_aged_media()
        assert set(deleted) == {"aged-1", "aged-2", "aged-3"}
        assert await storage.exists("fresh")

    async def test_get_media_status(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        media = create_test_media("status-test", age_minutes=0.0)
        await storage.save(media)
        status = await manager.get_media_status("status-test")
        assert status["media_id"] == "status-test"
        assert status["probability"] == 1.0
        assert status["aged_out"] is False
        assert status["time_saved"] is not None
        assert status["time_loaded"] is None
        assert status["time_parsed"] is None

    async def test_get_media_status_not_found(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        with pytest.raises(FileNotFoundError):
            await manager.get_media_status("nonexistent")


class TestCleanupScheduler:
    """Tests for CleanupScheduler class."""

    def test_init_defaults(self, tmp_path: Path) -> None:
        manager = create_lifecycle_manager(base_path=tmp_path)
        scheduler = CleanupScheduler(lifecycle_manager=manager)
        assert scheduler.lifecycle_manager == manager
        assert scheduler.interval_seconds == 300.0
        assert scheduler.on_cleanup is None
        assert scheduler.is_running is False

    def test_init_custom_interval(self, tmp_path: Path) -> None:
        manager = create_lifecycle_manager(base_path=tmp_path)
        scheduler = CleanupScheduler(lifecycle_manager=manager, interval_seconds=60.0)
        assert scheduler.interval_seconds == 60.0

    def test_init_with_callback(self, tmp_path: Path) -> None:
        manager = create_lifecycle_manager(base_path=tmp_path)
        callback = lambda ids: None
        scheduler = CleanupScheduler(lifecycle_manager=manager, on_cleanup=callback)
        assert scheduler.on_cleanup == callback


@pytest.mark.asyncio
class TestCleanupSchedulerAsync:
    """Async tests for CleanupScheduler."""

    async def test_run_once(self, tmp_path: Path) -> None:
        manager = create_lifecycle_manager(base_path=tmp_path)
        scheduler = CleanupScheduler(lifecycle_manager=manager)
        await manager.storage.save(create_test_media("fresh", age_minutes=0.0))
        await manager.storage.save(create_test_media("aged", age_minutes=100.0))
        deleted = await scheduler.run_once()
        assert deleted == ["aged"]

    async def test_start_stop(self, tmp_path: Path) -> None:
        manager = create_lifecycle_manager(base_path=tmp_path)
        scheduler = CleanupScheduler(lifecycle_manager=manager, interval_seconds=0.1)
        assert scheduler.is_running is False
        scheduler.start()
        assert scheduler.is_running is True
        await scheduler.stop()
        assert scheduler.is_running is False

    async def test_start_idempotent(self, tmp_path: Path) -> None:
        manager = create_lifecycle_manager(base_path=tmp_path)
        scheduler = CleanupScheduler(lifecycle_manager=manager, interval_seconds=1.0)
        scheduler.start()
        scheduler.start()
        assert scheduler.is_running is True
        await scheduler.stop()

    async def test_stop_idempotent(self, tmp_path: Path) -> None:
        manager = create_lifecycle_manager(base_path=tmp_path)
        scheduler = CleanupScheduler(lifecycle_manager=manager, interval_seconds=1.0)
        await scheduler.stop()
        await scheduler.stop()
        assert scheduler.is_running is False
