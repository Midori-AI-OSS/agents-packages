"""Tests for Pydantic models."""

from datetime import datetime

from midori_ai_media_request import MediaRequest
from midori_ai_media_request import MediaResponse
from midori_ai_media_request import RequestPriority
from midori_ai_media_request import RequestStatus

from midori_ai_media_vault import MediaType


class TestRequestPriority:
    """Tests for RequestPriority enum."""

    def test_all_priorities_exist(self) -> None:
        assert RequestPriority.LOW == "low"
        assert RequestPriority.NORMAL == "normal"
        assert RequestPriority.HIGH == "high"
        assert RequestPriority.CRITICAL == "critical"

    def test_priority_is_string(self) -> None:
        assert isinstance(RequestPriority.LOW.value, str)
        assert isinstance(RequestPriority.CRITICAL.value, str)


class TestRequestStatus:
    """Tests for RequestStatus enum."""

    def test_all_statuses_exist(self) -> None:
        assert RequestStatus.PENDING == "pending"
        assert RequestStatus.APPROVED == "approved"
        assert RequestStatus.DENIED == "denied"
        assert RequestStatus.PROCESSING == "processing"
        assert RequestStatus.COMPLETED == "completed"
        assert RequestStatus.EXPIRED == "expired"

    def test_status_is_string(self) -> None:
        assert isinstance(RequestStatus.PENDING.value, str)
        assert isinstance(RequestStatus.COMPLETED.value, str)


class TestMediaRequest:
    """Tests for MediaRequest model."""

    def test_create_request(self) -> None:
        request = MediaRequest(media_id="media-001", requested_type=MediaType.PHOTO, requester_id="agent-123")
        assert request.media_id == "media-001"
        assert request.requested_type == MediaType.PHOTO
        assert request.requester_id == "agent-123"

    def test_default_priority(self) -> None:
        request = MediaRequest(media_id="media-001", requested_type=MediaType.PHOTO, requester_id="agent-123")
        assert request.priority == RequestPriority.NORMAL

    def test_custom_priority(self) -> None:
        request = MediaRequest(media_id="media-001", requested_type=MediaType.PHOTO, requester_id="agent-123", priority=RequestPriority.CRITICAL)
        assert request.priority == RequestPriority.CRITICAL

    def test_request_time_auto_set(self) -> None:
        request = MediaRequest(media_id="media-001", requested_type=MediaType.PHOTO, requester_id="agent-123")
        assert isinstance(request.request_time, datetime)
        assert request.request_time.tzinfo is not None

    def test_optional_reason(self) -> None:
        request = MediaRequest(media_id="media-001", requested_type=MediaType.PHOTO, requester_id="agent-123", reason="Urgent processing needed")
        assert request.reason == "Urgent processing needed"

    def test_all_media_types(self) -> None:
        for media_type in MediaType:
            request = MediaRequest(media_id="test-id", requested_type=media_type, requester_id="agent")
            assert request.requested_type == media_type

    def test_serialization_roundtrip(self) -> None:
        request = MediaRequest(media_id="media-002", requested_type=MediaType.VIDEO, requester_id="agent-456", priority=RequestPriority.HIGH, reason="Testing")
        json_str = request.model_dump_json()
        loaded = MediaRequest.model_validate_json(json_str)
        assert loaded.media_id == request.media_id
        assert loaded.requested_type == request.requested_type
        assert loaded.requester_id == request.requester_id
        assert loaded.priority == request.priority
        assert loaded.reason == request.reason


class TestMediaResponse:
    """Tests for MediaResponse model."""

    def test_create_response(self) -> None:
        response = MediaResponse(request_id="req-001", media_id="media-001", status=RequestStatus.COMPLETED)
        assert response.request_id == "req-001"
        assert response.media_id == "media-001"
        assert response.status == RequestStatus.COMPLETED

    def test_completed_with_content(self) -> None:
        response = MediaResponse(request_id="req-001", media_id="media-001", status=RequestStatus.COMPLETED, decrypted_content=b"image data", media_type=MediaType.PHOTO, parsing_probability=1.0)
        assert response.decrypted_content == b"image data"
        assert response.media_type == MediaType.PHOTO
        assert response.parsing_probability == 1.0

    def test_denied_with_reason(self) -> None:
        response = MediaResponse(request_id="req-001", media_id="media-001", status=RequestStatus.DENIED, denial_reason="Type mismatch", parsing_probability=0.8)
        assert response.denial_reason == "Type mismatch"
        assert response.parsing_probability == 0.8
        assert response.decrypted_content is None

    def test_expired_response(self) -> None:
        response = MediaResponse(request_id="req-001", media_id="media-001", status=RequestStatus.EXPIRED, denial_reason="Media has aged out", media_type=MediaType.AUDIO, parsing_probability=0.0)
        assert response.status == RequestStatus.EXPIRED
        assert response.denial_reason == "Media has aged out"

    def test_response_time_auto_set(self) -> None:
        response = MediaResponse(request_id="req-001", media_id="media-001", status=RequestStatus.PENDING)
        assert isinstance(response.response_time, datetime)
        assert response.response_time.tzinfo is not None

    def test_all_statuses(self) -> None:
        for status in RequestStatus:
            response = MediaResponse(request_id="req-001", media_id="media-001", status=status)
            assert response.status == status

    def test_serialization_roundtrip(self) -> None:
        response = MediaResponse(request_id="req-002", media_id="media-002", status=RequestStatus.COMPLETED, decrypted_content=b"video data", media_type=MediaType.VIDEO, parsing_probability=0.75)
        json_str = response.model_dump_json()
        loaded = MediaResponse.model_validate_json(json_str)
        assert loaded.request_id == response.request_id
        assert loaded.media_id == response.media_id
        assert loaded.status == response.status
        assert loaded.decrypted_content == response.decrypted_content
        assert loaded.media_type == response.media_type
        assert loaded.parsing_probability == response.parsing_probability
