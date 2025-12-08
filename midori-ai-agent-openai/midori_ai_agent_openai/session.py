"""Session wrapper for OpenAI agents using the MemoryStore or SQLiteSession.

This module provides utilities to integrate with the OpenAI agents SDK's
session-based memory management, allowing both in-memory and SQLite-based
persistence options.
"""

from pathlib import Path

from typing import Any
from typing import Optional

from agents.memory import SQLiteSession


class OpenAIAgentSession:
    """Wrapper class to manage OpenAI agent sessions with optional SQLite persistence.

    This class provides a clean interface for managing agent conversations
    using the OpenAI agents SDK's native session handling. It supports both
    in-memory sessions (default) and SQLite-based persistent storage.

    Usage:
        # In-memory session (lost when process ends)
        session = OpenAIAgentSession(session_id="chat-123")

        # Persistent SQLite session
        session = OpenAIAgentSession(
            session_id="chat-123",
            db_path="/data/conversations.db"
        )

        # Use with Runner.run
        result = await Runner.run(agent, message, session=session.session)
    """

    def __init__(self, session_id: str, db_path: Optional[str] = None, sessions_table: str = "agent_sessions", messages_table: str = "agent_messages") -> None:
        """Initialize the OpenAI agent session.

        Args:
            session_id: Unique identifier for the conversation session
            db_path: Path to SQLite database. If None, uses in-memory database.
            sessions_table: Name of the sessions table in the database
            messages_table: Name of the messages table in the database
        """
        self._session_id = session_id
        self._db_path = db_path if db_path else ":memory:"
        self._session = SQLiteSession(session_id=session_id, db_path=self._db_path, sessions_table=sessions_table, messages_table=messages_table)

    @property
    def session(self) -> SQLiteSession:
        """Return the underlying SQLiteSession for use with Runner.run."""
        return self._session

    @property
    def session_id(self) -> str:
        """Return the session ID."""
        return self._session_id

    @property
    def db_path(self) -> str:
        """Return the database path."""
        return self._db_path

    async def get_items(self, limit: Optional[int] = None) -> list[Any]:
        """Retrieve conversation history items.

        Args:
            limit: Maximum number of items to retrieve

        Returns:
            List of conversation items
        """
        return await self._session.get_items(limit)

    async def add_items(self, items: list[Any]) -> None:
        """Add items to the conversation history.

        Args:
            items: List of items to add
        """
        await self._session.add_items(items)

    async def clear(self) -> None:
        """Clear all items from the session."""
        await self._session.clear_session()

    async def pop_item(self) -> Optional[Any]:
        """Remove and return the most recent item.

        Returns:
            The most recent item or None if empty
        """
        return await self._session.pop_item()

    def close(self) -> None:
        """Close the database connection."""
        self._session.close()

    def __enter__(self) -> "OpenAIAgentSession":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - closes the session."""
        self.close()

    async def __aenter__(self) -> "OpenAIAgentSession":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit - closes the session."""
        self.close()
