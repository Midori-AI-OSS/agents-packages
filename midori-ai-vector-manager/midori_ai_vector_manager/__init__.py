"""Midori AI Vector Manager - Reusable vector storage for Midori AI packages."""

from .backends.chromadb import ChromaMultimodalStore
from .backends.chromadb import ChromaVectorStore

from .config import DEFAULT_PERSIST_PATH

from .embeddings import EmbeddingFunction
from .embeddings import create_openai_embedding_function
from .embeddings import get_default_embedding_function

from .enums import SenderType

from .models import VectorEntry

from .protocol import VectorStoreProtocol


__all__ = ["ChromaMultimodalStore", "ChromaVectorStore", "create_openai_embedding_function", "DEFAULT_PERSIST_PATH", "EmbeddingFunction", "get_default_embedding_function", "LanceVectorStore", "SenderType", "VectorEntry", "VectorStoreProtocol"]


def __getattr__(name: str):
    """Lazy import for LanceVectorStore to avoid import errors on incompatible systems."""
    if name == "LanceVectorStore":
        from .backends.lancedb import LanceVectorStore

        return LanceVectorStore
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
