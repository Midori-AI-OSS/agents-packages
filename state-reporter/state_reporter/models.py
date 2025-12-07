"""Pydantic models for service state reporting."""

from typing import Any
from typing import Dict
from typing import Optional

from pydantic import BaseModel

from .enums import ServiceStatus


class ServiceState(BaseModel):
    """Model representing a service's current state."""

    service: str
    status: ServiceStatus
    metadata: Optional[Dict[str, Any]] = None

    def to_json(self) -> dict:
        """Convert to JSON-serializable dict for API calls."""
        return self.model_dump(mode="json")
