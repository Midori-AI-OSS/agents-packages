"""OpenAI Agents SDK implementation using openai-agents library."""

from typing import Any
from typing import Optional

from agents import Agent
from agents import Runner
from agents import RunConfig
from agents import ModelSettings
from agents.models.openai_provider import OpenAIProvider

from openai.types.shared import Reasoning

from midori_ai_logger import MidoriAiLogger

from midori_ai_agent_base.models import AgentPayload
from midori_ai_agent_base.models import AgentResponse
from midori_ai_agent_base.models import MemoryEntryData
from midori_ai_agent_base.protocol import MidoriAiAgentProtocol

from .session import OpenAIAgentSession


class OpenAIAgentsAdapter(MidoriAiAgentProtocol):
    """OpenAI Agents SDK implementation using Agent and Runner.

    This adapter supports two modes of memory management:
    1. Payload-based memory (via `memory` field in AgentPayload) - builds context from entries
    2. Session-based memory (via SQLiteSession) - uses OpenAI agents native session handling

    For session-based memory, create an OpenAIAgentSession and pass it to invoke methods.
    """

    def __init__(self, model: str, api_key: str, base_url: Optional[str] = None, context_window: int = 128000, use_responses: bool = True, db_path: Optional[str] = None) -> None:
        """Initialize the OpenAI Agents adapter.

        Args:
            model: Model name to use
            api_key: API key for authentication
            base_url: Base URL for the API endpoint (optional)
            context_window: Context window size (default: 128000)
            use_responses: Whether to use the responses API (default: True). Set to False for backends like Ollama/LocalAI that don't support it.
            db_path: Path to SQLite database for session storage. If None, session-based memory is disabled by default.
        """
        self._model = model
        self._api_key = api_key
        self._base_url = base_url
        self._context_window = context_window
        self._use_responses = use_responses
        self._db_path = db_path
        self._logger = MidoriAiLogger(None, name="OpenAIAgentsAdapter")
        self._provider = OpenAIProvider(api_key=api_key, base_url=base_url, use_responses=use_responses)
        self._run_config = RunConfig(model=model, model_provider=self._provider)
        self._sessions: dict[str, OpenAIAgentSession] = {}

    def get_session(self, session_id: str) -> OpenAIAgentSession:
        """Get or create a session for the given session ID.

        Args:
            session_id: Unique identifier for the conversation

        Returns:
            OpenAIAgentSession instance for the session
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = OpenAIAgentSession(session_id=session_id, db_path=self._db_path)
        return self._sessions[session_id]

    def close_session(self, session_id: str) -> None:
        """Close and remove a session.

        Args:
            session_id: The session to close
        """
        if session_id in self._sessions:
            self._sessions[session_id].close()
            del self._sessions[session_id]

    def close_all_sessions(self) -> None:
        """Close all open sessions."""
        for session in self._sessions.values():
            session.close()
        self._sessions.clear()

    def _create_agent(self, instructions: str, tools: Optional[list[Any]] = None, model_settings: Optional[ModelSettings] = None) -> Agent:
        """Create an Agent instance with the given instructions.

        Args:
            instructions: System instructions for the agent
            tools: Optional list of tools to bind
            model_settings: Optional model settings including reasoning effort

        Returns:
            Configured Agent instance
        """
        settings = model_settings if model_settings is not None else ModelSettings()
        return Agent(name="MidoriAgent", model=self._model, instructions=instructions, tools=tools or [], model_settings=settings)

    def _build_model_settings(self, payload: AgentPayload) -> Optional[ModelSettings]:
        """Build ModelSettings from payload reasoning effort configuration.

        Args:
            payload: The agent payload containing optional reasoning effort config

        Returns:
            ModelSettings with reasoning configuration, or None if no reasoning effort specified or responses API disabled
        """
        if payload.reasoning_effort is None:
            return None
        if not self._use_responses:
            return None
        re = payload.reasoning_effort
        reasoning_kwargs: dict[str, Any] = {"effort": re.effort}
        if getattr(re, "summary", None) is not None:
            reasoning_kwargs["summary"] = re.summary
        if getattr(re, "generate_summary", None) is not None:
            reasoning_kwargs["generate_summary"] = re.generate_summary
        reasoning = Reasoning(**reasoning_kwargs)
        return ModelSettings(reasoning=reasoning)

    def _build_memory_context(self, memory: list[MemoryEntryData]) -> str:
        """Build a context string from memory entries.

        Args:
            memory: List of memory entries

        Returns:
            Formatted context string
        """
        parts: list[str] = []
        for entry in memory:
            role = entry.role.upper() if isinstance(entry.role, str) else str(entry.role).upper()
            parts.append(f"{role}: {entry.content}")
            if entry.tool_calls:
                for tc in entry.tool_calls:
                    tc_name = tc.get("name", "unknown")
                    tc_result = tc.get("result", "")
                    parts.append(f"  [Tool: {tc_name}] {tc_result}")
        return "\n".join(parts)

    def _extract_from_result(self, result: Any) -> tuple[str, str]:
        """Extract thinking and response text from Runner result.

        Inspects result.new_items for ReasoningItem and MessageOutputItem to extract
        structured reasoning and response text separately.

        Args:
            result: The RunResult from Runner.run()

        Returns:
            Tuple of (thinking_text, response_text)
        """
        thinking_parts: list[str] = []
        response_parts: list[str] = []

        if hasattr(result, "new_items") and result.new_items:
            for item in result.new_items:
                item_type = getattr(item, "type", "")

                if item_type == "reasoning_item":
                    raw_item = getattr(item, "raw_item", None)
                    if raw_item and hasattr(raw_item, "content"):
                        for content_item in raw_item.content:
                            text = getattr(content_item, "text", "")
                            if text:
                                thinking_parts.append(text)

                elif item_type == "message_output_item":
                    raw_item = getattr(item, "raw_item", None)
                    if raw_item and hasattr(raw_item, "content"):
                        for content_item in raw_item.content:
                            text = getattr(content_item, "text", "")
                            if text:
                                response_parts.append(text)

        thinking_text = " ".join(thinking_parts)
        response_text = " ".join(response_parts)

        if not response_text and result.final_output:
            response_text = str(result.final_output)

        return thinking_text, response_text

    async def invoke(self, payload: AgentPayload, session: Optional[OpenAIAgentSession] = None) -> AgentResponse:
        """Process an agent payload and return a response.

        Args:
            payload: The standardized input containing user message, context, etc.
            session: Optional OpenAIAgentSession for session-based memory. If provided,
                     the session's SQLite-backed history is used instead of payload memory.

        Returns:
            AgentResponse with thinking, response, and optional tool calls.
        """
        await self._logger.print(f"Invoking OpenAI Agents for session {payload.session_id}", mode="debug")

        instructions = payload.system_context or "You are a helpful assistant."

        if session is None and payload.memory:
            memory_context = self._build_memory_context(payload.memory)
            instructions = f"{instructions}\n\nConversation history:\n{memory_context}"
        elif session is None and payload.thinking_blob:
            instructions = f"{instructions}\n\nPrevious context: {payload.thinking_blob}"

        model_settings = self._build_model_settings(payload)
        agent = self._create_agent(instructions, model_settings=model_settings)

        if session is not None:
            result = await Runner.run(agent, payload.user_message, run_config=self._run_config, session=session.session)
        else:
            result = await Runner.run(agent, payload.user_message, run_config=self._run_config)

        thinking_text, response_text = self._extract_from_result(result)

        return AgentResponse(thinking=thinking_text, response=response_text)

    async def invoke_with_tools(self, payload: AgentPayload, tools: list[Any], session: Optional[OpenAIAgentSession] = None) -> AgentResponse:
        """Process with tool execution capability.

        Args:
            payload: The standardized input containing user message, context, etc.
            tools: List of tool definitions/callables to bind to the agent.
            session: Optional OpenAIAgentSession for session-based memory.

        Returns:
            AgentResponse with thinking, response, and any tool calls made.
        """
        await self._logger.print(f"Invoking OpenAI Agents with tools for session {payload.session_id}", mode="debug")

        instructions = payload.system_context or "You are a helpful assistant."

        if session is None and payload.memory:
            memory_context = self._build_memory_context(payload.memory)
            instructions = f"{instructions}\n\nConversation history:\n{memory_context}"
        elif session is None and payload.thinking_blob:
            instructions = f"{instructions}\n\nPrevious context: {payload.thinking_blob}"

        model_settings = self._build_model_settings(payload)
        agent = self._create_agent(instructions, tools, model_settings=model_settings)

        if session is not None:
            result = await Runner.run(agent, payload.user_message, run_config=self._run_config, session=session.session)
        else:
            result = await Runner.run(agent, payload.user_message, run_config=self._run_config)

        thinking_text, response_text = self._extract_from_result(result)

        return AgentResponse(thinking=thinking_text, response=response_text)

    async def get_context_window(self) -> int:
        """Return the context window size for this backend.

        Returns:
            Maximum number of tokens the model can process.
        """
        return self._context_window

    async def supports_streaming(self) -> bool:
        """Whether this backend supports streaming responses.

        Returns:
            True - OpenAI Agents supports streaming.
        """
        return True
