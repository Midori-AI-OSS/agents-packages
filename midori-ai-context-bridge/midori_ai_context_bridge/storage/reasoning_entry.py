"""ReasoningEntry model for context bridge.

This module provides the ReasoningEntry model that wraps VectorEntry objects
with reasoning-specific fields and behavior.
"""

import time

from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from midori_ai_vector_manager import VectorEntry

from ..config import ModelType


class ReasoningEntry(BaseModel):
    """Extended entry with reasoning-specific fields and multiple vector entries.

    Attributes:
        model_type: Type of model (preprocessing or working_awareness)
        entries: List of vector entries for flexibility
    """

    model_type: ModelType
    entries: list[VectorEntry] = Field(default_factory=list)

    def add_entry(self, entry: VectorEntry) -> None:
        """Add a vector entry to this reasoning context.

        Args:
            entry: VectorEntry to add
        """
        self.entries.append(entry)

    def get_entries(self) -> list[VectorEntry]:
        """Get all vector entries.

        Returns:
            List of all vector entries
        """
        return self.entries

    @property
    def age_minutes(self) -> float:
        """Return age of oldest entry in minutes.

        Returns:
            Age in minutes, 0.0 if no entries
        """
        if not self.entries:
            return 0.0
        oldest = min(e.timestamp for e in self.entries)
        return (time.time() - oldest) / 60.0

    @property
    def id(self) -> Optional[str]:
        """Return ID of first entry if exists.

        Returns:
            ID of first entry or None
        """
        first_entry = self.entries[0] if len(self.entries) > 0 else None
        return first_entry.id if first_entry else None

    @property
    def session_id(self) -> Optional[str]:
        """Return session_id from metadata of first entry if exists.

        Returns:
            Session ID from metadata or None
        """
        first_entry = self.entries[0] if len(self.entries) > 0 else None
        return first_entry.metadata.get("session_id") if first_entry else None

    @property
    def text(self) -> str:
        """Return concatenated text from all entries.

        Returns:
            Combined text from all entries
        """
        return " ".join(e.text for e in self.entries)

    @property
    def timestamp(self) -> float:
        """Return timestamp of oldest entry.

        Returns:
            Timestamp of oldest entry, 0.0 if no entries
        """
        if not self.entries:
            return 0.0
        return min(e.timestamp for e in self.entries)

    @property
    def metadata(self) -> dict[str, Any]:
        """Return combined metadata from all entries.

        Returns:
            Merged metadata from all entries
        """
        combined: dict[str, Any] = {}
        for entry in self.entries:
            combined.update(entry.metadata)
        return combined
