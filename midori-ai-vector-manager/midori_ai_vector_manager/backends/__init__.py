"""Vector storage backends."""

from .chromadb import ChromaMultimodalStore
from .chromadb import ChromaVectorStore


__all__ = ["ChromaMultimodalStore", "ChromaVectorStore", "LanceVectorStore"]


def __getattr__(name: str):
    """Lazy import for LanceVectorStore to avoid import errors on incompatible systems."""
    if name == "LanceVectorStore":
        from .lancedb import LanceVectorStore

        return LanceVectorStore
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
