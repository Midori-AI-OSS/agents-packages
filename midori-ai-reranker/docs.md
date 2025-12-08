# Midori AI Reranker - Detailed Documentation

LangChain-powered reranking utilities for Midori AI vector storage with filter pipelines, threshold configuration, and optional LLM-based reranking.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Basic Usage](#basic-usage)
4. [Threshold Configuration](#threshold-configuration)
5. [Custom Filter Pipelines](#custom-filter-pipelines)
6. [Optional LLM Reranking](#optional-llm-reranking)
7. [Embedding Providers](#embedding-providers)
8. [API Reference](#api-reference)

## Overview

When retrieving vectors from storage, raw similarity search results often need refinement:

1. **Relevance filtering** - Remove results below a similarity threshold
2. **Redundancy removal** - Filter out near-duplicate content
3. **Sender prioritization** - Prioritize user content vs model content for better LLM/LRM context
4. **LLM-based reranking** - Use an LLM to intelligently reorder results (optional, heavyweight)

This package wraps LangChain's document transformers with a Midori AI-friendly interface:

- Uses `EmbeddingsRedundantFilter` and `EmbeddingsFilter` for fast, filter-based reranking
- Uses `DocumentCompressorPipeline` for chaining filters
- Uses `InMemoryVectorStore` pattern for efficient temporary storage
- Supports configurable thresholds with per-query modifiers
- Integrates with `midori-ai-agent-base` for optional LLM-based reranking
- Works with `midori-ai-vector-manager` types (`VectorEntry`, `SenderType`)

**Key Design Principles:**

- **LangChain-powered** - Leverage battle-tested LangChain document transformers
- **Filter-first architecture** - Prioritize fast embedding-based filters over slow LLM reranking
- **Pipeline composition** - Use `DocumentCompressorPipeline` for chaining filters
- **Threshold configurability** - Support per-query threshold modifiers (base + modifier)
- **Async-first** - Use LangChain's async methods (`ainvoke`, `afrom_texts`)
- **BYOB (Bring Your Own Backend)** - Users provide their own embedding/LLM endpoints

## Installation

All embedding providers (OpenAI, Ollama, LocalAI, HuggingFace) are included by default.

```bash
# Using UV
uv add "git+https://github.com/Midori-AI-OSS/Carly-AGI#subdirectory=Rest-Servers/packages/midori-ai-reranker"

# Using Pip
pip install "git+https://github.com/Midori-AI-OSS/Carly-AGI#subdirectory=Rest-Servers/packages/midori-ai-reranker"
```

## Basic Usage

### Production Pattern

```python
from midori_ai_reranker import DocumentReranker, get_localai_embeddings

# Configure embeddings (OpenAI-compatible endpoint)
embeddings = get_localai_embeddings(
    api_key="your-api-key",
    model="text-embedding-ada-002",
    base_url="http://localhost:8080/v1"
)

# Create reranker with the production filter pipeline
reranker = DocumentReranker(
    embeddings=embeddings,
    relevance_threshold=0.2  # Base threshold
)

# Rerank a list of text items
question = "What did the user ask about?"
raw_items = ["memory text 1", "memory text 2", "duplicate of 1", ...]

reranked_items = await reranker.rerank(
    question=question,
    items=raw_items,
    similarity_threshold_mod=0.0  # Optional per-query adjustment
)
```

### Using OpenAI Embeddings

```python
from midori_ai_reranker import DocumentReranker, get_openai_embeddings

# Direct OpenAI API
embeddings = get_openai_embeddings(
    api_key="your-openai-api-key",
    model="text-embedding-3-small"
)

reranker = DocumentReranker(embeddings=embeddings)

reranked_items = await reranker.rerank(
    question="What is the capital of France?",
    items=["Paris is the capital", "London is in England", "Paris has the Eiffel Tower"]
)
```

### Using Ollama Embeddings

```python
from midori_ai_reranker import DocumentReranker, get_ollama_embeddings

# Local Ollama server
embeddings = get_ollama_embeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

reranker = DocumentReranker(embeddings=embeddings)

reranked_items = await reranker.rerank(
    question="Tell me about Python",
    items=["Python is a programming language", "Snakes are reptiles", "Python has great libraries"]
)
```

## Threshold Configuration

The relevance threshold is calculated as: **`effective_threshold = base_threshold + similarity_threshold_mod`**

- **Base threshold:** 0.2 (default, set during reranker initialization)
- **Threshold modifier:** 0.0 (default, can be adjusted per-query)

### Using Threshold Modifiers

```python
from midori_ai_reranker import DocumentReranker, get_openai_embeddings

embeddings = get_openai_embeddings(
    api_key="your-api-key",
    model="text-embedding-3-small"
)

reranker = DocumentReranker(
    embeddings=embeddings,
    relevance_threshold=0.2  # Base threshold
)

# For user-specific memory queries, use higher threshold
reranked_items = await reranker.rerank(
    question="What did I say earlier?",
    items=raw_items,
    similarity_threshold_mod=0.3  # 0.2 base + 0.3 = 0.5 effective threshold
)

# For web/general queries, use lower threshold
reranked_items = await reranker.rerank(
    question="General information about topic",
    items=raw_items,
    similarity_threshold_mod=0.0  # 0.2 base + 0.0 = 0.2 effective threshold
)
```

### Advanced Configuration

```python
from midori_ai_reranker import DocumentReranker, RerankerConfig, get_openai_embeddings

embeddings = get_openai_embeddings(
    api_key="your-api-key",
    model="text-embedding-3-small"
)

# Create custom config
config = RerankerConfig(
    relevance_threshold=0.3,          # Higher base threshold
    max_items=100,                     # Process more items
    enable_redundant_filter=True,      # Enable duplicate removal
    enable_relevance_filter=True       # Enable relevance filtering
)

reranker = DocumentReranker(embeddings=embeddings, config=config)

reranked_items = await reranker.rerank(
    question="Search query",
    items=raw_items
)
```

## Custom Filter Pipelines

Build custom filter chains with `FilterPipeline`:

```python
from midori_ai_reranker import FilterPipeline, RedundantFilter, RelevanceFilter, get_openai_embeddings

embeddings = get_openai_embeddings(
    api_key="your-api-key",
    model="text-embedding-3-small"
)

# Build custom pipeline (order matters!)
pipeline = FilterPipeline(
    embeddings=embeddings,
    filters=[
        RedundantFilter(embeddings),              # Remove duplicates first
        RelevanceFilter(embeddings, threshold=0.3), # Then filter by relevance
    ]
)

reranked = await pipeline.compress(
    query="What is machine learning?",
    documents=raw_items,
    max_results=10  # Limit to top 10
)
```

### Filter Order Matters

**Recommended order:** `RedundantFilter` → `RelevanceFilter`

1. Remove duplicates first (faster, reduces items for next filter)
2. Then filter by relevance (operates on deduplicated set)

## Optional LLM Reranking

LLM-based reranking is **optional and expensive**. Use it sparingly when embedding-based filters are insufficient.

```python
from midori_ai_reranker import FilterPipeline, RedundantFilter, RelevanceFilter, LLMReranker, get_openai_embeddings
from midori_ai_agent_base import get_agent

# Set up embeddings
embeddings = get_openai_embeddings(
    api_key="your-api-key",
    model="text-embedding-3-small"
)

# Use Midori AI agent base factory
agent = await get_agent(
    backend="langchain",
    model="groq/compound",
    api_key="your-groq-api-key",
    base_url="https://api.groq.com/openai/v1",
    temperature=0.1,
    use_responses_api=True
)

# Create LLM reranker using the agent
llm_reranker = LLMReranker(agent=agent)

# Add to pipeline after filters (optional, expensive)
pipeline = FilterPipeline(
    embeddings=embeddings,
    filters=[
        RedundantFilter(embeddings),
        RelevanceFilter(embeddings, threshold=0.2),
        llm_reranker,  # Optional final LLM pass
    ]
)

# Note: LLMReranker does NOT integrate with DocumentCompressorPipeline
# Use it separately for custom reranking logic
documents = ["doc1", "doc2", "doc3"]
reranked = await llm_reranker.rerank(
    query="What is the most relevant document?",
    documents=documents,
    top_k=5
)
```

## Embedding Providers

### OpenAI

```python
from midori_ai_reranker import get_openai_embeddings

# Direct OpenAI API
embeddings = get_openai_embeddings(
    api_key="your-openai-api-key",
    model="text-embedding-3-small"
)

# Custom base URL (e.g., Azure OpenAI)
embeddings = get_openai_embeddings(
    api_key="your-api-key",
    model="text-embedding-ada-002",
    base_url="https://your-resource.openai.azure.com/openai/deployments/your-deployment"
)
```

### Ollama

```python
from midori_ai_reranker import get_ollama_embeddings

# Local Ollama server
embeddings = get_ollama_embeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)
```

### LocalAI (OpenAI-Compatible)

```python
from midori_ai_reranker import get_localai_embeddings

# Any OpenAI-compatible endpoint
embeddings = get_localai_embeddings(
    api_key="your-api-key",
    model="text-embedding-ada-002",
    base_url="http://localhost:8080/v1",
    max_retries=1,
    request_timeout=75
)
```

### HuggingFace

```python
from midori_ai_reranker import get_huggingface_embeddings

# Local or HuggingFace Inference API
embeddings = get_huggingface_embeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# With custom model kwargs
embeddings = get_huggingface_embeddings(
    model_name="sentence-transformers/all-mpnet-base-v2",
    model_kwargs={"device": "cuda"}
)
```

## API Reference

### DocumentReranker

Main class for document reranking with configurable filters.

```python
DocumentReranker(
    embeddings: Embeddings,
    relevance_threshold: float = 0.2,
    config: Optional[RerankerConfig] = None
)
```

**Parameters:**
- `embeddings`: Embeddings function for similarity comparison
- `relevance_threshold`: Base relevance threshold (default 0.2)
- `config`: Optional RerankerConfig for advanced settings

**Methods:**

```python
async def rerank(
    question: str,
    items: list[str],
    similarity_threshold_mod: float = 0.0,
    max_results: Optional[int] = None
) -> list[str]
```

### FilterPipeline

Custom filter pipeline for document compression.

```python
FilterPipeline(
    embeddings: Embeddings,
    filters: Optional[list] = None
)
```

**Parameters:**
- `embeddings`: Embeddings function for similarity comparison
- `filters`: Optional list of filter components (RedundantFilter, RelevanceFilter, etc.)

**Methods:**

```python
async def compress(
    query: str,
    documents: list[str],
    max_results: Optional[int] = None
) -> list[str]
```

### RerankerConfig

Configuration dataclass for reranker settings.

```python
@dataclass
class RerankerConfig:
    relevance_threshold: float = 0.2
    similarity_threshold_mod: float = 0.0
    max_items: int = 50
    enable_redundant_filter: bool = True
    enable_relevance_filter: bool = True
```

### RedundantFilter

Wrapper for LangChain's `EmbeddingsRedundantFilter`.

```python
RedundantFilter(
    embeddings: Embeddings,
    similarity_threshold: float = 0.95
)
```

### RelevanceFilter

Wrapper for LangChain's `EmbeddingsFilter`.

```python
RelevanceFilter(
    embeddings: Embeddings,
    threshold: float = 0.2
)
```

**Methods:**

```python
def update_threshold(new_threshold: float) -> None
```

### LLMReranker

Optional LLM-based reranking using Midori AI agent base.

```python
LLMReranker(agent: MidoriAiAgentProtocol)
```

**Methods:**

```python
async def rerank(
    query: str,
    documents: list[str],
    top_k: Optional[int] = None
) -> list[str]
```

## LangChain Components Reference

| Component | Import Path | Purpose |
|-----------|-------------|---------|
| `EmbeddingsRedundantFilter` | `langchain_community.document_transformers` | Remove duplicate documents |
| `EmbeddingsFilter` | `langchain.retrievers.document_compressors.embeddings_filter` | Filter by relevance threshold |
| `DocumentCompressorPipeline` | `langchain.retrievers.document_compressors.base` | Chain filters together |
| `ContextualCompressionRetriever` | `langchain.retrievers` | Orchestrate compression with retriever |
| `InMemoryVectorStore` | `langchain_community.vectorstores` | Temporary store for raw results |

## Performance Notes

- **Filter-based reranking** (default) is fast and cost-effective
- **LLM-based reranking** is slow and expensive - use sparingly
- **Default max_items** is 50 (performance/cost tradeoff)
- **Filter order** matters: redundant → relevance is optimal
- **Threshold tuning**: Start with 0.2, adjust based on precision/recall needs

## Examples

See the [examples directory](./examples) for more usage patterns and integration examples.
