"""Main ThinkingCompactor class for consolidating multiple model outputs."""

from typing import Optional

from midori_ai_logger import MidoriAiLogger

from midori_ai_agent_base.models import AgentPayload
from midori_ai_agent_base.protocol import MidoriAiAgentProtocol

from .config import CompactorConfig
from .prompts import build_consolidation_prompt


class ThinkingCompactor:
    """Consolidates multiple reasoning model outputs into a single message.

    This class uses an agent (via MidoriAiAgentProtocol) to intelligently merge
    outputs from any number of reasoning models, supporting any language.

    100% async-friendly implementation.

    Example:
        ```python
        from midori_ai_compactor import ThinkingCompactor
        from midori_ai_agent_base import get_agent

        agent = await get_agent(backend="langchain", model="gpt-4", api_key="...")
        compactor = ThinkingCompactor(agent=agent)

        outputs = ["Analysis 1...", "Analysis 2...", "분석 3..."]
        consolidated = await compactor.compact(outputs)
        ```
    """

    def __init__(self, agent: MidoriAiAgentProtocol, config: Optional[CompactorConfig] = None) -> None:
        """Initialize the ThinkingCompactor.

        Args:
            agent: An instance of MidoriAiAgentProtocol to use for consolidation
            config: Optional configuration for customizing consolidation behavior
        """
        self._agent = agent
        self._config = config if config is not None else CompactorConfig()
        self._logger = MidoriAiLogger(None, name="ThinkingCompactor")

    async def compact(self, outputs: list[str]) -> str:
        """Consolidate multiple model outputs into a single message.

        Args:
            outputs: List of strings from reasoning models (any number, any language)

        Returns:
            A single consolidated string that merges all inputs intelligently
        """
        await self._logger.print(f"Compacting {len(outputs)} outputs", mode="debug")

        if len(outputs) == 0:
            await self._logger.print("No outputs to compact, returning empty string", mode="debug")
            return ""

        if len(outputs) == 1:
            await self._logger.print("Single output, returning as-is", mode="debug")
            return outputs[0]

        prompt = build_consolidation_prompt(outputs, self._config.custom_prompt)

        payload = AgentPayload(user_message=prompt, thinking_blob="", system_context="", user_profile={}, tools_available=[], session_id="compactor-session")

        response = await self._agent.invoke(payload)

        await self._logger.print(f"Compaction complete, response length: {len(response.response)}", mode="debug")

        return response.response
