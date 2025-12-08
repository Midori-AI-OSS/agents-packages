"""Embedding function abstractions for vector storage.

This module provides wrappers and utilities for embedding functions,
making it easy to use custom embeddings or fall back to ChromaDB defaults.
"""

from typing import Any
from typing import Callable
from typing import Optional
from typing import Protocol


class EmbeddingFunction(Protocol):
    """Protocol for embedding functions compatible with ChromaDB.

    Any callable that takes a list of texts and returns a list of embeddings
    can be used as an embedding function.
    """

    def __call__(self, input: list[str]) -> list[list[float]]:
        """Embed a list of texts.

        Args:
            input: List of text strings to embed

        Returns:
            List of embedding vectors (list of floats)
        """
        ...


def get_default_embedding_function() -> Optional[Any]:
    """Get the default ChromaDB embedding function.

    Returns None to let ChromaDB use its built-in default.

    Returns:
        None (ChromaDB will use default)
    """
    return None


def create_openai_embedding_function(api_key: str, model_name: str = "text-embedding-ada-002", api_base: Optional[str] = None) -> Callable[[list[str]], list[list[float]]]:
    """Create an OpenAI-compatible embedding function.

    Args:
        api_key: OpenAI API key
        model_name: Model name (default: text-embedding-ada-002)
        api_base: Optional custom API base URL (for LocalAI, etc.)

    Returns:
        An embedding function compatible with ChromaDB

    Raises:
        ImportError: If chromadb.utils.embedding_functions is not available
    """
    from chromadb.utils import embedding_functions

    kwargs: dict[str, Any] = {"api_key": api_key, "model_name": model_name}
    if api_base:
        kwargs["api_base"] = api_base

    return embedding_functions.OpenAIEmbeddingFunction(**kwargs)
