# midori-ai-context-bridge Documentation

Persistent thinking cache with time-based memory decay for AI reasoning models. Uses `midori-ai-vector-manager` for vector storage.

## Overview

The Context Bridge package solves the problem of reasoning models "rehashing" the same prompts by providing a caching layer that:

- Uses `midori-ai-vector-manager` for vector storage (backed by ChromaDB)
- Implements gradual memory corruption for older data to simulate natural forgetting
- Supports different decay rates for different model types
- Automatically cleans up data older than the removal threshold

## Architecture

Context Bridge now depends on `midori-ai-vector-manager` for all vector storage operations:
- **Storage**: Delegates to `ChromaVectorStore` from vector-manager
- **Decay/Corruption**: Retained in context-bridge as domain-specific logic
- **ReasoningEntry**: Wraps `VectorEntry` objects with reasoning-specific fields

## Installation

See README.md for installation instructions.

## Core Concepts

### Model Types

The package supports two model types with different decay characteristics:

| Model Type | Corruption Start | Full Removal |
|------------|------------------|--------------|
| PREPROCESSING | 30 minutes | 90 minutes |
| WORKING_AWARENESS | 12 hours | 36 hours |

- **PREPROCESSING**: Fast-decaying tactical memory for preprocessing analysis
- **WORKING_AWARENESS**: Slow-decaying strategic memory for deeper context

### Memory Decay

Memory corruption simulates natural forgetting:

1. **Fresh data** (age < decay threshold): No corruption
2. **Aging data** (between decay and removal threshold): Progressive character-level corruption
3. **Old data** (age >= removal threshold): Automatically removed

## Usage

### Basic Usage

```python
from midori_ai_context_bridge import ContextBridge, ModelType

# Initialize with default settings
bridge = ContextBridge(max_tokens_per_summary=500)

# Store reasoning after model inference
await bridge.store_reasoning(
    session_id="username:discordid",
    text="The user asked about weather. Key entities: weather, location...",
    model_type=ModelType.PREPROCESSING
)

# Get prior reasoning before next model inference
context = await bridge.get_prior_reasoning(
    session_id="username:discordid",
    model_type=ModelType.PREPROCESSING
)
# Returns compressed context with corruption applied based on age
```

### Integration with Reasoning Models

```python
from midori_ai_context_bridge import ContextBridge, ModelType

bridge = ContextBridge(max_tokens_per_summary=500)

async def get_thinking(past_messages, username, discordid, ...):
    session_id = f"{username}:{discordid}"
    
    # Get prior reasoning for preprocessing (30 min decay)
    preprocessing_context = await bridge.get_prior_reasoning(
        session_id,
        model_type=ModelType.PREPROCESSING
    )
    
    # Get prior reasoning for working awareness (12 hour decay)
    working_context = await bridge.get_prior_reasoning(
        session_id,
        model_type=ModelType.WORKING_AWARENESS
    )
    
    # ... run preprocessing models with preprocessing_context ...
    # ... run working awareness models with working_context ...
    
    # Store results for next time
    await bridge.store_reasoning(
        session_id,
        preprocessing_result,
        model_type=ModelType.PREPROCESSING
    )
    await bridge.store_reasoning(
        session_id,
        working_result,
        model_type=ModelType.WORKING_AWARENESS
    )
    
    return thinking_text
```

### Custom Decay Configuration

```python
from midori_ai_context_bridge import (
    ContextBridge,
    BridgeConfig,
    DecayConfig,
    ModelType,
)

# Custom decay: preprocessing expires faster
custom_config = BridgeConfig(
    max_tokens_per_summary=1000,
    preprocessing_decay=DecayConfig(
        decay_minutes=15,        # Start corrupting after 15 minutes
        removal_multiplier=3.0,  # Remove after 45 minutes
        corruption_intensity=0.4 # Higher corruption rate
    ),
    working_awareness_decay=DecayConfig(
        decay_minutes=360,       # Start corrupting after 6 hours
        removal_multiplier=3.0,  # Remove after 18 hours
        corruption_intensity=0.2 # Lower corruption rate
    ),
)

bridge = ContextBridge(config=custom_config)
```

### Persistent Storage

```python
# Use default persistent storage (~/.midoriai/vectorstore/chromadb/)
bridge = ContextBridge(max_tokens_per_summary=500)

# Use custom persistent storage path
bridge = ContextBridge(
    max_tokens_per_summary=500,
    persist_directory="/path/to/chromadb"
)

# Use ephemeral in-memory storage (not persisted)
bridge = ContextBridge(
    max_tokens_per_summary=500,
    persist_directory=None
)
```

### Session Management

```python
# Get statistics for a session
stats = await bridge.get_session_stats("username:discordid")
print(stats)
# {
#     "session_id": "username:discordid",
#     "preprocessing_count": 5,
#     "working_awareness_count": 3,
#     "total_count": 8,
#     "oldest_preprocessing_age_minutes": 25.5,
#     "oldest_working_age_minutes": 120.3
# }

# Clear all entries for a session
removed = await bridge.clear_session("username:discordid")
print(f"Removed {removed} entries")

# Manual cleanup of expired entries
removed = await bridge.cleanup_expired()
print(f"Cleaned up {removed} expired entries")
```

## API Reference

### ContextBridge

Main interface for the context bridge.

#### Constructor

```python
ContextBridge(
    max_tokens_per_summary: int = 500,
    config: Optional[BridgeConfig] = None,
    persist_directory: Optional[str] = None
)
```

#### Methods

- `store_reasoning(session_id, text, model_type, metadata=None)` - Store reasoning text
- `get_prior_reasoning(session_id, model_type, include_corrupted=True)` - Get prior reasoning with decay
- `cleanup_expired()` - Remove all expired entries
- `get_session_stats(session_id)` - Get session statistics
- `clear_session(session_id)` - Clear all entries for a session
- `count()` - Get total entry count

### ModelType

Enum for model types:
- `ModelType.PREPROCESSING` - 30 minute decay
- `ModelType.WORKING_AWARENESS` - 12 hour decay

### BridgeConfig

Configuration dataclass:
- `max_tokens_per_summary: int` - Max tokens for compressed output
- `chroma_collection_name: str` - ChromaDB collection name
- `preprocessing_decay: DecayConfig` - Decay config for preprocessing
- `working_awareness_decay: DecayConfig` - Decay config for working awareness

### DecayConfig

Decay configuration dataclass:
- `decay_minutes: int` - Minutes before corruption begins
- `removal_multiplier: float` - Multiplier for removal threshold (default 3.0)
- `corruption_intensity: float` - Max corruption rate (0.0 to 1.0)

### MemoryCorruptor

Low-level corruption logic:
- `calculate_severity(age_minutes)` - Get corruption severity (0.0 to 1.0)
- `corrupt_text(text, age_minutes)` - Apply corruption to text
- `should_remove(age_minutes)` - Check if data should be removed
- `process_text(text, age_minutes)` - Process with corruption and removal

### ChromaStorage

Direct access to ChromaDB storage:
- `store(session_id, text, model_type, metadata=None)` - Store entry
- `get_entries_for_session(session_id, model_type=None, limit=100)` - Get entries
- `delete_entries(entry_ids)` - Delete by IDs
- `get_all_entries(limit=1000)` - Get all entries
- `count()` - Get total count
- `clear()` - Clear all entries

### ContextCompressor

Context compression utilities:
- `compress(texts, separator)` - Compress multiple texts
- `compress_with_labels(labeled_texts, separator)` - Compress with labels
- `estimate_tokens(text)` - Estimate token count

## Memory Corruption Details

The corruption algorithm:

1. Calculate severity based on age: `severity = (age - decay_threshold) / (removal_threshold - decay_threshold)`
2. For each character, with probability `severity * corruption_intensity`:
   - 50% chance: remove the character
   - 50% chance: replace with random lowercase letter or space
3. Severity increases linearly from 0% at decay threshold to 100% at removal threshold

Example corruption progression:
- Fresh (0-30 min): "The user asked about weather in Seattle"
- Aging (45 min): "The user asked abut weather in eatle"
- Old (75 min): "Th  us r asked but wath r n stle"
- Expired (90+ min): Entry removed

## Dependencies

- `midori_ai_vector_manager` - Vector storage abstraction (backed by ChromaDB)
- `midori_ai_logger` - Logging (via git+)
- `pydantic>=2.0.0` - Data validation and models
