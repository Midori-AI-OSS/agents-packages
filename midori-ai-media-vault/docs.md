# midori-ai-media-vault Documentation

Encrypted media storage with Pydantic models for agent systems.

## Overview

This package provides secure media storage capabilities for agent systems, featuring:

- **Pydantic-based serialization** for type safety and validation
- **Per-file random Fernet encryption keys** stored alongside encrypted content
- **Onion/layered encryption**: Storage layer adds system-stats-derived encryption
- **Integrity verification** via SHA-256 hash of decrypted content
- **Support for multiple media types**: photos, videos, audio, text
- **100% async-friendly implementation**

## Quick Start

```python
import uuid

from pathlib import Path

from midori_ai_media_vault import MediaCrypto
from midori_ai_media_vault import MediaMetadata
from midori_ai_media_vault import MediaObject
from midori_ai_media_vault import MediaStorage
from midori_ai_media_vault import MediaType


async def example():
    # Create storage
    storage = MediaStorage(base_path=Path("./media_storage"))

    # Encrypt content with random key
    content = b"photo bytes here..."
    encrypted_content, encryption_key, integrity_hash = MediaCrypto.encrypt(content)

    # Create media object
    media = MediaObject(
        id=str(uuid.uuid4()),
        media_type=MediaType.PHOTO,
        metadata=MediaMetadata(content_hash=integrity_hash),
        user_id="user_12345",
        encrypted_content=encrypted_content,
        encryption_key=encryption_key,
        content_integrity_hash=integrity_hash,
    )

    # Save to disk
    await storage.save(media)

    # Load and decrypt
    loaded_media = await storage.load(media.id)
    decrypted = MediaCrypto.decrypt(
        loaded_media.encrypted_content,
        loaded_media.encryption_key,
        loaded_media.content_integrity_hash,
    )
    assert decrypted == content
```

## Data Models

### MediaType

Enum for supported media types:

```python
from midori_ai_media_vault import MediaType

MediaType.PHOTO  # "photo"
MediaType.VIDEO  # "video"
MediaType.AUDIO  # "audio"
MediaType.TEXT   # "text"
```

### MediaMetadata

Metadata tracking for media objects:

```python
from midori_ai_media_vault import MediaMetadata

metadata = MediaMetadata(
    content_hash="sha256-hash-of-raw-content",
)

# Auto-populated fields:
# - time_saved: datetime (default: now)
# - time_loaded: Optional[datetime]
# - time_parsed: Optional[datetime]
```

**Note:** Lifecycle management (ageout, decay) is handled by the `midori-ai-media-lifecycle` package, not the vault.

### MediaObject

Core media object with encrypted content:

```python
from midori_ai_media_vault import MediaObject

media = MediaObject(
    id="unique-media-id",
    media_type=MediaType.PHOTO,
    metadata=MediaMetadata(content_hash="..."),
    user_id="owner-user-id",
    encrypted_content=b"encrypted-bytes",
    encryption_key=b"fernet-key",
    content_integrity_hash="sha256-of-decrypted-content",
)
```

## Encryption

### MediaCrypto

Static methods for per-file encryption:

```python
from midori_ai_media_vault import MediaCrypto

# Encrypt data with a new random key
encrypted, key, hash = MediaCrypto.encrypt(b"raw content")

# Decrypt data and verify integrity
decrypted = MediaCrypto.decrypt(encrypted, key, hash)
```

### Encryption Approach

- Each media file uses a **unique random Fernet key**
- The key is stored in the Pydantic model alongside encrypted content
- Integrity is verified via SHA-256 hash on decrypt
- No key derivation complexity - keys are randomly generated

## Storage

### MediaStorage

Async disk storage with Pydantic JSON serialization and onion encryption:

```python
from pathlib import Path

from midori_ai_media_vault import MediaStorage

# Initialize storage (uses system-stats encryption by default with 12 iterations)
storage = MediaStorage(base_path=Path("./media_storage"))

# Custom iterations for key derivation
storage = MediaStorage(base_path=Path("./media_storage"), system_key_iterations=12)

# Save media (writes encrypted to {base_path}/{id}.media)
await storage.save(media)

# Load media by ID
loaded = await storage.load("media-id")

# Delete media
deleted = await storage.delete("media-id")  # Returns True if deleted

# Check if media exists
exists = await storage.exists("media-id")

# List all media IDs
ids = await storage.list_all()

# List media IDs filtered by type
photo_ids = await storage.list_by_type(MediaType.PHOTO)
audio_ids = await storage.list_by_type(MediaType.AUDIO)
```

#### list_by_type Performance Note

The `list_by_type()` method is optimized to simply list files in the type-specific folder (e.g., `photo/`, `video/`), without needing to load or decrypt any files. This makes it very fast even for large collections.

```python
# Fast operation - just lists folder contents
photo_ids = await storage.list_by_type(MediaType.PHOTO)
for photo_id in photo_ids:
    media = await storage.load(photo_id)
    # Process media...
```

### Storage Format and Folder Structure

Media objects are organized into type-specific subfolders for optimized filtering:

```
base_path/
├── photo/
│   ├── photo-1.media
│   └── photo-2.media
├── video/
│   └── video-1.media
├── audio/
│   └── audio-1.media
└── text/
    └── text-1.media
```

Each `.media` file contains the serialized MediaObject JSON encrypted using a system-stats-derived key.

### Onion/Layered Encryption

The storage uses two layers of encryption (like Tor/onion routing):

1. **Inner layer**: Media content is encrypted with a per-file random Fernet key (stored in MediaObject)
2. **Outer layer**: The entire MediaObject JSON is encrypted with a system-stats-derived key when saving

This provides defense-in-depth: even if storage files are copied to another system, they cannot be decrypted without matching system stats.

### SystemCrypto

The system-stats encryption uses stable hardware characteristics that are unlikely to change over 90 minutes:

```python
from midori_ai_media_vault import SystemCrypto, get_system_stats, derive_system_key

# Get raw system stats string
stats = get_system_stats()
# Returns: "total_memory|cpu_count|processor|machine|system"

# Derive a Fernet key from system stats
key = derive_system_key(iterations=12)  # 12 SHA-256 iterations

# Use SystemCrypto directly
crypto = SystemCrypto(iterations=12)
encrypted = crypto.encrypt(b"data")
decrypted = crypto.decrypt(encrypted)
```

System stats collected:
- Total memory (NOT free/used memory)
- CPU count (logical)
- CPU processor/name
- Machine architecture
- Operating system

## Best Practices

1. **Always verify integrity**: Use `MediaCrypto.decrypt()` which automatically verifies the hash.

2. **Store encryption keys securely**: While keys are stored with the data for simplicity, consider additional security measures for production.

3. **Use async operations**: All storage operations are async-friendly for non-blocking I/O.

4. **Manage lifecycle externally**: This package handles storage only. Use `midori-ai-media-lifecycle` to configure retention policies and cleanup schedules.

## Error Handling

```python
from midori_ai_media_vault import MediaCrypto

try:
    decrypted = MediaCrypto.decrypt(encrypted, key, expected_hash)
except ValueError as e:
    # Content integrity check failed - data may be corrupted
    print(f"Integrity error: {e}")
```

## Integration with Other Packages

This package is designed as the foundation for the media storage family:

- **midori-ai-media-lifecycle**: Time-based decay and parsing scheduler (depends on this package)
- **midori-ai-media-request**: Type-safe request/response interface for agents (depends on this package)
