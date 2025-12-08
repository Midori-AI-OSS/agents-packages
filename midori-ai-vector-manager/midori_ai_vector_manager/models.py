"""Pydantic models for vector entries."""

import time

from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from .enums import SenderType


class VectorEntry(BaseModel):
    """A stored vector entry with metadata.

    Attributes:
        id: Unique identifier (time-based)
        text: The text content
        timestamp: Unix timestamp when stored
        sender: Optional sender type (user, model, or system) for reranking
        metadata: Additional metadata
    """

    id: str
    text: str
    timestamp: float
    sender: Optional[SenderType] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def age_minutes(self) -> float:
        """Return age of entry in minutes."""
        return (time.time() - self.timestamp) / 60.0

    def to_chromadb_metadata(self) -> dict[str, Any]:
        """Convert to ChromaDB metadata format (sender stored in metadata tag)."""
        meta = self.metadata.copy()
        meta["timestamp"] = self.timestamp
        if self.sender:
            meta["sender"] = self.sender.value
        return meta
