"""ChromaDB backend implementation for vector storage.

This module provides ChromaDB-backed vector storage implementations
with support for text and multimodal (image) content.
"""

import asyncio
import hashlib
import time
import uuid

from uuid import UUID

import chromadb

from typing import Any
from typing import Optional
from typing import Sequence

from chromadb.api.models.AsyncCollection import AsyncCollection
from chromadb.api.types import Documents
from chromadb.api.types import Embeddings
from chromadb.api.types import EmbeddingFunction
from chromadb.api.types import GetResult
from chromadb.api.types import IDs
from chromadb.api.types import Include
from chromadb.api.types import Metadatas
from chromadb.api.types import QueryResult
from chromadb.api.types import Where
from chromadb.api.types import WhereDocument

from midori_ai_logger import MidoriAiLogger

from ..config import DEFAULT_PERSIST_PATH
from ..enums import SenderType
from ..models import VectorEntry
from ..protocol import VectorStoreProtocol


_logger = MidoriAiLogger(None, name="VectorManager")


class SimpleHashEmbeddingFunction(EmbeddingFunction[Documents]):
    """Simple embedding function that creates deterministic embeddings from text hashes.
    
    This is a fallback embedding function that doesn't require model downloads.
    It generates 384-dimensional embeddings (matching MiniLM) using a hash-based approach.
    While not semantically meaningful, it provides consistent, deterministic embeddings
    suitable for testing and environments without internet access.
    """

    def __init__(self) -> None:
        """Initialize the simple hash embedding function."""
        pass

    def __call__(self, input: Documents) -> Embeddings:
        """Generate hash-based embeddings for documents.
        
        Args:
            input: List of documents to embed
            
        Returns:
            List of 384-dimensional embedding vectors
        """
        embeddings = []
        for doc in input:
            doc_bytes = doc.encode('utf-8')
            hash_obj = hashlib.sha384(doc_bytes)
            hash_bytes = hash_obj.digest()
            embedding = [float(b) / 255.0 - 0.5 for b in hash_bytes]
            while len(embedding) < 384:
                hash_obj = hashlib.sha384(hash_obj.digest())
                hash_bytes = hash_obj.digest()
                embedding.extend([float(b) / 255.0 - 0.5 for b in hash_bytes])
            embeddings.append(embedding[:384])
        return embeddings

    @staticmethod
    def name() -> str:
        """Return the name of this embedding function."""
        return "simple_hash"

    def get_config(self) -> dict[str, Any]:
        """Return the configuration of this embedding function."""
        return {}

    @staticmethod
    def build_from_config(config: dict[str, Any]) -> "SimpleHashEmbeddingFunction":
        """Build an instance from configuration."""
        return SimpleHashEmbeddingFunction()


class AsyncClientAdapter:
    """Adapter to make sync ChromaDB clients work with AsyncCollection.
    
    This adapter wraps PersistentClient or EphemeralClient and provides
    the async interface expected by AsyncCollection, using asyncio.to_thread()
    internally to handle the sync operations without blocking the event loop.
    """

    def __init__(self, sync_client: Any) -> None:
        """Initialize the adapter with a sync client.
        
        Args:
            sync_client: A PersistentClient or EphemeralClient instance
        """
        self._sync_client = sync_client

    async def _count(self, collection_id: UUID, tenant: Optional[str] = None, database: Optional[str] = None) -> int:
        """Async wrapper for count operation."""
        return await asyncio.to_thread(self._sync_client._count, collection_id)

    async def _add(self, collection_id: UUID, ids: IDs, embeddings: Embeddings, metadatas: Optional[Metadatas] = None, documents: Optional[Documents] = None, uris: Optional[Any] = None, tenant: Optional[str] = None, database: Optional[str] = None) -> bool:
        """Async wrapper for add operation."""
        return await asyncio.to_thread(self._sync_client._add, ids=ids, collection_id=collection_id, embeddings=embeddings, metadatas=metadatas, documents=documents, uris=uris)

    async def _get(self, collection_id: UUID, ids: Optional[IDs] = None, where: Optional[Where] = None, sort: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = None, page: Optional[int] = None, page_size: Optional[int] = None, where_document: Optional[WhereDocument] = None, include: Include = ["embeddings", "metadatas", "documents"], tenant: Optional[str] = None, database: Optional[str] = None) -> GetResult:
        """Async wrapper for get operation."""
        return await asyncio.to_thread(self._sync_client._get, collection_id=collection_id, ids=ids, where=where, limit=limit, offset=offset, where_document=where_document, include=include)

    async def _query(self, collection_id: UUID, query_embeddings: Embeddings, ids: Optional[IDs] = None, n_results: int = 10, where: Optional[Where] = None, where_document: Optional[WhereDocument] = None, include: Include = ["embeddings", "metadatas", "documents", "distances"], tenant: Optional[str] = None, database: Optional[str] = None) -> QueryResult:
        """Async wrapper for query operation."""
        return await asyncio.to_thread(self._sync_client._query, collection_id=collection_id, query_embeddings=query_embeddings, ids=ids, n_results=n_results, where=where, where_document=where_document, include=include)

    async def _update(self, collection_id: UUID, ids: IDs, embeddings: Optional[Embeddings] = None, metadatas: Optional[Metadatas] = None, documents: Optional[Documents] = None, uris: Optional[Any] = None, tenant: Optional[str] = None, database: Optional[str] = None) -> bool:
        """Async wrapper for update operation."""
        return await asyncio.to_thread(self._sync_client._update, collection_id=collection_id, ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents, uris=uris)

    async def _upsert(self, collection_id: UUID, ids: IDs, embeddings: Embeddings, metadatas: Optional[Metadatas] = None, documents: Optional[Documents] = None, uris: Optional[Any] = None, tenant: Optional[str] = None, database: Optional[str] = None) -> bool:
        """Async wrapper for upsert operation."""
        return await asyncio.to_thread(self._sync_client._upsert, ids=ids, collection_id=collection_id, embeddings=embeddings, metadatas=metadatas, documents=documents, uris=uris)

    async def _delete(self, collection_id: UUID, ids: Optional[IDs] = None, where: Optional[Where] = None, where_document: Optional[WhereDocument] = None, tenant: Optional[str] = None, database: Optional[str] = None) -> Sequence[UUID]:
        """Async wrapper for delete operation."""
        return await asyncio.to_thread(self._sync_client._delete, collection_id=collection_id, ids=ids, where=where, where_document=where_document)

    def get_or_create_collection(self, name: str, metadata: Optional[dict[str, Any]] = None, embedding_function: Optional[Any] = None) -> Any:
        """Sync wrapper to get or create collection."""
        return self._sync_client.get_or_create_collection(name=name, metadata=metadata, embedding_function=embedding_function)

    def delete_collection(self, name: str) -> None:
        """Sync wrapper to delete collection."""
        self._sync_client.delete_collection(name=name)

    def create_async_collection(self, sync_collection: Any, embedding_function: Optional[Any] = None) -> AsyncCollection:
        """Create an AsyncCollection from a sync collection.
        
        Args:
            sync_collection: The sync collection to wrap
            embedding_function: Optional embedding function (uses sync_collection's if not provided)
            
        Returns:
            AsyncCollection instance
        """
        if embedding_function is None:
            embedding_function = sync_collection._embedding_function
        return AsyncCollection(client=self, model=sync_collection._model, embedding_function=embedding_function, data_loader=None)


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
                If None, uses SimpleHashEmbeddingFunction (no downloads required).
            disable_time_gating: If True, disables time-based ID generation and timestamp
                metadata for long-term storage. Entries will use simple UUIDs instead.
                Default is False to maintain backward compatibility.

        Note:
            The embedding function cannot be changed after a persistent storage
            is created. If you need different embeddings, use a different
            persist_directory or collection_name.
            
            This implementation uses ChromaDB's native async API through AsyncCollection,
            with an adapter layer to bridge sync client initialization and async operations.
        """
        self._collection_name = collection_name
        self._disable_time_gating = disable_time_gating

        if persist_directory == "default":
            persist_path = DEFAULT_PERSIST_PATH / "chromadb"
            persist_path.mkdir(parents=True, exist_ok=True)
            sync_client = chromadb.PersistentClient(path=str(persist_path))
        elif persist_directory is None:
            sync_client = chromadb.EphemeralClient()
        else:
            sync_client = chromadb.PersistentClient(path=persist_directory)

        self._client_adapter = AsyncClientAdapter(sync_client)
        if embedding_function is None:
            embedding_function = SimpleHashEmbeddingFunction()
            _logger.rprint("Using SimpleHashEmbeddingFunction (no internet connection required)", mode="debug")
        
        self._embedding_function = embedding_function
        collection_kwargs: dict[str, Any] = {"name": collection_name, "metadata": {"hnsw:space": "cosine"}, "embedding_function": embedding_function}

        sync_collection = self._client_adapter.get_or_create_collection(**collection_kwargs)
        self._collection = self._client_adapter.create_async_collection(sync_collection)
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
        await self._collection.add(ids=[entry_id], documents=[text], metadatas=[chroma_metadata])
        _logger.rprint(f"Stored entry {entry_id} in collection {self._collection_name}", mode="debug")
        return entry

    async def get_by_id(self, entry_id: str) -> Optional[VectorEntry]:
        """Get a single entry by ID.

        Args:
            entry_id: The unique identifier of the entry

        Returns:
            The VectorEntry if found, None otherwise
        """
        results = await self._collection.get(ids=[entry_id], include=["documents", "metadatas"])
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
            results = await self._collection.get(limit=limit, include=["documents", "metadatas"])
        else:
            where_filter = self._build_where_filter(filters)
            results = await self._collection.get(where=where_filter, limit=limit, include=["documents", "metadatas"])
        return self._results_to_entries(results)

    async def search_similar(self, query_text: str, limit: int = 10) -> list[VectorEntry]:
        """Semantic similarity search.

        Args:
            query_text: Text to search for similar entries
            limit: Maximum number of entries to return

        Returns:
            List of VectorEntry objects ranked by similarity
        """
        results = await self._collection.query(query_texts=[query_text], n_results=limit, include=["documents", "metadatas"])
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
        await self._collection.delete(ids=entry_ids)
        _logger.rprint(f"Deleted {len(entry_ids)} entries from collection {self._collection_name}", mode="debug")
        return len(entry_ids)

    async def count(self) -> int:
        """Return total entry count."""
        return await self._collection.count()

    async def clear(self) -> None:
        """Clear all entries from the store."""
        self._client_adapter.delete_collection(name=self._collection_name)
        sync_collection = self._client_adapter.get_or_create_collection(name=self._collection_name, metadata={"hnsw:space": "cosine"}, embedding_function=self._embedding_function)
        self._collection = self._client_adapter.create_async_collection(sync_collection)
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
            sync_client = chromadb.PersistentClient(path=str(persist_path))
        elif persist_directory is None:
            sync_client = chromadb.EphemeralClient()
        else:
            sync_client = chromadb.PersistentClient(path=persist_directory)

        self._client_adapter = AsyncClientAdapter(sync_client)
        self._embedding_function = self._get_openclip_embedding()
        sync_collection = self._client_adapter.get_or_create_collection(name=collection_name, embedding_function=self._embedding_function, metadata={"hnsw:space": "cosine"})
        self._collection = self._client_adapter.create_async_collection(sync_collection)

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
        await self._collection.add(ids=[entry_id], images=[image_data], metadatas=[entry_metadata])
        return VectorEntry(id=entry_id, text="[image]", timestamp=timestamp, sender=None, metadata=metadata or {})

    async def query_by_text(self, query_text: str, limit: int = 5) -> list[VectorEntry]:
        """Query images by text description.

        Args:
            query_text: Text description to search for
            limit: Maximum number of results

        Returns:
            List of VectorEntry objects for matching images
        """
        results = await self._collection.query(query_texts=[query_text], n_results=limit, include=["metadatas"])
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
        return await self._collection.count()

    async def clear(self) -> None:
        """Clear all images from the store."""
        self._client_adapter.delete_collection(name=self._collection_name)
        sync_collection = self._client_adapter.get_or_create_collection(name=self._collection_name, embedding_function=self._embedding_function, metadata={"hnsw:space": "cosine"})
        self._collection = self._client_adapter.create_async_collection(sync_collection)
