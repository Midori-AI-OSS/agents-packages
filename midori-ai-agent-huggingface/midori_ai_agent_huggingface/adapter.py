"""HuggingFace local inference implementation of the Midori AI agent protocol."""

import re
import json
import asyncio

from threading import Thread
from concurrent.futures import ThreadPoolExecutor

from typing import Any
from typing import AsyncIterator

from midori_ai_logger import MidoriAiLogger

from midori_ai_agent_base.models import AgentPayload
from midori_ai_agent_base.models import AgentResponse
from midori_ai_agent_base.models import MemoryEntryData
from midori_ai_agent_base.protocol import MidoriAiAgentProtocol

from .config import DeviceType
from .config import HuggingFaceConfig
from .config import create_config
from .pipeline_manager import PipelineManager


REASONING_PATTERNS = [re.compile(r"<think>(.*?)</think>", re.DOTALL | re.IGNORECASE), re.compile(r"<thinking>(.*?)</thinking>", re.DOTALL | re.IGNORECASE), re.compile(r"<reasoning>(.*?)</reasoning>", re.DOTALL | re.IGNORECASE), re.compile(r"<chain_of_thought>(.*?)</chain_of_thought>", re.DOTALL | re.IGNORECASE)]


class HuggingFaceLocalAgent(MidoriAiAgentProtocol):
    """HuggingFace local inference implementation.

    This adapter runs LLM inference locally using HuggingFace transformers,
    without requiring an external server. It is async-friendly by using
    thread executors for synchronous inference calls.

    IMPORTANT: Model files can be very large (1GB-50GB+). The first inference
    will be slow as the model downloads and loads. Subsequent calls are fast.
    """

    def __init__(self, model: str, device: DeviceType = "auto", torch_dtype: str = "auto", max_new_tokens: int = 512, temperature: float = 0.7, top_p: float = 0.9, top_k: int = 50, do_sample: bool = True, context_window: int = 4096, trust_remote_code: bool = False, load_in_8bit: bool = False, load_in_4bit: bool = False, **kwargs: Any) -> None:
        """Initialize the HuggingFace local agent.

        Args:
            model: HuggingFace model identifier (e.g., 'TinyLlama/TinyLlama-1.1B-Chat-v1.0').
            device: Device to run inference on ('auto', 'cpu', 'cuda', 'mps').
            torch_dtype: Data type for model weights ('auto', 'float16', 'float32', 'bfloat16').
            max_new_tokens: Maximum tokens to generate per response.
            temperature: Sampling temperature (0.0-2.0).
            top_p: Nucleus sampling probability (0.0-1.0).
            top_k: Top-k sampling parameter.
            do_sample: Whether to use sampling (True) or greedy decoding (False).
            context_window: Maximum context window size for the model.
            trust_remote_code: Whether to trust remote code in model files.
            load_in_8bit: Load model in 8-bit precision (requires bitsandbytes).
            load_in_4bit: Load model in 4-bit precision (requires bitsandbytes).
            **kwargs: Additional generation kwargs passed to the model.
        """
        self._config = create_config(model=model, device=device, torch_dtype=torch_dtype, max_new_tokens=max_new_tokens, temperature=temperature, top_p=top_p, top_k=top_k, do_sample=do_sample, context_window=context_window, trust_remote_code=trust_remote_code, load_in_8bit=load_in_8bit, load_in_4bit=load_in_4bit, **kwargs)
        self._pipeline_manager = PipelineManager(self._config)
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._logger = MidoriAiLogger(None, name="HuggingFaceLocalAgent")

    @property
    def config(self) -> HuggingFaceConfig:
        """Get the current configuration."""
        return self._config

    @property
    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self._pipeline_manager.is_loaded

    def _build_memory_context(self, memory: list[MemoryEntryData]) -> str:
        """Build a context string from memory entries.

        Args:
            memory: List of memory entries.

        Returns:
            Formatted context string.
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

    def _extract_reasoning(self, text: str) -> tuple[str, str]:
        """Extract reasoning/thinking content from model output.

        First attempts to use the tokenizer's parse_response() method if available
        (see https://huggingface.co/docs/transformers/main/chat_response_parsing).
        Falls back to regex-based parsing for common reasoning tags used by LRMs
        like DeepSeek-R1, GPT-OSS reasoning models, etc.

        Args:
            text: Raw model output text.

        Returns:
            Tuple of (thinking_text, response_text) where thinking_text contains
            extracted reasoning and response_text is the clean response.
        """
        parsed = self._pipeline_manager.parse_response(text)
        if parsed is not None:
            thinking = parsed.get("thinking", "") or ""
            content = parsed.get("content", "") or parsed.get("response", "") or ""
            if thinking or content:
                return str(thinking), str(content) if content else text.strip()

        thinking_parts: list[str] = []
        clean_text = text

        for pattern in REASONING_PATTERNS:
            matches = pattern.findall(clean_text)
            for match in matches:
                thinking_parts.append(match.strip())
            clean_text = pattern.sub("", clean_text)

        thinking_text = " ".join(thinking_parts)
        response_text = clean_text.strip()

        return thinking_text, response_text

    def _parse_tool_arguments(self, args_str: str) -> dict[str, Any]:
        """Parse tool arguments from string format.

        Supports formats like: arg1=val1, arg2=val2

        Args:
            args_str: String containing arguments.

        Returns:
            Dictionary of parsed arguments.
        """
        args: dict[str, Any] = {}
        if not args_str or not args_str.strip():
            return args

        parts = args_str.split(",")
        for part in parts:
            part = part.strip()
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            key = key.strip()
            value = value.strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            elif value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            elif value.isdigit():
                value = int(value)
            else:
                try:
                    value = float(value)
                except ValueError:
                    pass
            args[key] = value

        return args

    def _parse_tool_calls(self, text: str) -> list[dict[str, Any]]:
        """Parse tool calls from model output.

        Supports multiple formats:
        1. JSON: {"tool_calls": [{"name": "func", "arguments": {...}}]}
        2. Text: TOOL_CALL: func(arg1=val1, arg2=val2)

        Args:
            text: Raw model output text.

        Returns:
            List of tool call dicts with 'name' and 'arguments' keys.
        """
        tool_calls: list[dict[str, Any]] = []

        try:
            data = json.loads(text)
            if isinstance(data, dict) and "tool_calls" in data:
                raw_calls = data["tool_calls"]
                if isinstance(raw_calls, list):
                    for call in raw_calls:
                        if isinstance(call, dict) and "name" in call:
                            tool_calls.append({"name": call["name"], "arguments": call.get("arguments", {})})
                    return tool_calls
        except (json.JSONDecodeError, TypeError):
            pass

        pattern = re.compile(r"TOOL_CALL:\s*(\w+)\((.*?)\)", re.IGNORECASE)
        for match in pattern.finditer(text):
            name = match.group(1)
            args_str = match.group(2)
            try:
                args = self._parse_tool_arguments(args_str)
                tool_calls.append({"name": name, "arguments": args})
            except Exception as e:
                self._logger.print(f"Failed to parse tool arguments for {name}: {e}", mode="error")

        return tool_calls

    def _build_prompt(self, payload: AgentPayload) -> str:
        """Build a prompt from the payload.

        Args:
            payload: The agent payload.

        Returns:
            Formatted prompt string.
        """
        parts: list[str] = []

        if payload.system_context:
            parts.append(f"System: {payload.system_context}")

        if payload.memory:
            memory_context = self._build_memory_context(payload.memory)
            if memory_context:
                parts.append(f"\nConversation history:\n{memory_context}")
        elif payload.thinking_blob:
            parts.append(f"\nPrevious context: {payload.thinking_blob}")

        parts.append(f"\nUser: {payload.user_message}")
        parts.append("\nAssistant:")

        return "\n".join(parts)

    def _sync_invoke(self, payload: AgentPayload) -> AgentResponse:
        """Synchronous invoke implementation.

        Args:
            payload: The agent payload.

        Returns:
            AgentResponse with generated text and parsed tool calls.
        """
        prompt = self._build_prompt(payload)
        raw_response = self._pipeline_manager.generate(prompt)
        thinking_text, response_text = self._extract_reasoning(raw_response)
        tool_calls = self._parse_tool_calls(raw_response)
        return AgentResponse(thinking=thinking_text, response=response_text, tool_calls=tool_calls if tool_calls else None)

    def _sync_invoke_with_tools(self, payload: AgentPayload, tools: list[Any]) -> AgentResponse:
        """Synchronous invoke with tools implementation.

        The tools are included in the prompt as available actions. The model
        may use TOOL_CALL: func(args) or JSON format to indicate tool usage.
        Tool calls are parsed from the response but not automatically executed.

        Args:
            payload: The agent payload.
            tools: List of tool definitions.

        Returns:
            AgentResponse with generated text and parsed tool calls.
        """
        tool_descriptions: list[str] = []
        for tool in tools:
            if callable(tool) and hasattr(tool, "__name__"):
                doc = getattr(tool, "__doc__", "") or ""
                tool_descriptions.append(f"- {tool.__name__}: {doc.split(chr(10))[0]}")
            elif isinstance(tool, dict):
                name = tool.get("name", "unknown")
                desc = tool.get("description", "")
                tool_descriptions.append(f"- {name}: {desc}")

        tools_text = "\n".join(tool_descriptions) if tool_descriptions else "No tools available."

        modified_payload = AgentPayload(user_message=payload.user_message, thinking_blob=payload.thinking_blob, system_context=f"{payload.system_context}\n\nAvailable tools:\n{tools_text}\n\nTo use a tool, output: TOOL_CALL: tool_name(arg1=value1, arg2=value2)", user_profile=payload.user_profile, tools_available=payload.tools_available, session_id=payload.session_id, metadata=payload.metadata, reasoning_effort=payload.reasoning_effort, memory=payload.memory)

        return self._sync_invoke(modified_payload)

    async def invoke(self, payload: AgentPayload) -> AgentResponse:
        """Process an agent payload and return a response.

        Args:
            payload: The standardized input containing user message, context, etc.

        Returns:
            AgentResponse with thinking, response, and optional tool calls.
        """
        await self._logger.print(f"Invoking HuggingFace local agent for session {payload.session_id}", mode="debug")

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, self._sync_invoke, payload)

        return result

    async def invoke_with_tools(self, payload: AgentPayload, tools: list[Any]) -> AgentResponse:
        """Process with tool execution capability.

        Note: Tool support is limited for local models. The tools are described
        in the prompt, but automatic tool execution is not supported. The model
        may describe which tools to use in its response.

        Args:
            payload: The standardized input containing user message, context, etc.
            tools: List of tool definitions/callables to describe to the model.

        Returns:
            AgentResponse with thinking, response, and any tool calls made.
        """
        await self._logger.print(f"Invoking HuggingFace local agent with tools for session {payload.session_id}", mode="debug")

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, self._sync_invoke_with_tools, payload, tools)

        return result

    async def stream(self, payload: AgentPayload) -> AsyncIterator[str]:
        """Stream response tokens from the model.

        Args:
            payload: The standardized input containing user message, context, etc.

        Yields:
            Token strings as they are generated.
        """
        await self._logger.print(f"Streaming HuggingFace local agent for session {payload.session_id}", mode="debug")

        prompt = self._build_prompt(payload)

        await self._pipeline_manager.load_pipeline()
        streamer = self._pipeline_manager.create_streamer()

        generation_kwargs = self._pipeline_manager.get_generation_kwargs()
        generation_kwargs["streamer"] = streamer

        def generate_in_thread() -> None:
            pipeline = self._pipeline_manager._pipeline
            if pipeline:
                pipeline(prompt, **generation_kwargs)

        loop = asyncio.get_event_loop()
        thread = Thread(target=generate_in_thread)
        thread.start()

        try:
            for text in streamer:
                yield text
                await asyncio.sleep(0)
        finally:
            await loop.run_in_executor(None, thread.join)

    async def get_context_window(self) -> int:
        """Return the context window size for this backend.

        Returns:
            Maximum number of tokens the model can process.
        """
        return self._config.context_window

    async def supports_streaming(self) -> bool:
        """Whether this backend supports streaming responses.

        Returns:
            True - Streaming is now supported via TextIteratorStreamer.
        """
        return True

    async def unload_model(self) -> None:
        """Unload the model and free memory.

        Call this when you're done with the agent to release GPU/CPU memory.
        """
        await self._pipeline_manager.unload()

    def __del__(self) -> None:
        """Cleanup executor on deletion."""
        if hasattr(self, "_executor"):
            self._executor.shutdown(wait=False)
