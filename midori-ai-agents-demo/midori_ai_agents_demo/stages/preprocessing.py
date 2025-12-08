"""Preprocessing stage for the reasoning pipeline.

This stage demonstrates:
- Using the midori-ai-agent-base protocol
- Input validation and normalization
- Context preparation
- Error handling patterns
"""

from typing import Optional

from midori_ai_agent_base import AgentPayload
from midori_ai_agent_base import MidoriAiAgentProtocol
from midori_ai_logger import MidoriAiLogger

from ..enums import StageType
from ..models import StageContext

from .base import BaseStage


class PreprocessingStage(BaseStage):
    """Preprocessing stage that validates and prepares input.
    
    This stage demonstrates how to:
    - Use the MidoriAiAgentProtocol from agent-base
    - Build structured prompts for LRM tasks
    - Validate and normalize input
    - Add context and constraints
    
    In a real pipeline, this stage might:
    - Extract entities and keywords
    - Normalize formatting
    - Add relevant background context
    - Validate constraints
    """

    def __init__(self, agent: MidoriAiAgentProtocol, enabled: bool = True, logger: Optional[MidoriAiLogger] = None):
        """Initialize the preprocessing stage.
        
        Args:
            agent: The agent to use for preprocessing (demonstrates protocol usage)
            enabled: Whether this stage should execute
            logger: Optional logger instance
        """
        super().__init__(enabled=enabled, logger=logger)
        self._agent = agent

    @property
    def stage_type(self) -> StageType:
        """Return the stage type."""
        return StageType.PREPROCESSING

    async def _execute(self, context: StageContext) -> str:
        """Preprocess the input using the agent.
        
        This demonstrates:
        1. Building a structured prompt for preprocessing
        2. Using AgentPayload to structure the request
        3. Calling the agent protocol's execute_with_reasoning method
        4. Extracting and returning the result
        
        Args:
            context: Stage context with the original request
            
        Returns:
            Preprocessed and validated input text
        """
        self._logger.info("Preprocessing input with agent protocol")

        prompt = self._build_preprocessing_prompt(context)

        payload = AgentPayload(prompt=prompt, max_tokens=500, temperature=0.3)

        self._logger.debug(f"Sending preprocessing request: {prompt[:100]}...")

        response = await self._agent.execute_with_reasoning(payload)

        self._logger.info(f"Preprocessing complete, result length: {len(response.text)}")

        return response.text

    def _build_preprocessing_prompt(self, context: StageContext) -> str:
        """Build the preprocessing prompt.
        
        This demonstrates how to structure prompts for preprocessing tasks,
        including context and constraints from the original request.
        
        Args:
            context: Stage context with the original request
            
        Returns:
            Formatted prompt for the preprocessing agent
        """
        request = context.request

        prompt_parts = ["You are a preprocessing agent for a reasoning pipeline.", "Your task is to validate, normalize, and prepare the following input for reasoning:", f"\nInput: {request.prompt}"]

        if request.context:
            prompt_parts.append(f"\nContext: {request.context}")

        if request.constraints:
            constraints_text = "\n".join(f"- {c}" for c in request.constraints)

            prompt_parts.append(f"\nConstraints:\n{constraints_text}")

        prompt_parts.append("\nProvide a clear, well-structured version of this task that will be " "easier for downstream reasoning stages to process.")

        return "\n".join(prompt_parts)
