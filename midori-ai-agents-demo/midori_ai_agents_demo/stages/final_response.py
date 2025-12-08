"""Final response stage for the reasoning pipeline.

This stage demonstrates:
- Synthesizing all previous stage results
- Generating a coherent final answer
- Adding metadata and context
- Closing the reasoning loop
"""

from typing import Optional

from midori_ai_agent_base import AgentPayload
from midori_ai_agent_base import MidoriAiAgentProtocol
from midori_ai_logger import MidoriAiLogger

from ..enums import StageType
from ..models import StageContext

from .base import BaseStage


class FinalResponseStage(BaseStage):
    """Final response stage that synthesizes all results into a coherent answer.
    
    This stage demonstrates how to:
    - Gather and synthesize outputs from all previous stages
    - Generate a final, user-facing response
    - Add context and metadata
    - Close the reasoning loop with a clear answer
    
    In a real pipeline, this stage might:
    - Format the response for the target audience
    - Add citations or references
    - Include confidence metrics
    - Provide reasoning transparency
    """

    def __init__(self, agent: MidoriAiAgentProtocol, enabled: bool = True, logger: Optional[MidoriAiLogger] = None):
        """Initialize the final response stage.
        
        Args:
            agent: The agent to use for response synthesis
            enabled: Whether this stage should execute
            logger: Optional logger instance
        """
        super().__init__(enabled=enabled, logger=logger)
        self._agent = agent

    @property
    def stage_type(self) -> StageType:
        """Return the stage type."""
        return StageType.FINAL_RESPONSE

    async def _execute(self, context: StageContext) -> str:
        """Synthesize all stage results into a final response.
        
        This demonstrates:
        1. Gathering outputs from all previous stages
        2. Building a synthesis prompt
        3. Using the agent to generate a coherent final answer
        4. Including relevant context and metadata
        
        Args:
            context: Stage context with all previous stage results
            
        Returns:
            The final synthesized response
        """
        self._logger.info("Synthesizing final response from all stages")

        synthesis_prompt = self._build_synthesis_prompt(context)

        self._logger.debug(f"Created synthesis prompt: {len(synthesis_prompt)} chars")

        payload = AgentPayload(prompt=synthesis_prompt, max_tokens=1500, temperature=0.5)

        response = await self._agent.execute_with_reasoning(payload)

        self._logger.info(f"Final response generated: {len(response.text)} chars")

        return response.text

    def _build_synthesis_prompt(self, context: StageContext) -> str:
        """Build the prompt for synthesizing the final response.
        
        This demonstrates how to structure a synthesis prompt that
        incorporates results from all previous stages.
        
        Args:
            context: Stage context with all previous results
            
        Returns:
            Formatted prompt for response synthesis
        """
        prompt_parts = ["You are synthesizing the final response for a reasoning pipeline.", f"\nOriginal request: {context.request.prompt}"]

        if context.request.context:
            prompt_parts.append(f"\nContext: {context.request.context}")

        prompt_parts.append("\nIntermediate results from the pipeline:")

        for result in context.previous_results:
            if result.output and result.stage_type != StageType.FINAL_RESPONSE:
                stage_name = result.stage_type.value.replace("_", " ").title()

                output_preview = result.output[:500] + "..." if len(result.output) > 500 else result.output

                prompt_parts.append(f"\n{stage_name}:\n{output_preview}")

        prompt_parts.append("\nProvide a clear, comprehensive final answer that synthesizes all the " "reasoning above. Be concise but complete, and ensure the response " "directly addresses the original request.")

        if context.request.constraints:
            constraints_text = "\n".join(f"- {c}" for c in context.request.constraints)

            prompt_parts.append(f"\nEnsure your response satisfies these constraints:\n{constraints_text}")

        return "\n".join(prompt_parts)
