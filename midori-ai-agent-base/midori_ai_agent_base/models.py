"""Data models for agent protocol payloads and responses."""

from dataclasses import dataclass
from dataclasses import field

from typing import Any
from typing import Literal
from typing import Optional


ReasoningEffortLevel = Literal["none", "minimal", "low", "medium", "high"]
ReasoningSummaryType = Literal["auto", "concise", "detailed"]


@dataclass
class MemoryEntryData:
    """Lightweight representation of a memory entry for payload transport.

    This is a simplified version of MemoryEntry for use in AgentPayload,
    avoiding circular dependencies with the memory package.
    """

    role: str
    content: str
    timestamp: Optional[float] = None
    tool_calls: Optional[list[dict[str, Any]]] = None
    metadata: Optional[dict[str, Any]] = None


@dataclass
class ReasoningEffort:
    """Configuration for LRM reasoning effort.

    This mirrors the OpenAI Reasoning object structure for type-safe
    configuration across all agent backends.

    Note: The `generate_summary` field is part of the OpenAI Reasoning spec but is not
    supported by all providers (e.g., Groq). Adapters will only use `effort` and `summary`
    fields when forwarding to providers that don't support `generate_summary`.

    Attributes:
        effort: The reasoning effort level. Valid values: "none", "minimal", "low", "medium", "high".
        generate_summary: How to generate summaries. Valid values: "auto", "concise", "detailed".
            Note: Not supported by all providers and may be ignored.
        summary: The summary type. Valid values: "auto", "concise", "detailed".
    """

    effort: ReasoningEffortLevel = "low"
    generate_summary: Optional[ReasoningSummaryType] = None
    summary: Optional[ReasoningSummaryType] = None


@dataclass
class AgentPayload:
    """Standardized input for all agent backends."""

    user_message: str
    thinking_blob: str
    system_context: str
    user_profile: dict
    tools_available: list[str]
    session_id: str
    metadata: Optional[dict[str, Any]] = None
    reasoning_effort: Optional[ReasoningEffort] = None
    memory: Optional[list[MemoryEntryData]] = field(default=None)


@dataclass
class AgentResponse:
    """Standardized output from all agent backends."""

    thinking: str
    response: str
    code: Optional[str] = None
    tool_calls: Optional[list[dict[str, Any]]] = None
    metadata: Optional[dict[str, Any]] = None
