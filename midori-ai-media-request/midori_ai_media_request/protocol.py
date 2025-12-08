"""Abstract base class defining the media request handler protocol."""

from abc import ABC
from abc import abstractmethod

from midori_ai_media_vault import MediaType

from .models import MediaRequest
from .models import MediaResponse


class MediaRequestProtocol(ABC):
    """Protocol that media request handlers must implement.

    IMPORTANT: All methods MUST be async-friendly. Use async/await throughout.
    """

    @abstractmethod
    async def request_media(self, request: MediaRequest) -> MediaResponse:
        """Process a media request and return a response.

        This method should:
        1. Load media from storage
        2. Validate type matches requested_type
        3. Check if media is aged out
        4. Check parsing probability
        5. Decrypt content if all checks pass
        6. Update parsed timestamp

        Args:
            request: The MediaRequest containing media_id, requested_type, etc.

        Returns:
            MediaResponse with status and optional decrypted_content.
        """
        ...

    @abstractmethod
    async def get_request_status(self, request_id: str) -> MediaResponse:
        """Get the status of a previous request.

        Args:
            request_id: The unique identifier of the request.

        Returns:
            MediaResponse with current status.
        """
        ...

    @abstractmethod
    async def cancel_request(self, request_id: str) -> bool:
        """Cancel a pending request.

        Args:
            request_id: The unique identifier of the request to cancel.

        Returns:
            True if cancelled, False if request not found or already processed.
        """
        ...

    @abstractmethod
    async def list_ids_by_type(self, media_type: MediaType, requester_id: str) -> list[str]:
        """List all media IDs of a specific type.

        This enables developers to:
        1. Get all photo IDs, then loop and process each
        2. Get all audio IDs for transcription batch
        3. Filter media by type for their parsing systems

        Args:
            media_type: The type of media to list
            requester_id: ID of the agent/user making the request (reserved for future access control/audit logging)

        Returns:
            List of media IDs that match the type
        """
        ...
