"""Pydantic models for media storage."""

from datetime import datetime
from datetime import timezone
from enum import Enum

from typing import Optional

from pydantic import BaseModel
from pydantic import Field


def utcnow() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class MediaType(str, Enum):
    """Supported media types."""

    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"


class MediaMetadata(BaseModel):
    """Metadata tracking for media objects."""

    time_saved: datetime = Field(default_factory=utcnow)
    time_loaded: Optional[datetime] = None
    time_parsed: Optional[datetime] = None
    content_hash: str = Field(..., description="SHA-256 hash of raw content for integrity")


class MediaObject(BaseModel):
    """Core media object with encrypted content and per-file random key."""

    id: str = Field(..., description="Unique media identifier")
    media_type: MediaType
    metadata: MediaMetadata
    user_id: str = Field(..., description="Owner user ID")
    encrypted_content: bytes = Field(..., description="Encrypted media bytes")
    encryption_key: bytes = Field(..., description="Random Fernet key for this file")
    content_integrity_hash: str = Field(..., description="SHA-256 hash of decrypted content for verification")
