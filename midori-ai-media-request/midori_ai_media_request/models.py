"""Pydantic models for media request/response protocol."""

from datetime import datetime
from datetime import timezone
from enum import Enum

from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from midori_ai_media_vault import MediaType


def utcnow() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class RequestPriority(str, Enum):
    """Priority levels for media requests."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class RequestStatus(str, Enum):
    """Status of a media request."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    PROCESSING = "processing"
    COMPLETED = "completed"
    EXPIRED = "expired"


class MediaRequest(BaseModel):
    """Request model for media parsing."""

    media_id: str = Field(..., description="Unique identifier of the media to request")
    requested_type: MediaType = Field(..., description="Expected type of the media")
    requester_id: str = Field(..., description="ID of the agent/user requesting the media")
    priority: RequestPriority = Field(default=RequestPriority.NORMAL, description="Priority of the request")
    request_time: datetime = Field(default_factory=utcnow, description="When the request was made")
    reason: Optional[str] = Field(default=None, description="Optional reason for the request")


class MediaResponse(BaseModel):
    """Response model for media requests."""

    request_id: str = Field(..., description="Unique identifier for this request/response")
    media_id: str = Field(..., description="ID of the requested media")
    status: RequestStatus = Field(..., description="Status of the request")
    decrypted_content: Optional[bytes] = Field(default=None, description="Decrypted media content when COMPLETED")
    parsing_probability: Optional[float] = Field(default=None, description="Current parsing probability (0.0-1.0)")
    denial_reason: Optional[str] = Field(default=None, description="Reason for denial when DENIED or EXPIRED")
    media_type: Optional[MediaType] = Field(default=None, description="Type of the media")
    response_time: datetime = Field(default_factory=utcnow, description="When the response was generated")
