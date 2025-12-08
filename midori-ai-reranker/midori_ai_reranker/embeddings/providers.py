"""Embedding providers and helpers."""

from typing import Optional

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_localai import LocalAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings


def get_openai_embeddings(api_key: str, model: str = "text-embedding-3-small", base_url: Optional[str] = None):
    """Create OpenAI embeddings instance.

    Args:
        api_key: OpenAI API key
        model: Model name (default: text-embedding-3-small)
        base_url: Optional custom base URL for OpenAI-compatible endpoints

    Returns:
        OpenAIEmbeddings instance
    """
    kwargs = {"model": model, "api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url

    return OpenAIEmbeddings(**kwargs)


def get_ollama_embeddings(model: str = "nomic-embed-text", base_url: str = "http://localhost:11434"):
    """Create Ollama embeddings instance.

    Args:
        model: Model name (default: nomic-embed-text)
        base_url: Ollama server URL (default: http://localhost:11434)

    Returns:
        OllamaEmbeddings instance
    """
    return OllamaEmbeddings(model=model, base_url=base_url)


def get_localai_embeddings(api_key: str, model: str, base_url: str, max_retries: int = 1, request_timeout: int = 75):
    """Create LocalAI embeddings instance for OpenAI-compatible endpoints.

    Args:
        api_key: API key for the endpoint
        model: Model name
        base_url: Base URL for the OpenAI-compatible endpoint
        max_retries: Maximum number of retries (default: 1)
        request_timeout: Request timeout in seconds (default: 75)

    Returns:
        LocalAIEmbeddings instance
    """
    return LocalAIEmbeddings(openai_api_base=base_url, openai_api_key=api_key, model=model, max_retries=max_retries, request_timeout=request_timeout)


def get_huggingface_embeddings(model_name: str = "sentence-transformers/all-MiniLM-L6-v2", model_kwargs: Optional[dict] = None):
    """Create HuggingFace embeddings instance.

    Args:
        model_name: HuggingFace model name (default: sentence-transformers/all-MiniLM-L6-v2)
        model_kwargs: Optional model configuration kwargs

    Returns:
        HuggingFaceEmbeddings instance
    """
    kwargs = {"model_name": model_name}
    if model_kwargs:
        kwargs["model_kwargs"] = model_kwargs

    return HuggingFaceEmbeddings(**kwargs)
