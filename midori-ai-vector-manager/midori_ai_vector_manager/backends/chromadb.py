"""ChromaDB backend implementation for vector storage.

This module provides ChromaDB-backed vector storage implementations
with support for text and multimodal (image) content.
"""

import time
import uuid

import chromadb

from typing import Any
from typing import Optional

from midori_ai_logger import MidoriAiLogger

from ..config import DEFAULT_PERSIST_PATH
from ..enums import SenderType
from ..models import VectorEntry
from ..protocol import VectorStoreProtocol


_logger = MidoriAiLogger(None, name="VectorManager")


def generate_time_based_id() -> str:
    """Generate a time-based unique ID.

    Returns:
        String ID with timestamp prefix for natural ordering
    """
    timestamp_ms = int(time.time() * 1000)
    unique_suffix = uuid.uuid4().hex[:8]
    return f"{timestamp_ms}-{unique_suffix}"


class ChromaVectorStore(VectorStoreProtocol):
    """ChromaDB-based vector storage implementation.

    Provides persistent vector storage with time-based IDs and
    support for metadata filtering and semantic similarity search.
    """

    def __init__(self, collection_name: str, persist_directory: Optional[str] = "default", embedding_function: Optional[Any] = None, disable_time_gating: bool = False) -> None:
        """Initialize ChromaDB storage.

        Args:
            collection_name: Name for the ChromaDB collection
            persist_directory: Directory for persistence.
                - "default": Uses ~/.midoriai/vectorstore/chromadb/
                - None: Uses ephemeral in-memory storage
                - str: Uses the specified path
            embedding_function: Optional custom embedding function.
                If None, ChromaDB uses its default embeddings (CPU-based, can be slow).
            disable_time_gating: If True, disables time-based ID generation and timestamp
                metadata for long-term storage. Entries will use simple UUIDs instead.
                Default is False to maintain backward compatibility.

        Note:
            The embedding function cannot be changed after a persistent storage
            is created. If you need different embeddings, use a different
            persist_directory or collection_name. The default ChromaDB embeddings
            run on CPU and may be slow for large datasets.
        """
        self._collection_name = collection_name
        self._disable_time_gating = disable_time_gating

        if persist_directory == "default":
            persist_path = DEFAULT_PERSIST_PATH / "chromadb"
            persist_path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(persist_path))
        elif persist_directory is None:
            self._client = chromadb.EphemeralClient()
        else:
            self._client = chromadb.PersistentClient(path=persist_directory)

        collection_kwargs: dict[str, Any] = {"name": collection_name, "metadata": {"hnsw:space": "cosine"}}
        if embedding_function is not None:
            collection_kwargs["embedding_function"] = embedding_function

        self._collection = self._client.get_or_create_collection(**collection_kwargs)
        _logger.rprint(f"Initialized ChromaVectorStore collection: {collection_name}", mode="debug")

    async def store(self, text: str, sender: Optional[SenderType] = None, metadata: Optional[dict[str, Any]] = None) -> VectorEntry:
        """Store text with optional sender and metadata.

        Args:
            text: Text content to store
            sender: Optional sender type for reranking
            metadata: Optional additional metadata

        Returns:
            The created VectorEntry
        """
        if self._disable_time_gating:
            entry_id = uuid.uuid4().hex
            timestamp = 0.0
        else:
            entry_id = generate_time_based_id()
            timestamp = time.time()
        entry = VectorEntry(id=entry_id, text=text, timestamp=timestamp, sender=sender, metadata=metadata or {})
        chroma_metadata = entry.to_chromadb_metadata()
        self._collection.add(ids=[entry_id], documents=[text], metadatas=[chroma_metadata])
        _logger.rprint(f"Stored entry {entry_id} in collection {self._collection_name}", mode="debug")
        return entry

    async def get_by_id(self, entry_id: str) -> Optional[VectorEntry]:
        """Get a single entry by ID.

        Args:
            entry_id: The unique identifier of the entry

        Returns:
            The VectorEntry if found, None otherwise
        """
        results = self._collection.get(ids=[entry_id], include=["documents", "metadatas"])
        if not results or not results["ids"]:
            return None
        doc = results["documents"][0] if results["documents"] else ""
        meta = results["metadatas"][0] if results["metadatas"] else {}
        return self._metadata_to_entry(entry_id, doc, meta)

    async def query(self, filters: dict[str, Any], limit: int = 100) -> list[VectorEntry]:
        """Query entries matching metadata filters.

        Args:
            filters: Metadata filters to apply (empty dict returns all entries)
            limit: Maximum number of entries to return

        Returns:
            List of matching VectorEntry objects
        """
        if not filters:
            results = self._collection.get(limit=limit, include=["documents", "metadatas"])
        else:
            where_filter = self._build_where_filter(filters)
            results = self._collection.get(where=where_filter, limit=limit, include=["documents", "metadatas"])
        return self._results_to_entries(results)

    async def search_similar(self, query_text: str, limit: int = 10) -> list[VectorEntry]:
        """Semantic similarity search.

        Args:
            query_text: Text to search for similar entries
            limit: Maximum number of entries to return

        Returns:
            List of VectorEntry objects ranked by similarity
        """
        results = self._collection.query(query_texts=[query_text], n_results=limit, include=["documents", "metadatas"])
        return self._query_results_to_entries(results)

    async def delete(self, entry_ids: list[str]) -> int:
        """Delete entries by IDs.

        Args:
            entry_ids: List of entry IDs to delete

        Returns:
            Number of entries deleted
        """
        if not entry_ids:
            return 0
        self._collection.delete(ids=entry_ids)
        _logger.rprint(f"Deleted {len(entry_ids)} entries from collection {self._collection_name}", mode="debug")
        return len(entry_ids)

    async def count(self) -> int:
        """Return total entry count."""
        return self._collection.count()

    async def clear(self) -> None:
        """Clear all entries from the store."""
        self._client.delete_collection(name=self._collection_name)
        self._collection = self._client.get_or_create_collection(name=self._collection_name, metadata={"hnsw:space": "cosine"})
        _logger.rprint(f"Cleared collection {self._collection_name}", mode="debug")

    def _build_where_filter(self, filters: dict[str, Any]) -> dict[str, Any]:
        """Build ChromaDB where filter from metadata filters."""
        if len(filters) == 0:
            return {}
        if len(filters) == 1:
            key, value = next(iter(filters.items()))
            return {key: value}
        conditions = [{k: v} for k, v in filters.items()]
        return {"$and": conditions}

    def _metadata_to_entry(self, entry_id: str, doc: str, meta: dict[str, Any]) -> VectorEntry:
        """Convert ChromaDB metadata to VectorEntry."""
        timestamp = meta.pop("timestamp", 0.0)
        sender_str = meta.pop("sender", None)
        sender = SenderType(sender_str) if sender_str else None
        return VectorEntry(id=entry_id, text=doc, timestamp=timestamp, sender=sender, metadata=meta)

    def _results_to_entries(self, results: dict[str, Any]) -> list[VectorEntry]:
        """Convert ChromaDB get results to VectorEntry list."""
        entries = []
        if results and results["ids"]:
            for i, entry_id in enumerate(results["ids"]):
                doc = results["documents"][i] if results["documents"] else ""
                meta = dict(results["metadatas"][i]) if results["metadatas"] else {}
                entries.append(self._metadata_to_entry(entry_id, doc, meta))
        return sorted(entries, key=lambda e: e.timestamp)

    def _query_results_to_entries(self, results: dict[str, Any]) -> list[VectorEntry]:
        """Convert ChromaDB query results to VectorEntry list."""
        entries = []
        if results and results["ids"] and results["ids"][0]:
            ids = results["ids"][0]
            docs = results["documents"][0] if results["documents"] else [""] * len(ids)
            metas = results["metadatas"][0] if results["metadatas"] else [{}] * len(ids)
            for i, entry_id in enumerate(ids):
                doc = docs[i] if i < len(docs) else ""
                meta = dict(metas[i]) if i < len(metas) else {}
                entries.append(self._metadata_to_entry(entry_id, doc, meta))
        return entries


class ChromaMultimodalStore:
    """ChromaDB-based multimodal storage for images.

    Uses OpenCLIP embeddings for image storage and text-based querying.
    """

    def __init__(self, collection_name: str, persist_directory: Optional[str] = "default") -> None:
        """Initialize ChromaDB multimodal storage.

        Args:
            collection_name: Name for the ChromaDB collection
            persist_directory: Directory for persistence.
                - "default": Uses ~/.midoriai/vectorstore/chromadb/
                - None: Uses ephemeral in-memory storage
                - str: Uses the specified path
        """
        self._collection_name = collection_name

        if persist_directory == "default":
            persist_path = DEFAULT_PERSIST_PATH / "chromadb"
            persist_path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(persist_path))
        elif persist_directory is None:
            self._client = chromadb.EphemeralClient()
        else:
            self._client = chromadb.PersistentClient(path=persist_directory)

        self._embedding_function = self._get_openclip_embedding()
        self._collection = self._client.get_or_create_collection(name=collection_name, embedding_function=self._embedding_function, metadata={"hnsw:space": "cosine"})

    def _get_openclip_embedding(self) -> Any:
        """Get OpenCLIP embedding function for multimodal support."""
        try:
            from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction

            return OpenCLIPEmbeddingFunction()
        except ImportError:
            raise ImportError("OpenCLIP embedding function requires additional dependencies. Install chromadb with the 'openclip' extra.")

    async def store_image(self, image_data: bytes, metadata: Optional[dict[str, Any]] = None) -> VectorEntry:
        """Store an image with optional metadata.

        Args:
            image_data: Image bytes
            metadata: Optional additional metadata

        Returns:
            The created VectorEntry (text field contains placeholder)
        """
        entry_id = generate_time_based_id()
        timestamp = time.time()
        entry_metadata: dict[str, Any] = {"timestamp": timestamp, **(metadata or {})}
        self._collection.add(ids=[entry_id], images=[image_data], metadatas=[entry_metadata])
        return VectorEntry(id=entry_id, text="[image]", timestamp=timestamp, sender=None, metadata=metadata or {})

    async def query_by_text(self, query_text: str, limit: int = 5) -> list[VectorEntry]:
        """Query images by text description.

        Args:
            query_text: Text description to search for
            limit: Maximum number of results

        Returns:
            List of VectorEntry objects for matching images
        """
        results = self._collection.query(query_texts=[query_text], n_results=limit, include=["metadatas"])
        entries = []
        if results and results["ids"] and results["ids"][0]:
            ids = results["ids"][0]
            metas = results["metadatas"][0] if results["metadatas"] else [{}] * len(ids)
            for i, entry_id in enumerate(ids):
                meta = dict(metas[i]) if i < len(metas) else {}
                timestamp = meta.pop("timestamp", 0.0)
                entries.append(VectorEntry(id=entry_id, text="[image]", timestamp=timestamp, sender=None, metadata=meta))
        return entries

    async def count(self) -> int:
        """Return total image count."""
        return self._collection.count()

    async def clear(self) -> None:
        """Clear all images from the store."""
        self._client.delete_collection(name=self._collection_name)
        self._collection = self._client.get_or_create_collection(name=self._collection_name, embedding_function=self._embedding_function, metadata={"hnsw:space": "cosine"})
