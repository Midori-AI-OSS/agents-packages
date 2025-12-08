"""Configuration for vector storage backends."""

from pathlib import Path


DEFAULT_PERSIST_PATH = Path.home() / ".midoriai" / "vectorstore"
"""Standard persistence path: ~/.midoriai/vectorstore/{backend}/"""
