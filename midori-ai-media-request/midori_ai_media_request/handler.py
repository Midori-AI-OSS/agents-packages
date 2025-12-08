"""Default implementation of the media request handler."""

import uuid

from midori_ai_media_lifecycle import LifecycleManager

from midori_ai_media_vault import MediaCrypto
from midori_ai_media_vault import MediaType

from .models import MediaRequest
from .models import MediaResponse
from .models import RequestStatus

from .protocol import MediaRequestProtocol


class MediaRequestHandler(MediaRequestProtocol):
    """Default implementation of media request handling.

    Uses LifecycleManager for storage access and decay checking,
    MediaCrypto for content decryption.
    """

    def __init__(self, lifecycle_manager: LifecycleManager) -> None:
        """Initialize the handler with a lifecycle manager.

        Args:
            lifecycle_manager: LifecycleManager instance for storage and decay operations.
        """
        self.lifecycle_manager = lifecycle_manager
        self._pending_requests: dict[str, MediaResponse] = {}

    async def request_media(self, request: MediaRequest) -> MediaResponse:
        """Process a media request following the validation flow.

        Flow:
        1. Load media from storage
        2. Type validation: If requested_type != media.media_type, return DENIED
        3. Decay check: If is_aged_out(), return EXPIRED
        4. Probability check: If should_parse() returns False, return DENIED with probability
        5. Success: Decrypt content, update parsed timestamp, return COMPLETED with content

        Args:
            request: The MediaRequest to process.

        Returns:
            MediaResponse with appropriate status and content.
        """
        request_id = str(uuid.uuid4())
        try:
            media = await self.lifecycle_manager.storage.load(request.media_id)
        except FileNotFoundError:
            response = MediaResponse(request_id=request_id, media_id=request.media_id, status=RequestStatus.DENIED, denial_reason="Media not found")
            return response

        probability = self.lifecycle_manager.get_parsing_probability(media)

        if request.requested_type != media.media_type:
            response = MediaResponse(request_id=request_id, media_id=request.media_id, status=RequestStatus.DENIED, denial_reason=f"Type mismatch: requested {request.requested_type.value}, found {media.media_type.value}", media_type=media.media_type, parsing_probability=probability)
            return response

        if self.lifecycle_manager.is_aged_out(media):
            response = MediaResponse(request_id=request_id, media_id=request.media_id, status=RequestStatus.EXPIRED, denial_reason="Media has aged out", media_type=media.media_type, parsing_probability=probability)
            return response

        if not self.lifecycle_manager.should_parse(media):
            response = MediaResponse(request_id=request_id, media_id=request.media_id, status=RequestStatus.DENIED, denial_reason=f"Parsing probability check failed (probability: {probability:.1%})", media_type=media.media_type, parsing_probability=probability)
            return response

        decrypted_content = MediaCrypto.decrypt(media.encrypted_content, media.encryption_key, media.content_integrity_hash)

        await self.lifecycle_manager.mark_parsed(media)

        response = MediaResponse(request_id=request_id, media_id=request.media_id, status=RequestStatus.COMPLETED, decrypted_content=decrypted_content, media_type=media.media_type, parsing_probability=probability)

        return response

    async def get_request_status(self, request_id: str) -> MediaResponse:
        """Get the status of a previous request.

        Note: This implementation only tracks pending requests in memory.
        Completed requests are not stored.

        Args:
            request_id: The unique identifier of the request.

        Returns:
            MediaResponse with current status.

        Raises:
            KeyError: If request_id is not found.
        """
        if request_id not in self._pending_requests:
            raise KeyError(f"Request {request_id} not found")
        return self._pending_requests[request_id]

    async def cancel_request(self, request_id: str) -> bool:
        """Cancel a pending request.

        Args:
            request_id: The unique identifier of the request to cancel.

        Returns:
            True if cancelled, False if request not found or already processed.
        """
        if request_id not in self._pending_requests:
            return False
        response = self._pending_requests[request_id]
        if response.status not in (RequestStatus.PENDING, RequestStatus.PROCESSING):
            return False
        del self._pending_requests[request_id]
        return True

    async def list_ids_by_type(self, media_type: MediaType, requester_id: str) -> list[str]:
        """List all media IDs of a specific type for batch operations.

        This enables developers to:
        1. Get all photo IDs, then loop and process each
        2. Get all audio IDs for transcription batch
        3. Filter media by type for their parsing systems

        NOTE: This method loads and decrypts each media file to check its type.
        For large collections, this may be slow. Consider caching results if
        used frequently.

        Args:
            media_type: The type of media to list
            requester_id: ID of the agent/user making the request (reserved for future access control/audit logging)

        Returns:
            List of media IDs that match the type
        """
        return await self.lifecycle_manager.storage.list_by_type(media_type)
