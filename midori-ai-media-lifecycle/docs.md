# midori-ai-media-lifecycle Documentation

Time-based lifecycle management for media objects with parsing probability decay and automatic cleanup.

## Overview

This package provides lifecycle management capabilities for media objects, featuring:

- **Time-based parsing probability decay**: Media becomes less likely to be parsed as it ages
- **Configurable decay timeline**: Customize full-probability and zero-probability thresholds via `DecayConfig`
- **Automatic cleanup**: Background scheduler removes aged-out media
- **Lifecycle tracking**: Mark media as loaded/parsed with timestamps
- **100% async-friendly implementation**

**Note:** All lifecycle configuration is managed through `DecayConfig` at the manager level. Individual media objects do not have per-media ageout settings - this ensures consistent lifecycle management across all stored media.

## Quick Start

```python
from pathlib import Path

from midori_ai_media_lifecycle import DecayConfig
from midori_ai_media_lifecycle import LifecycleManager
from midori_ai_media_lifecycle import create_lifecycle_manager

from midori_ai_media_vault import MediaCrypto
from midori_ai_media_vault import MediaMetadata
from midori_ai_media_vault import MediaObject
from midori_ai_media_vault import MediaStorage
from midori_ai_media_vault import MediaType


async def example():
    # Create lifecycle manager with default decay (35 min full, 90 min zero)
    manager = create_lifecycle_manager(base_path=Path("./media_storage"))

    # Or with custom decay config
    config = DecayConfig(full_probability_minutes=30.0, zero_probability_minutes=60.0)
    manager = create_lifecycle_manager(base_path=Path("./media_storage"), config=config)

    # Create and save media object
    content = b"photo bytes here..."
    encrypted, key, hash_str = MediaCrypto.encrypt(content)
    media = MediaObject(
        id="photo-001",
        media_type=MediaType.PHOTO,
        metadata=MediaMetadata(content_hash=hash_str),
        user_id="user-123",
        encrypted_content=encrypted,
        encryption_key=key,
        content_integrity_hash=hash_str,
    )
    await manager.storage.save(media)

    # Check parsing probability
    probability = manager.get_parsing_probability(media)
    print(f"Parsing probability: {probability:.1%}")

    # Probabilistically decide to parse
    if manager.should_parse(media):
        # Process the media...
        await manager.mark_parsed(media)

    # Check if aged out
    if manager.is_aged_out(media):
        print("Media has aged out")
```

## Decay Timeline

The default decay configuration applies to **all media objects** in the system:

| Age | Parsing Probability |
|-----|---------------------|
| 0-35 min | 100% |
| 35 min | 100% (decay starts) |
| 62.5 min | 50% |
| 90 min | 0% (aged out) |
| 90+ min | Should be cleaned up |

**Important:** The decay timeline is set at the `LifecycleManager` level via `DecayConfig` and applies uniformly to all media. There are no per-media ageout overrides.

### Custom Configuration

```python
from midori_ai_media_lifecycle import DecayConfig

# Shorter decay window
config = DecayConfig(full_probability_minutes=15.0, zero_probability_minutes=45.0)

# Longer decay window
config = DecayConfig(full_probability_minutes=60.0, zero_probability_minutes=180.0)
```

## Decay Functions

### get_parsing_probability

Calculate parsing probability based on media age:

```python
from datetime import datetime
from datetime import timezone

from midori_ai_media_lifecycle import DecayConfig
from midori_ai_media_lifecycle import get_parsing_probability

time_saved = datetime.now(timezone.utc)
probability = get_parsing_probability(time_saved)  # Returns 1.0 for fresh media

# With custom config
config = DecayConfig(full_probability_minutes=30.0, zero_probability_minutes=60.0)
probability = get_parsing_probability(time_saved, config)
```

### should_parse

Make a probabilistic decision about whether to parse:

```python
from midori_ai_media_lifecycle import should_parse

if should_parse(time_saved):
    # Parse the media
    pass
```

### is_aged_out

Check if media has passed the ageout threshold:

```python
from midori_ai_media_lifecycle import is_aged_out

if is_aged_out(time_saved):
    # Media should be cleaned up
    pass
```

### get_age_minutes

Get the age of media in minutes:

```python
from midori_ai_media_lifecycle import get_age_minutes

age = get_age_minutes(time_saved)
print(f"Media is {age:.1f} minutes old")
```

## Lifecycle Manager

The `LifecycleManager` class provides high-level operations for media lifecycle:

```python
from pathlib import Path

from midori_ai_media_lifecycle import DecayConfig
from midori_ai_media_lifecycle import LifecycleManager
from midori_ai_media_lifecycle import create_lifecycle_manager

from midori_ai_media_vault import MediaStorage


# Using factory function
manager = create_lifecycle_manager(base_path=Path("./media"))

# Or with existing storage
storage = MediaStorage(base_path=Path("./media"))
config = DecayConfig()
manager = LifecycleManager(storage=storage, config=config)
```

### Methods

#### get_parsing_probability(media)

Get probability for a MediaObject:

```python
probability = manager.get_parsing_probability(media)
```

#### should_parse(media)

Probabilistic parse decision:

```python
if manager.should_parse(media):
    # Process media
    pass
```

#### is_aged_out(media)

Check if media is aged out:

```python
if manager.is_aged_out(media):
    print("Media has aged out")
```

#### mark_loaded(media)

Update time_loaded and persist:

```python
media = await manager.mark_loaded(media)
print(f"Loaded at: {media.metadata.time_loaded}")
```

#### mark_parsed(media)

Update time_parsed and persist:

```python
media = await manager.mark_parsed(media)
print(f"Parsed at: {media.metadata.time_parsed}")
```

#### cleanup_aged_media()

Remove all aged-out media from storage:

```python
deleted_ids = await manager.cleanup_aged_media()
print(f"Cleaned up {len(deleted_ids)} media objects")
```

#### get_media_status(media_id)

Get comprehensive status for a media object:

```python
status = await manager.get_media_status("photo-001")
print(f"Probability: {status['probability']:.1%}")
print(f"Aged out: {status['aged_out']}")
print(f"Time saved: {status['time_saved']}")
```

## Cleanup Scheduler

The `CleanupScheduler` runs periodic background cleanup:

```python
from midori_ai_media_lifecycle import CleanupScheduler
from midori_ai_media_lifecycle import create_lifecycle_manager


# Create manager and scheduler
manager = create_lifecycle_manager(base_path=Path("./media"))
scheduler = CleanupScheduler(
    lifecycle_manager=manager,
    interval_seconds=300.0,  # Run every 5 minutes
)

# Start background cleanup
scheduler.start()

# Check if running
print(f"Running: {scheduler.is_running}")

# Stop when done
await scheduler.stop()
```

### Cleanup Callback

Register a callback to be notified of cleanups:

```python
def on_cleanup(deleted_ids: list[str]) -> None:
    print(f"Deleted {len(deleted_ids)} media objects")
    for media_id in deleted_ids:
        print(f"  - {media_id}")


scheduler = CleanupScheduler(lifecycle_manager=manager, interval_seconds=60.0, on_cleanup=on_cleanup)
scheduler.start()
```

### Manual Cleanup

Run cleanup once without scheduling:

```python
deleted_ids = await scheduler.run_once()
```

## Integration with Media Vault

This package builds on `midori-ai-media-vault`:

```python
from pathlib import Path

from midori_ai_media_lifecycle import CleanupScheduler
from midori_ai_media_lifecycle import DecayConfig
from midori_ai_media_lifecycle import LifecycleManager

from midori_ai_media_vault import MediaCrypto
from midori_ai_media_vault import MediaMetadata
from midori_ai_media_vault import MediaObject
from midori_ai_media_vault import MediaStorage
from midori_ai_media_vault import MediaType


async def full_workflow():
    # Setup
    storage = MediaStorage(base_path=Path("./media"))
    config = DecayConfig(full_probability_minutes=35.0, zero_probability_minutes=90.0)
    manager = LifecycleManager(storage=storage, config=config)

    # Create media
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

    # Load and process
    loaded = await storage.load("img-001")
    loaded = await manager.mark_loaded(loaded)

    if manager.should_parse(loaded):
        # Decrypt and parse content
        decrypted = MediaCrypto.decrypt(loaded.encrypted_content, loaded.encryption_key, loaded.content_integrity_hash)
        # ... process decrypted content ...
        await manager.mark_parsed(loaded)

    # Start background cleanup
    scheduler = CleanupScheduler(lifecycle_manager=manager, interval_seconds=300.0)
    scheduler.start()

    # ... application runs ...

    # Cleanup on shutdown
    await scheduler.stop()
```

## Best Practices

1. **Use appropriate decay times**: Choose decay windows that match your data retention requirements.

2. **Monitor cleanup operations**: Use the callback parameter to track what gets cleaned up.

3. **Start scheduler early**: Start the cleanup scheduler when your application initializes.

4. **Graceful shutdown**: Always stop the scheduler before application exit.

5. **Check probability before expensive operations**: Use `should_parse()` to avoid processing stale data.

## Error Handling

```python
from midori_ai_media_lifecycle import create_lifecycle_manager


manager = create_lifecycle_manager(base_path=Path("./media"))

try:
    status = await manager.get_media_status("unknown-id")
except FileNotFoundError:
    print("Media not found")
```

## Integration with Other Packages

This package is part of the media storage family:

- **midori-ai-media-vault**: Encrypted storage foundation (required dependency)
- **midori-ai-media-request**: Type-safe request/response interface (future)
