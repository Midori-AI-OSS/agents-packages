# midori-ai-media-request Documentation

Type-safe request/response protocol for media parsing in agent systems.

## Overview

This package provides a standardized way for agents to request media with:

- **Type validation**: Ensures requested type matches stored media type
- **Priority-based queuing**: Support for LOW, NORMAL, HIGH, CRITICAL priorities
- **Decay-aware responses**: Respects parsing probability from media lifecycle
- **Clear status tracking**: PENDING, APPROVED, DENIED, PROCESSING, COMPLETED, EXPIRED
- **100% async-friendly implementation**

## Quick Start

```python
from pathlib import Path

from midori_ai_media_lifecycle import create_lifecycle_manager

from midori_ai_media_request import MediaRequest
from midori_ai_media_request import MediaRequestHandler
from midori_ai_media_request import RequestPriority

from midori_ai_media_vault import MediaType


async def example():
    # Create lifecycle manager (handles storage and decay)
    manager = create_lifecycle_manager(base_path=Path("./media_storage"))

    # Create request handler
    handler = MediaRequestHandler(lifecycle_manager=manager)

    # Create a request for media
    request = MediaRequest(
        media_id="photo-001",
        requested_type=MediaType.PHOTO,
        requester_id="agent-123",
        priority=RequestPriority.HIGH,
        reason="User requested photo analysis",
    )

    # Process the request
    response = await handler.request_media(request)

    if response.status == RequestStatus.COMPLETED:
        # Access decrypted content
        content = response.decrypted_content
        print(f"Got {len(content)} bytes of content")
    else:
        # Handle denial or expiration
        print(f"Request {response.status.value}: {response.denial_reason}")
```

## Request/Response Flow

The media request flow follows these steps:

1. **Agent creates MediaRequest** with `media_id`, `requested_type`, `requester_id`
2. **Handler loads media** from storage
3. **Type validation**: If `requested_type != media.media_type`, return DENIED
4. **Decay check**: If `is_aged_out()`, return EXPIRED
5. **Probability check**: If `should_parse()` returns False, return DENIED with probability
6. **Success**: Decrypt content, update parsed timestamp, return COMPLETED with content

## Data Models

### RequestPriority

Enum for request priority levels:

```python
from midori_ai_media_request import RequestPriority

RequestPriority.LOW       # "low"
RequestPriority.NORMAL    # "normal" (default)
RequestPriority.HIGH      # "high"
RequestPriority.CRITICAL  # "critical"
```

### RequestStatus

Enum for request status:

```python
from midori_ai_media_request import RequestStatus

RequestStatus.PENDING     # "pending" - Request received, not yet processed
RequestStatus.APPROVED    # "approved" - Request approved, awaiting processing
RequestStatus.DENIED      # "denied" - Request denied (type mismatch, probability)
RequestStatus.PROCESSING  # "processing" - Request being processed
RequestStatus.COMPLETED   # "completed" - Request fulfilled, content available
RequestStatus.EXPIRED     # "expired" - Media has aged out
```

### MediaRequest

Request model for media parsing:

```python
from midori_ai_media_request import MediaRequest
from midori_ai_media_request import RequestPriority

from midori_ai_media_vault import MediaType

request = MediaRequest(
    media_id="photo-001",           # Required: ID of media to request
    requested_type=MediaType.PHOTO, # Required: Expected media type
    requester_id="agent-123",       # Required: ID of requesting agent
    priority=RequestPriority.HIGH,  # Optional: Priority level (default: NORMAL)
    reason="Analysis needed",       # Optional: Reason for request
)

# Auto-populated fields:
# - request_time: datetime (current UTC time)
```

### MediaResponse

Response model for media requests:

```python
from midori_ai_media_request import MediaResponse
from midori_ai_media_request import RequestStatus

from midori_ai_media_vault import MediaType

# Successful response
response = MediaResponse(
    request_id="req-uuid-001",          # Unique request identifier
    media_id="photo-001",               # Requested media ID
    status=RequestStatus.COMPLETED,     # Request status
    decrypted_content=b"image bytes",   # Decrypted content (COMPLETED only)
    media_type=MediaType.PHOTO,         # Actual media type
    parsing_probability=1.0,            # Current parsing probability
)

# Denied response
response = MediaResponse(
    request_id="req-uuid-002",
    media_id="photo-002",
    status=RequestStatus.DENIED,
    denial_reason="Type mismatch: requested video, found photo",
    media_type=MediaType.PHOTO,
    parsing_probability=0.8,
)

# Expired response
response = MediaResponse(
    request_id="req-uuid-003",
    media_id="photo-003",
    status=RequestStatus.EXPIRED,
    denial_reason="Media has aged out",
    parsing_probability=0.0,
)
```

## Request Handler

### MediaRequestHandler

The default implementation of media request handling:

```python
from pathlib import Path

from midori_ai_media_lifecycle import create_lifecycle_manager

from midori_ai_media_request import MediaRequestHandler


# Create handler with lifecycle manager
manager = create_lifecycle_manager(base_path=Path("./media"))
handler = MediaRequestHandler(lifecycle_manager=manager)
```

### Methods

#### request_media(request)

Process a media request:

```python
from midori_ai_media_request import MediaRequest
from midori_ai_media_request import RequestStatus

from midori_ai_media_vault import MediaType


request = MediaRequest(
    media_id="photo-001",
    requested_type=MediaType.PHOTO,
    requester_id="agent-123",
)
response = await handler.request_media(request)

if response.status == RequestStatus.COMPLETED:
    content = response.decrypted_content
    # Process content...
elif response.status == RequestStatus.DENIED:
    print(f"Denied: {response.denial_reason}")
elif response.status == RequestStatus.EXPIRED:
    print(f"Expired: {response.denial_reason}")
```

#### get_request_status(request_id)

Get status of a previous request:

```python
try:
    response = await handler.get_request_status("req-uuid-001")
    print(f"Status: {response.status.value}")
except KeyError:
    print("Request not found")
```

#### cancel_request(request_id)

Cancel a pending request:

```python
cancelled = await handler.cancel_request("req-uuid-001")
if cancelled:
    print("Request cancelled")
else:
    print("Request not found or already processed")
```

#### list_ids_by_type(media_type, requester_id)

List all media IDs of a specific type for batch operations:

```python
from midori_ai_media_vault import MediaType


# Get all photo IDs
photo_ids = await handler.list_ids_by_type(MediaType.PHOTO, requester_id="agent-123")

# Get all audio IDs for transcription batch
audio_ids = await handler.list_ids_by_type(MediaType.AUDIO, requester_id="agent-123")

# Loop over and process each
for photo_id in photo_ids:
    request = MediaRequest(
        media_id=photo_id,
        requested_type=MediaType.PHOTO,
        requester_id="agent-123"
    )
    response = await handler.request_media(request)
    if response.status == RequestStatus.COMPLETED:
        # Process photo content
        process_photo(response.decrypted_content)
```

**Performance Note**: This method loads and decrypts each media file to check its type. For large collections, this may be slow. Consider caching results if used frequently.

## Custom Protocol Implementation

You can create custom handlers by implementing the `MediaRequestProtocol`:

```python
from midori_ai_media_request import MediaRequest
from midori_ai_media_request import MediaRequestProtocol
from midori_ai_media_request import MediaResponse
from midori_ai_media_request import RequestStatus


class QueuedMediaRequestHandler(MediaRequestProtocol):
    """Custom handler with request queueing."""

    async def request_media(self, request: MediaRequest) -> MediaResponse:
        # Add to queue for async processing
        request_id = await self._add_to_queue(request)
        return MediaResponse(
            request_id=request_id,
            media_id=request.media_id,
            status=RequestStatus.PENDING,
        )

    async def get_request_status(self, request_id: str) -> MediaResponse:
        # Check queue status
        return await self._check_queue_status(request_id)

    async def cancel_request(self, request_id: str) -> bool:
        # Remove from queue
        return await self._remove_from_queue(request_id)
```

## Integration with Media Packages

This package integrates with:

- **midori-ai-media-vault**: Storage and encryption (provides MediaObject, MediaType, MediaCrypto)
- **midori-ai-media-lifecycle**: Decay management (provides LifecycleManager, should_parse, is_aged_out)

### Complete Example

```python
from pathlib import Path

from midori_ai_media_lifecycle import CleanupScheduler
from midori_ai_media_lifecycle import DecayConfig
from midori_ai_media_lifecycle import LifecycleManager

from midori_ai_media_request import MediaRequest
from midori_ai_media_request import MediaRequestHandler
from midori_ai_media_request import RequestPriority
from midori_ai_media_request import RequestStatus

from midori_ai_media_vault import MediaCrypto
from midori_ai_media_vault import MediaMetadata
from midori_ai_media_vault import MediaObject
from midori_ai_media_vault import MediaStorage
from midori_ai_media_vault import MediaType


async def full_workflow():
    # Setup storage and lifecycle
    storage = MediaStorage(base_path=Path("./media"))
    config = DecayConfig(full_probability_minutes=35.0, zero_probability_minutes=90.0)
    manager = LifecycleManager(storage=storage, config=config)

    # Create request handler
    handler = MediaRequestHandler(lifecycle_manager=manager)

    # Store some media
    content = b"image data..."
    encrypted, key, hash_str = MediaCrypto.encrypt(content)
    media = MediaObject(
        id="img-001",
        media_type=MediaType.PHOTO,
        metadata=MediaMetadata(content_hash=hash_str),
        user_id="user-123",
        encrypted_content=encrypted,
        encryption_key=key,
        content_integrity_hash=hash_str,
    )
    await storage.save(media)

    # Request the media
    request = MediaRequest(
        media_id="img-001",
        requested_type=MediaType.PHOTO,
        requester_id="agent-456",
        priority=RequestPriority.NORMAL,
    )
    response = await handler.request_media(request)

    if response.status == RequestStatus.COMPLETED:
        # Decrypted content is ready
        assert response.decrypted_content == content
        print(f"Successfully retrieved {len(response.decrypted_content)} bytes")
    elif response.status == RequestStatus.DENIED:
        print(f"Request denied: {response.denial_reason}")
        print(f"Parsing probability was: {response.parsing_probability:.1%}")
    elif response.status == RequestStatus.EXPIRED:
        print(f"Media expired: {response.denial_reason}")

    # Start background cleanup
    scheduler = CleanupScheduler(lifecycle_manager=manager, interval_seconds=300.0)
    scheduler.start()

    # ... application runs ...

    # Cleanup on shutdown
    await scheduler.stop()
```

## Error Handling

```python
from midori_ai_media_request import MediaRequest
from midori_ai_media_request import RequestStatus

from midori_ai_media_vault import MediaType


# Handle different response statuses
request = MediaRequest(
    media_id="photo-001",
    requested_type=MediaType.PHOTO,
    requester_id="agent-123",
)
response = await handler.request_media(request)

match response.status:
    case RequestStatus.COMPLETED:
        process_content(response.decrypted_content)
    case RequestStatus.DENIED:
        log_denial(response.denial_reason, response.parsing_probability)
    case RequestStatus.EXPIRED:
        log_expiration(response.denial_reason)
    case _:
        log_unexpected_status(response.status)
```

## Best Practices

1. **Check status before accessing content**: Always verify `status == COMPLETED` before using `decrypted_content`.

2. **Log denial reasons**: Track why requests fail to identify patterns or issues.

3. **Use appropriate priorities**: Reserve CRITICAL for time-sensitive operations.

4. **Include request reasons**: Helps with debugging and audit trails.

5. **Handle all statuses**: Don't assume success - always handle DENIED and EXPIRED cases.

## Type Validation

The handler enforces type matching between requested type and stored type:

```python
# This will be DENIED if media is actually VIDEO
request = MediaRequest(
    media_id="media-001",
    requested_type=MediaType.PHOTO,  # Must match stored type
    requester_id="agent-123",
)
response = await handler.request_media(request)

if response.status == RequestStatus.DENIED:
    # Response includes actual media type
    print(f"Expected {request.requested_type.value}, found {response.media_type.value}")
```
