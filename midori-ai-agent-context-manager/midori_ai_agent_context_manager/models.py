"""Memory entry models for agent conversation history."""

import time

from enum import Enum

from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class MessageRole(str, Enum):
    """Role of a message in a conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ToolCallEntry(BaseModel):
    """Represents a tool call made by the agent."""

    name: str = Field(description="Name of the tool called")
    args: dict[str, Any] = Field(default_factory=dict, description="Arguments passed to the tool")
    result: Optional[str] = Field(default=None, description="Result returned by the tool")
    call_id: Optional[str] = Field(default=None, description="Unique identifier for this tool call")


class MemoryEntry(BaseModel):
    """A single entry in the agent's memory/conversation history."""

    model_config = ConfigDict(use_enum_values=True)

    role: MessageRole = Field(description="Role of the message sender")
    content: str = Field(description="Text content of the message")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of when the entry was created")
    tool_calls: Optional[list[ToolCallEntry]] = Field(default=None, description="Tool calls made in this turn")
    metadata: Optional[dict[str, Any]] = Field(default=None, description="Additional metadata for the entry")


class MemorySnapshot(BaseModel):
    """Complete memory state that can be persisted to disk."""

    agent_id: str = Field(description="Unique identifier for the agent")
    entries: list[MemoryEntry] = Field(default_factory=list, description="List of memory entries")
    summary: Optional[str] = Field(default=None, description="Summary of older entries")
    created_at: float = Field(default_factory=time.time, description="When this snapshot was first created")
    updated_at: float = Field(default_factory=time.time, description="When this snapshot was last updated")
    metadata: Optional[dict[str, Any]] = Field(default=None, description="Additional metadata for the snapshot")
    version: str = Field(default="1.0.0", description="Schema version for migration support")
