"""Abstract base class defining the agent protocol interface."""

from abc import ABC
from abc import abstractmethod

from typing import Any

from .models import AgentPayload
from .models import AgentResponse


class MidoriAiAgentProtocol(ABC):
    """Protocol that all agent backends must implement.

    IMPORTANT: All methods MUST be async-friendly. Use async/await throughout.
    """

    @abstractmethod
    async def invoke(self, payload: AgentPayload) -> AgentResponse:
        """Process an agent payload and return a response.

        Args:
            payload: The standardized input containing user message, context, etc.

        Returns:
            AgentResponse with thinking, response, and optional tool calls.
        """
        ...

    @abstractmethod
    async def invoke_with_tools(self, payload: AgentPayload, tools: list[Any]) -> AgentResponse:
        """Process with tool execution capability.

        Args:
            payload: The standardized input containing user message, context, etc.
            tools: List of tool definitions/callables to bind to the model.

        Returns:
            AgentResponse with thinking, response, and any tool calls made.
        """
        ...

    @abstractmethod
    async def get_context_window(self) -> int:
        """Return the context window size for this backend.

        Returns:
            Maximum number of tokens the model can process.
        """
        ...

    @abstractmethod
    async def supports_streaming(self) -> bool:
        """Whether this backend supports streaming responses.

        Returns:
            True if streaming is supported, False otherwise.
        """
        ...
