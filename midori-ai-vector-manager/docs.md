# midori-ai-vector-manager Documentation

## Overview

`midori-ai-vector-manager` provides a reusable, protocol-based vector storage abstraction for Midori AI packages. It extracts the ChromaDB wrapper into a standalone package that any component can use.

## Features

- **Protocol-based design**: `VectorStoreProtocol` ABC allows future backend support
- **ChromaDB backend**: Full-featured ChromaDB implementation
- **Multimodal support**: Text and image storage via OpenCLIP
- **Sender tracking**: `SenderType` enum for reranking support
- **Standard persistence**: Default path `~/.midoriai/vectorstore/{backend}/`
- **Flexible embeddings**: Support ChromaDB defaults or custom OpenAI-friendly models
- **Long-term storage**: Optional `disable_time_gating` flag for permanent knowledge storage
- **100% async-friendly**: All operations are async-compatible

## API Reference

### Enums

#### SenderType

```python
from midori_ai_vector_manager import SenderType

class SenderType(str, Enum):
    USER = "user"      # Content from user
    MODEL = "model"    # Content from model
    SYSTEM = "system"  # System-generated content
```

### Models

#### VectorEntry

```python
from midori_ai_vector_manager import VectorEntry

entry = VectorEntry(
    id="1234567890-abc12345",
    text="The stored text content",
    timestamp=1699999999.0,
    sender=SenderType.USER,
    metadata={"session_id": "user123"}
)

# Get age in minutes
age = entry.age_minutes

# Convert to ChromaDB metadata format
chroma_meta = entry.to_chromadb_metadata()
```

### Protocol

#### VectorStoreProtocol

All backends implement this protocol:

```python
class VectorStoreProtocol(ABC):
    async def store(self, text: str, sender: Optional[SenderType] = None, metadata: Optional[dict[str, Any]] = None) -> VectorEntry
    async def get_by_id(self, entry_id: str) -> Optional[VectorEntry]
    async def query(self, filters: dict[str, Any], limit: int = 100) -> list[VectorEntry]
    async def search_similar(self, query_text: str, limit: int = 10) -> list[VectorEntry]
    async def delete(self, entry_ids: list[str]) -> int
    async def count(self) -> int
    async def clear(self) -> None
```

### Backends

#### ChromaVectorStore

Text-only vector storage with ChromaDB:

```python
from midori_ai_vector_manager import ChromaVectorStore, SenderType

# Create store with default persistence path (~/.midoriai/vectorstore/chromadb/)
store = ChromaVectorStore(collection_name="my_collection")

# Or with custom path
store = ChromaVectorStore(
    collection_name="my_collection",
    persist_directory="/custom/path"
)

# Or disable time gating for long-term storage
long_term_store = ChromaVectorStore(
    collection_name="long_term_knowledge",
    disable_time_gating=True  # Entries use simple UUIDs without timestamps
)

# Store text with sender metadata
entry = await store.store(
    text="This is my reasoning about the problem...",
    sender=SenderType.MODEL,
    metadata={"session_id": "user123", "model": "preprocessing"}
)

# Query by metadata
entries = await store.query(
    filters={"session_id": "user123"},
    limit=50
)

# Semantic similarity search
similar = await store.search_similar(
    query_text="What did the user ask about?",
    limit=10
)

# Delete entries
deleted_count = await store.delete([entry.id for entry in entries])

# Get entry by ID
entry = await store.get_by_id("1234567890-abc12345")

# Count entries
total = await store.count()

# Clear all entries
await store.clear()
```

#### ChromaMultimodalStore

Image storage with OpenCLIP embeddings:

```python
from midori_ai_vector_manager import ChromaMultimodalStore

# Create multimodal store
image_store = ChromaMultimodalStore(collection_name="user_images")

# Store an image
entry = await image_store.store_image(
    image_data=image_bytes,
    metadata={"user_id": "123", "description": "selfie"}
)

# Query images by text
results = await image_store.query_by_text(
    query_text="animals",
    limit=5
)
```

### Custom Embedding Functions

Use custom OpenAI-friendly embedding models:

```python
from midori_ai_vector_manager import ChromaVectorStore
from chromadb.utils import embedding_functions

# Use OpenAI embeddings
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key="your-api-key",
    model_name="text-embedding-ada-002"
)

store = ChromaVectorStore(
    collection_name="my_collection",
    embedding_function=openai_ef
)

# Or use any OpenAI-compatible endpoint (LocalAI, etc.)
localai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_base="http://localhost:8080/v1",
    api_key="not-needed",
    model_name="text-embedding-ada-002"
)

store = ChromaVectorStore(
    collection_name="my_collection",
    embedding_function=localai_ef
)
```

## Configuration

### Default Persistence Path

The default persistence path is `~/.midoriai/vectorstore/{backend}/`. For ChromaDB, this becomes `~/.midoriai/vectorstore/chromadb/`.

You can override this with the `persist_directory` parameter:

```python
store = ChromaVectorStore(
    collection_name="my_collection",
    persist_directory="/custom/path/to/storage"
)
```

### Ephemeral Storage

For in-memory storage (no persistence), pass `None` as `persist_directory`:

```python
store = ChromaVectorStore(
    collection_name="my_collection",
    persist_directory=None  # Ephemeral storage
)
```

## Integration Example

### Using with midori-ai-context-bridge

```python
from midori_ai_vector_manager import ChromaVectorStore, VectorEntry

# context-bridge creates its store using vector-manager
reasoning_store = ChromaVectorStore(
    collection_name="reasoning_cache",
    # Uses standard path: ~/.midoriai/vectorstore/chromadb/
)

# Store reasoning with sender tracking
entry = await reasoning_store.store(
    text="Preprocessing: Analyzed user intent...",
    sender=SenderType.MODEL,
    metadata={"session_id": "user:123", "model_type": "preprocessing"}
)

# Retrieve similar reasoning
similar = await reasoning_store.search_similar(
    query_text="user intent analysis",
    limit=5
)
```

## LanceDB Backend

LanceDB provides an alternative vector storage backend with columnar format storage:

```python
from midori_ai_vector_manager import LanceVectorStore, SenderType

# Create store with default persistence path (~/.midoriai/vectorstore/lancedb/)
store = LanceVectorStore(table_name="my_table")

# Or with custom path
store = LanceVectorStore(
    table_name="my_table",
    persist_directory="/custom/path"
)

# Store text with sender metadata
entry = await store.store(
    text="This is my reasoning about the problem...",
    sender=SenderType.MODEL,
    metadata={"session_id": "user123"}
)

# Semantic similarity search
similar = await store.search_similar(
    query_text="What did the user ask about?",
    limit=10
)
```

## Backend Comparison

| Database | Status | Notes |
|----------|--------|-------|
| ChromaDB | **Implemented** | CPU-based embeddings, good defaults |
| LanceDB | **Implemented** | Columnar format, fast analytics |
| Qdrant | Future | Production-ready, advanced filtering |
| Milvus | Not recommended | Complex setup, overkill for most uses |
