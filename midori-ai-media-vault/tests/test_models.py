"""Tests for Pydantic models."""

from datetime import datetime
from datetime import timezone

from midori_ai_media_vault import MediaMetadata
from midori_ai_media_vault import MediaObject
from midori_ai_media_vault import MediaType


class TestMediaType:
    """Tests for MediaType enum."""

    def test_all_types_exist(self) -> None:
        assert MediaType.PHOTO == "photo"
        assert MediaType.VIDEO == "video"
        assert MediaType.AUDIO == "audio"
        assert MediaType.TEXT == "text"

    def test_type_is_string(self) -> None:
        assert isinstance(MediaType.PHOTO.value, str)
        assert isinstance(MediaType.VIDEO.value, str)


class TestMediaMetadata:
    """Tests for MediaMetadata model."""

    def test_required_content_hash(self) -> None:
        metadata = MediaMetadata(content_hash="abc123")
        assert metadata.content_hash == "abc123"

    def test_default_values(self) -> None:
        metadata = MediaMetadata(content_hash="abc123")
        assert metadata.time_loaded is None
        assert metadata.time_parsed is None
        assert isinstance(metadata.time_saved, datetime)

    def test_time_saved_is_utc(self) -> None:
        metadata = MediaMetadata(content_hash="abc123")
        assert metadata.time_saved.tzinfo is not None

    def test_optional_times(self) -> None:
        now = datetime.now(timezone.utc)
        metadata = MediaMetadata(content_hash="abc123", time_loaded=now, time_parsed=now)
        assert metadata.time_loaded == now
        assert metadata.time_parsed == now


class TestMediaObject:
    """Tests for MediaObject model."""

    def test_create_media_object(self) -> None:
        metadata = MediaMetadata(content_hash="abc123")
        media = MediaObject(
            id="media-001",
            media_type=MediaType.PHOTO,
            metadata=metadata,
            user_id="user-123",
            encrypted_content=b"encrypted",
            encryption_key=b"key12345",
            content_integrity_hash="hash123",
        )
        assert media.id == "media-001"
        assert media.media_type == MediaType.PHOTO
        assert media.user_id == "user-123"
        assert media.encrypted_content == b"encrypted"
        assert media.encryption_key == b"key12345"
        assert media.content_integrity_hash == "hash123"

    def test_all_media_types(self) -> None:
        metadata = MediaMetadata(content_hash="abc123")
        for media_type in MediaType:
            media = MediaObject(
                id="test-id",
                media_type=media_type,
                metadata=metadata,
                user_id="user",
                encrypted_content=b"data",
                encryption_key=b"key",
                content_integrity_hash="hash",
            )
            assert media.media_type == media_type

    def test_serialization_roundtrip(self) -> None:
        metadata = MediaMetadata(content_hash="abc123")
        media = MediaObject(
            id="media-002",
            media_type=MediaType.VIDEO,
            metadata=metadata,
            user_id="user-456",
            encrypted_content=b"video-data",
            encryption_key=b"video-key",
            content_integrity_hash="video-hash",
        )
        json_str = media.model_dump_json()
        loaded = MediaObject.model_validate_json(json_str)
        assert loaded.id == media.id
        assert loaded.media_type == media.media_type
        assert loaded.user_id == media.user_id
        assert loaded.encrypted_content == media.encrypted_content
        assert loaded.encryption_key == media.encryption_key
        assert loaded.content_integrity_hash == media.content_integrity_hash
        assert loaded.metadata.content_hash == media.metadata.content_hash
