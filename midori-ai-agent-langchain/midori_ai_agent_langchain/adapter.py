"""Langchain-based agent implementation."""

from typing import Any
from typing import Optional
from typing import Union

from langchain_openai import ChatOpenAI

from langchain_core.messages import AIMessage
from langchain_core.messages import HumanMessage
from langchain_core.messages import SystemMessage
from langchain_core.messages import ToolMessage
from langchain_core.runnables import Runnable

from midori_ai_logger import MidoriAiLogger

from midori_ai_agent_base.models import AgentPayload
from midori_ai_agent_base.models import AgentResponse
from midori_ai_agent_base.models import MemoryEntryData
from midori_ai_agent_base.models import ReasoningEffort
from midori_ai_agent_base.parsing import parse_structured_response
from midori_ai_agent_base.protocol import MidoriAiAgentProtocol


LangchainMessage = Union[SystemMessage, HumanMessage, AIMessage, ToolMessage]


class LangchainAgent(MidoriAiAgentProtocol):
    """Langchain-based agent implementation. 100% async."""

    def __init__(self, model: str, api_key: str, base_url: str, temperature: float = 0.2, context_window: int = 128000, use_responses_api: bool = True, **kwargs: Any) -> None:
        """Initialize the Langchain agent.

        Args:
            model: Model name to use
            api_key: API key for authentication
            base_url: Base URL for the API endpoint
            temperature: Sampling temperature (default: 0.2)
            context_window: Context window size (default: 128000)
            use_responses_api: Whether to use the responses API (default: True). Set to False for backends like Ollama/LocalAI that don't support it.
            **kwargs: Additional arguments passed to ChatOpenAI
        """
        self._use_responses_api = use_responses_api
        self._model = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_completion_tokens=None,
            timeout=None,
            max_retries=1,
            use_responses_api=use_responses_api,
            **kwargs
        )
        self._context_window = context_window
        self._logger = MidoriAiLogger(None, name="LangchainAgent")

    def _memory_entry_to_message(self, entry: MemoryEntryData) -> Optional[LangchainMessage]:
        """Convert a MemoryEntryData to a Langchain message.

        Args:
            entry: The memory entry to convert

        Returns:
            Langchain message or None if role is unknown
        """
        role = entry.role.lower() if isinstance(entry.role, str) else str(entry.role)
        if role == "user":
            return HumanMessage(content=entry.content)
        elif role == "assistant":
            return AIMessage(content=entry.content)
        elif role == "system":
            return SystemMessage(content=entry.content)
        elif role == "tool":
            tool_call_id = "unknown"
            if entry.tool_calls and len(entry.tool_calls) > 0:
                call_id = entry.tool_calls[0].get("call_id")
                tool_call_id = call_id if call_id else "unknown"
            return ToolMessage(content=entry.content, tool_call_id=tool_call_id)
        return None

    def _build_messages(self, payload: AgentPayload) -> list[LangchainMessage]:
        """Build Langchain messages from payload.

        Args:
            payload: The agent payload to convert

        Returns:
            List of Langchain message objects
        """
        messages: list[LangchainMessage] = []

        if payload.system_context:
            messages.append(SystemMessage(content=payload.system_context))

        if payload.memory:
            for entry in payload.memory:
                msg = self._memory_entry_to_message(entry)
                if msg is not None:
                    messages.append(msg)
        elif payload.thinking_blob:
            messages.append(AIMessage(content=payload.thinking_blob))

        messages.append(HumanMessage(content=payload.user_message))

        return messages

    def _apply_reasoning(self, model: Runnable, reasoning_effort: Optional[ReasoningEffort]) -> Runnable:
        """Apply reasoning effort configuration to the model.

        Args:
            model: The LangChain runnable (ChatOpenAI or bound variant)
            reasoning_effort: Optional reasoning effort configuration

        Returns:
            Model with reasoning configuration applied via bind (only if responses API is enabled)
        """
        if reasoning_effort is None:
            return model
        if not self._use_responses_api:
            return model
        reasoning_dict: dict[str, Any] = {"effort": reasoning_effort.effort}
        if getattr(reasoning_effort, "summary", None) is not None:
            reasoning_dict["summary"] = reasoning_effort.summary
        if getattr(reasoning_effort, "generate_summary", None) is not None:
            reasoning_dict["generate_summary"] = reasoning_effort.generate_summary
        return model.bind(reasoning=reasoning_dict)

    def _parse_response(self, result: Any, with_tools: bool = False) -> AgentResponse:
        """Parse Langchain response into AgentResponse.

        Args:
            result: The raw response from Langchain (typically AIMessage)
            with_tools: Whether tool calls were expected

        Returns:
            Standardized AgentResponse
        """
        if hasattr(result, "content"):
            content = result.content
        else:
            content = result

        thinking_text, response_text = parse_structured_response(content)

        if not response_text and hasattr(result, "content"):
            response_text = str(result.content) if result.content else str(result)
        elif not response_text:
            response_text = str(result)

        tool_calls: Optional[list[dict[str, Any]]] = None

        if with_tools and hasattr(result, "tool_calls") and result.tool_calls:
            tool_calls = [{"name": tc.get("name", ""), "args": tc.get("args", {})} for tc in result.tool_calls]

        return AgentResponse(thinking=thinking_text, response=response_text, tool_calls=tool_calls)

    async def invoke(self, payload: AgentPayload) -> AgentResponse:
        """Process an agent payload and return a response.

        Args:
            payload: The standardized input containing user message, context, etc.

        Returns:
            AgentResponse with thinking, response, and optional tool calls.
        """
        await self._logger.print(f"Invoking with payload for session {payload.session_id}", mode="debug")
        messages = self._build_messages(payload)
        model = self._apply_reasoning(self._model, payload.reasoning_effort)
        result = await model.ainvoke(messages)
        return self._parse_response(result)

    async def invoke_with_tools(self, payload: AgentPayload, tools: list[Any]) -> AgentResponse:
        """Process with tool execution capability.

        Args:
            payload: The standardized input containing user message, context, etc.
            tools: List of tool definitions/callables to bind to the model.

        Returns:
            AgentResponse with thinking, response, and any tool calls made.
        """
        await self._logger.print(f"Invoking with tools for session {payload.session_id}", mode="debug")
        bound_model = self._model.bind_tools(tools)
        model = self._apply_reasoning(bound_model, payload.reasoning_effort)
        messages = self._build_messages(payload)
        result = await model.ainvoke(messages)
        return self._parse_response(result, with_tools=True)

    async def get_context_window(self) -> int:
        """Return the context window size for this backend.

        Returns:
            Maximum number of tokens the model can process.
        """
        return self._context_window

    async def supports_streaming(self) -> bool:
        """Whether this backend supports streaming responses.

        Returns:
            True - Langchain supports streaming.
        """
        return True
