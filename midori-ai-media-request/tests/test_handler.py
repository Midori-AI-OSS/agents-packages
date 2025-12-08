"""Tests for media request handler."""

import pytest

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from pathlib import Path

from midori_ai_media_lifecycle import DecayConfig
from midori_ai_media_lifecycle import LifecycleManager

from midori_ai_media_request import MediaRequest
from midori_ai_media_request import MediaRequestHandler
from midori_ai_media_request import RequestStatus

from midori_ai_media_vault import MediaCrypto
from midori_ai_media_vault import MediaMetadata
from midori_ai_media_vault import MediaObject
from midori_ai_media_vault import MediaStorage
from midori_ai_media_vault import MediaType


def create_test_media(media_id: str = "test-media", media_type: MediaType = MediaType.PHOTO, age_minutes: float = 0.0) -> MediaObject:
    """Create a test MediaObject with optional age and type."""
    content = b"test content"
    encrypted, key, hash_str = MediaCrypto.encrypt(content)
    time_saved = datetime.now(timezone.utc) - timedelta(minutes=age_minutes)
    metadata = MediaMetadata(content_hash=hash_str, time_saved=time_saved)
    return MediaObject(id=media_id, media_type=media_type, metadata=metadata, user_id="user-123", encrypted_content=encrypted, encryption_key=key, content_integrity_hash=hash_str)


class TestMediaRequestHandler:
    """Tests for MediaRequestHandler class."""

    def test_init(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        handler = MediaRequestHandler(lifecycle_manager=manager)
        assert handler.lifecycle_manager == manager


@pytest.mark.asyncio
class TestMediaRequestHandlerAsync:
    """Async tests for MediaRequestHandler."""

    async def test_request_media_success(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        handler = MediaRequestHandler(lifecycle_manager=manager)
        media = create_test_media("success-test", MediaType.PHOTO, age_minutes=0.0)
        await storage.save(media)
        request = MediaRequest(media_id="success-test", requested_type=MediaType.PHOTO, requester_id="agent-001")
        response = await handler.request_media(request)
        assert response.status == RequestStatus.COMPLETED
        assert response.decrypted_content == b"test content"
        assert response.media_type == MediaType.PHOTO
        assert response.parsing_probability == 1.0

    async def test_request_media_not_found(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        handler = MediaRequestHandler(lifecycle_manager=manager)
        request = MediaRequest(media_id="nonexistent", requested_type=MediaType.PHOTO, requester_id="agent-001")
        response = await handler.request_media(request)
        assert response.status == RequestStatus.DENIED
        assert response.denial_reason == "Media not found"

    async def test_request_media_type_mismatch(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        handler = MediaRequestHandler(lifecycle_manager=manager)
        media = create_test_media("type-test", MediaType.PHOTO, age_minutes=0.0)
        await storage.save(media)
        request = MediaRequest(media_id="type-test", requested_type=MediaType.VIDEO, requester_id="agent-001")
        response = await handler.request_media(request)
        assert response.status == RequestStatus.DENIED
        assert "Type mismatch" in response.denial_reason
        assert "requested video" in response.denial_reason
        assert "found photo" in response.denial_reason
        assert response.media_type == MediaType.PHOTO

    async def test_request_media_expired(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        handler = MediaRequestHandler(lifecycle_manager=manager)
        media = create_test_media("expired-test", MediaType.PHOTO, age_minutes=120.0)
        await storage.save(media)
        request = MediaRequest(media_id="expired-test", requested_type=MediaType.PHOTO, requester_id="agent-001")
        response = await handler.request_media(request)
        assert response.status == RequestStatus.EXPIRED
        assert "aged out" in response.denial_reason
        assert response.parsing_probability == 0.0

    async def test_request_media_updates_parsed_time(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        handler = MediaRequestHandler(lifecycle_manager=manager)
        media = create_test_media("parse-time-test", MediaType.PHOTO, age_minutes=0.0)
        await storage.save(media)
        loaded = await storage.load("parse-time-test")
        assert loaded.metadata.time_parsed is None
        request = MediaRequest(media_id="parse-time-test", requested_type=MediaType.PHOTO, requester_id="agent-001")
        response = await handler.request_media(request)
        assert response.status == RequestStatus.COMPLETED
        loaded = await storage.load("parse-time-test")
        assert loaded.metadata.time_parsed is not None

    async def test_request_all_media_types(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        handler = MediaRequestHandler(lifecycle_manager=manager)
        for media_type in MediaType:
            media = create_test_media(f"{media_type.value}-test", media_type, age_minutes=0.0)
            await storage.save(media)
            request = MediaRequest(media_id=f"{media_type.value}-test", requested_type=media_type, requester_id="agent-001")
            response = await handler.request_media(request)
            assert response.status == RequestStatus.COMPLETED
            assert response.media_type == media_type

    async def test_request_with_custom_decay_config(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        config = DecayConfig(full_probability_minutes=5.0, zero_probability_minutes=10.0)
        manager = LifecycleManager(storage=storage, config=config)
        handler = MediaRequestHandler(lifecycle_manager=manager)
        media = create_test_media("config-test", MediaType.PHOTO, age_minutes=15.0)
        await storage.save(media)
        request = MediaRequest(media_id="config-test", requested_type=MediaType.PHOTO, requester_id="agent-001")
        response = await handler.request_media(request)
        assert response.status == RequestStatus.EXPIRED

    async def test_get_request_status_not_found(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        handler = MediaRequestHandler(lifecycle_manager=manager)
        with pytest.raises(KeyError):
            await handler.get_request_status("nonexistent-request")

    async def test_cancel_request_not_found(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        handler = MediaRequestHandler(lifecycle_manager=manager)
        result = await handler.cancel_request("nonexistent-request")
        assert result is False

    async def test_list_ids_by_type_empty(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        handler = MediaRequestHandler(lifecycle_manager=manager)
        ids = await handler.list_ids_by_type(MediaType.PHOTO, "agent-001")
        assert ids == []

    async def test_list_ids_by_type_returns_matching(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        handler = MediaRequestHandler(lifecycle_manager=manager)
        await storage.save(create_test_media("photo-1", MediaType.PHOTO))
        await storage.save(create_test_media("photo-2", MediaType.PHOTO))
        await storage.save(create_test_media("video-1", MediaType.VIDEO))
        ids = await handler.list_ids_by_type(MediaType.PHOTO, "agent-001")
        assert set(ids) == {"photo-1", "photo-2"}

    async def test_list_ids_by_type_all_types(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        handler = MediaRequestHandler(lifecycle_manager=manager)
        for media_type in MediaType:
            await storage.save(create_test_media(f"{media_type.value}-test", media_type))
        for media_type in MediaType:
            ids = await handler.list_ids_by_type(media_type, "agent-001")
            assert ids == [f"{media_type.value}-test"]

    async def test_list_ids_by_type_no_match(self, tmp_path: Path) -> None:
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        handler = MediaRequestHandler(lifecycle_manager=manager)
        await storage.save(create_test_media("photo-1", MediaType.PHOTO))
        ids = await handler.list_ids_by_type(MediaType.VIDEO, "agent-001")
        assert ids == []

    async def test_list_ids_by_type_batch_workflow(self, tmp_path: Path) -> None:
        """Test the typical batch workflow: list IDs, then process each."""
        storage = MediaStorage(base_path=tmp_path)
        manager = LifecycleManager(storage=storage)
        handler = MediaRequestHandler(lifecycle_manager=manager)
        await storage.save(create_test_media("photo-1", MediaType.PHOTO))
        await storage.save(create_test_media("photo-2", MediaType.PHOTO))
        photo_ids = await handler.list_ids_by_type(MediaType.PHOTO, "agent-001")
        for photo_id in photo_ids:
            request = MediaRequest(media_id=photo_id, requested_type=MediaType.PHOTO, requester_id="agent-001")
            response = await handler.request_media(request)
            assert response.status == RequestStatus.COMPLETED
            assert response.decrypted_content == b"test content"
