"""LanceDB backend implementation for vector storage.

This module provides LanceDB-backed vector storage implementation
with support for text content using columnar storage format.
"""

from __future__ import annotations

import json
import time
import uuid
import lancedb

import pyarrow as pa

from typing import Any
from typing import Optional

from midori_ai_logger import MidoriAiLogger

from ..enums import SenderType
from ..models import VectorEntry
from ..config import DEFAULT_PERSIST_PATH
from ..protocol import VectorStoreProtocol


_logger = MidoriAiLogger(None, name="VectorManager.LanceDB")


def generate_time_based_id() -> str:
    """Generate a time-based unique ID.

    Returns:
        String ID with timestamp prefix for natural ordering
    """
    timestamp_ms = int(time.time() * 1000)
    unique_suffix = uuid.uuid4().hex[:8]
    return f"{timestamp_ms}-{unique_suffix}"


class LanceVectorStore(VectorStoreProtocol):
    """LanceDB-based vector storage implementation.

    Provides persistent vector storage using LanceDB's columnar format
    with time-based IDs and support for metadata filtering and semantic
    similarity search.

    Note:
        LanceDB is an embedded database with excellent Python support
        and fast columnar storage. It requires the 'lancedb' optional
        dependency to be installed.
    """

    def __init__(self, table_name: str, persist_directory: Optional[str] = "default", embedding_function: Optional[Any] = None) -> None:
        """Initialize LanceDB storage.

        Args:
            table_name: Name for the LanceDB table
            persist_directory: Directory for persistence.
                - "default": Uses ~/.midoriai/vectorstore/lancedb/
                - None: Uses in-memory storage (not persistent)
                - str: Uses the specified path
            embedding_function: Optional custom embedding function.
                If None, LanceDB uses its default embeddings.

        Note:
            The embedding function should be consistent for a given table.
            Changing embeddings after data is stored may cause issues with
            similarity search. LanceDB stores data in columnar format which
            is efficient for analytical queries.
        """

        self._table_name = table_name
        self._embedding_function = embedding_function

        if persist_directory == "default":
            persist_path = DEFAULT_PERSIST_PATH / "lancedb"
            persist_path.mkdir(parents=True, exist_ok=True)
            self._db = lancedb.connect(str(persist_path))
        elif persist_directory is None:
            self._db = lancedb.connect(":memory:")
        else:
            self._db = lancedb.connect(persist_directory)

        self._table = self._get_or_create_table()
        _logger.rprint(f"Initialized LanceVectorStore table: {table_name}", mode="debug")

    def _get_or_create_table(self) -> Any:
        """Get existing table or create new one."""

        if self._table_name in self._db.table_names():
            return self._db.open_table(self._table_name)

        schema = pa.schema([pa.field("id", pa.string()), pa.field("text", pa.string()), pa.field("timestamp", pa.float64()), pa.field("sender", pa.string()), pa.field("metadata", pa.string())])
        return self._db.create_table(self._table_name, schema=schema)

    async def store(self, text: str, sender: Optional[SenderType] = None, metadata: Optional[dict[str, Any]] = None) -> VectorEntry:
        """Store text with optional sender and metadata.

        Args:
            text: Text content to store
            sender: Optional sender type for reranking
            metadata: Optional additional metadata

        Returns:
            The created VectorEntry
        """
        entry_id = generate_time_based_id()
        timestamp = time.time()
        entry = VectorEntry(id=entry_id, text=text, timestamp=timestamp, sender=sender, metadata=metadata or {})
        data = [{"id": entry_id, "text": text, "timestamp": timestamp, "sender": sender.value if sender else "", "metadata": json.dumps(metadata or {})}]
        self._table.add(data)
        _logger.rprint(f"Stored entry {entry_id} in table {self._table_name}", mode="debug")
        return entry

    async def get_by_id(self, entry_id: str) -> Optional[VectorEntry]:
        """Get a single entry by ID.

        Args:
            entry_id: The unique identifier of the entry

        Returns:
            The VectorEntry if found, None otherwise
        """
        results = self._table.search().where(f"id = '{entry_id}'").limit(1).to_list()
        if not results:
            return None
        row = results[0]
        sender = SenderType(row["sender"]) if row["sender"] else None
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        return VectorEntry(id=row["id"], text=row["text"], timestamp=row["timestamp"], sender=sender, metadata=metadata)

    async def query(self, filters: dict[str, Any], limit: int = 100) -> list[VectorEntry]:
        """Query entries matching metadata filters.

        Args:
            filters: Metadata filters to apply (empty dict returns all entries)
            limit: Maximum number of entries to return

        Returns:
            List of matching VectorEntry objects
        """
        query = self._table.search()
        if filters:
            where_clauses = []
            for key, value in filters.items():
                if isinstance(value, str):
                    where_clauses.append(f"metadata LIKE '%\"{key}\": \"{value}\"%'")
                else:
                    where_clauses.append(f"metadata LIKE '%\"{key}\": {value}%'")
            if where_clauses:
                query = query.where(" AND ".join(where_clauses))

        results = query.limit(limit).to_list()
        entries = []
        for row in results:
            sender = SenderType(row["sender"]) if row["sender"] else None
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            entries.append(VectorEntry(id=row["id"], text=row["text"], timestamp=row["timestamp"], sender=sender, metadata=metadata))
        return sorted(entries, key=lambda e: e.timestamp)

    async def search_similar(self, query_text: str, limit: int = 10) -> list[VectorEntry]:
        """Semantic similarity search.

        Args:
            query_text: Text to search for similar entries
            limit: Maximum number of entries to return

        Returns:
            List of VectorEntry objects ranked by similarity
        """
        if self._embedding_function:
            query_embedding = self._embedding_function([query_text])[0]
            results = self._table.search(query_embedding).limit(limit).to_list()
        else:
            results = self._table.search(query_text).limit(limit).to_list()

        entries = []
        for row in results:
            sender = SenderType(row["sender"]) if row["sender"] else None
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            entries.append(VectorEntry(id=row["id"], text=row["text"], timestamp=row["timestamp"], sender=sender, metadata=metadata))
        return entries

    async def delete(self, entry_ids: list[str]) -> int:
        """Delete entries by IDs.

        Args:
            entry_ids: List of entry IDs to delete

        Returns:
            Number of entries deleted
        """
        if not entry_ids:
            return 0
        ids_str = ", ".join(f"'{id}'" for id in entry_ids)
        self._table.delete(f"id IN ({ids_str})")
        _logger.rprint(f"Deleted {len(entry_ids)} entries from table {self._table_name}", mode="debug")
        return len(entry_ids)

    async def count(self) -> int:
        """Return total entry count."""
        return self._table.count_rows()

    async def clear(self) -> None:
        """Clear all entries from the store."""
        self._db.drop_table(self._table_name)
        self._table = self._get_or_create_table()
        _logger.rprint(f"Cleared table {self._table_name}", mode="debug")
