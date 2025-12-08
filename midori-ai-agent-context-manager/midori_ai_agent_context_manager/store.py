"""Memory store for in-RAM storage with async file persistence."""

import time

import aiofiles
import aiofiles.os

from pathlib import Path

from typing import Any
from typing import Iterator
from typing import Optional

from .models import MemoryEntry
from .models import MemorySnapshot
from .models import MessageRole
from .models import ToolCallEntry


class MemoryStore:
    """In-memory storage for agent conversation history with async persistence.

    The MemoryStore maintains conversation history in RAM and provides async
    methods to persist and load from JSON files using Pydantic serialization.

    Usage:
        memory = MemoryStore(agent_id="my-agent")
        memory.add_user_message("Hello!")
        memory.add_assistant_message("Hi there!")
        await memory.save("/path/to/memory.json")

        # Later...
        memory = MemoryStore(agent_id="my-agent")
        await memory.load("/path/to/memory.json")
    """

    def __init__(self, agent_id: str, max_entries: Optional[int] = None) -> None:
        """Initialize the memory store.

        Args:
            agent_id: Unique identifier for the agent
            max_entries: Optional maximum number of entries to retain (None = unlimited)
        """
        self._agent_id = agent_id
        self._max_entries = max_entries
        self._entries: list[MemoryEntry] = []
        self._summary: Optional[str] = None
        self._created_at: float = time.time()
        self._updated_at: float = time.time()
        self._metadata: dict[str, Any] = {}
        self._file_path: Optional[Path] = None

    @property
    def agent_id(self) -> str:
        """Return the agent ID."""
        return self._agent_id

    @property
    def entries(self) -> list[MemoryEntry]:
        """Return the list of memory entries."""
        return self._entries.copy()

    @property
    def summary(self) -> Optional[str]:
        """Return the conversation summary."""
        return self._summary

    @summary.setter
    def summary(self, value: Optional[str]) -> None:
        """Set the conversation summary."""
        self._summary = value
        self._updated_at = time.time()

    @property
    def metadata(self) -> dict[str, Any]:
        """Return the metadata dictionary."""
        return self._metadata.copy()

    def set_metadata(self, key: str, value: Any) -> None:
        """Set a metadata value."""
        self._metadata[key] = value
        self._updated_at = time.time()

    def add_entry(self, entry: MemoryEntry) -> None:
        """Add a memory entry to the store.

        Args:
            entry: The memory entry to add
        """
        self._entries.append(entry)
        self._updated_at = time.time()
        self._trim_if_needed()

    def add_user_message(self, content: str, metadata: Optional[dict[str, Any]] = None) -> MemoryEntry:
        """Add a user message to the memory.

        Args:
            content: The message content
            metadata: Optional metadata for the entry

        Returns:
            The created memory entry
        """
        entry = MemoryEntry(role=MessageRole.USER, content=content, metadata=metadata)
        self.add_entry(entry)
        return entry

    def add_assistant_message(self, content: str, tool_calls: Optional[list[ToolCallEntry]] = None, metadata: Optional[dict[str, Any]] = None) -> MemoryEntry:
        """Add an assistant message to the memory.

        Args:
            content: The message content
            tool_calls: Optional list of tool calls made
            metadata: Optional metadata for the entry

        Returns:
            The created memory entry
        """
        entry = MemoryEntry(role=MessageRole.ASSISTANT, content=content, tool_calls=tool_calls, metadata=metadata)
        self.add_entry(entry)
        return entry

    def add_system_message(self, content: str, metadata: Optional[dict[str, Any]] = None) -> MemoryEntry:
        """Add a system message to the memory.

        Args:
            content: The message content
            metadata: Optional metadata for the entry

        Returns:
            The created memory entry
        """
        entry = MemoryEntry(role=MessageRole.SYSTEM, content=content, metadata=metadata)
        self.add_entry(entry)
        return entry

    def add_tool_result(self, tool_name: str, result: str, call_id: Optional[str] = None, metadata: Optional[dict[str, Any]] = None) -> MemoryEntry:
        """Add a tool result message to the memory.

        Args:
            tool_name: Name of the tool that was called
            result: The result returned by the tool
            call_id: Optional unique identifier for the tool call
            metadata: Optional metadata for the entry

        Returns:
            The created memory entry
        """
        tool_call = ToolCallEntry(name=tool_name, result=result, call_id=call_id)
        entry = MemoryEntry(role=MessageRole.TOOL, content=result, tool_calls=[tool_call], metadata=metadata)
        self.add_entry(entry)
        return entry

    def get_recent_entries(self, count: int) -> list[MemoryEntry]:
        """Get the most recent entries.

        Args:
            count: Number of entries to return

        Returns:
            List of the most recent memory entries
        """
        return self._entries[-count:] if count > 0 else []

    def get_entries_since(self, timestamp: float) -> list[MemoryEntry]:
        """Get entries since a given timestamp.

        Args:
            timestamp: Unix timestamp

        Returns:
            List of entries created after the timestamp
        """
        return [e for e in self._entries if e.timestamp > timestamp]

    def clear(self) -> None:
        """Clear all entries from the memory."""
        self._entries = []
        self._summary = None
        self._updated_at = time.time()

    def _trim_if_needed(self) -> None:
        """Trim entries if max_entries is set and exceeded."""
        if self._max_entries is not None and len(self._entries) > self._max_entries:
            excess = len(self._entries) - self._max_entries
            self._entries = self._entries[excess:]

    def to_snapshot(self) -> MemorySnapshot:
        """Create a MemorySnapshot from the current state.

        Returns:
            MemorySnapshot containing all current data
        """
        return MemorySnapshot(agent_id=self._agent_id, entries=self._entries.copy(), summary=self._summary, created_at=self._created_at, updated_at=self._updated_at, metadata=self._metadata.copy() if self._metadata else None)

    def from_snapshot(self, snapshot: MemorySnapshot) -> None:
        """Restore state from a MemorySnapshot.

        Args:
            snapshot: The snapshot to restore from
        """
        self._agent_id = snapshot.agent_id
        self._entries = snapshot.entries.copy()
        self._summary = snapshot.summary
        self._created_at = snapshot.created_at
        self._updated_at = snapshot.updated_at
        self._metadata = snapshot.metadata.copy() if snapshot.metadata else {}

    async def save(self, file_path: Optional[str] = None) -> None:
        """Save the memory to a JSON file.

        Args:
            file_path: Path to save to. If None, uses the last loaded/saved path.

        Raises:
            ValueError: If no file path is provided and none was previously set
        """
        if file_path is not None:
            self._file_path = Path(file_path)
        if self._file_path is None:
            raise ValueError("No file path specified. Provide a path or load from a file first.")
        path = self._file_path
        parent = path.parent
        if not await aiofiles.os.path.exists(parent):
            await aiofiles.os.makedirs(parent)
        snapshot = self.to_snapshot()
        json_data = snapshot.model_dump_json(indent=2)
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(json_data)

    async def load(self, file_path: str) -> bool:
        """Load memory from a JSON file.

        Args:
            file_path: Path to load from

        Returns:
            True if loaded successfully, False if file doesn't exist
        """
        path = Path(file_path)
        self._file_path = path
        if not await aiofiles.os.path.exists(path):
            return False
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            json_data = await f.read()
        snapshot = MemorySnapshot.model_validate_json(json_data)
        self.from_snapshot(snapshot)
        return True

    def __len__(self) -> int:
        """Return the number of entries in the memory."""
        return len(self._entries)

    def __iter__(self) -> Iterator[MemoryEntry]:
        """Iterate over the memory entries."""
        return iter(self._entries)
