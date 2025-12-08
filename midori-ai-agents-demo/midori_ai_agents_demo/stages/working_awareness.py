"""Working awareness stage for the reasoning pipeline.

This stage demonstrates:
- Parallel execution with asyncio.gather
- Multiple reasoning perspectives
- Concurrent agent calls
- Aggregating parallel results
"""

import asyncio

from typing import List
from typing import Optional

from midori_ai_agent_base import AgentPayload
from midori_ai_agent_base import MidoriAiAgentProtocol
from midori_ai_logger import MidoriAiLogger

from ..enums import StageType
from ..models import StageContext

from .base import BaseStage


class WorkingAwarenessStage(BaseStage):
    """Working awareness stage that generates multiple reasoning perspectives.
    
    This stage demonstrates how to:
    - Execute multiple reasoning tasks in parallel
    - Use asyncio.gather for concurrent operations
    - Combine multiple perspectives into a coherent result
    - Handle errors in parallel execution
    
    In a real pipeline, this stage might:
    - Generate multiple reasoning approaches
    - Explore different solution paths
    - Validate reasoning from different angles
    - Detect contradictions or gaps
    """

    def __init__(self, agent: MidoriAiAgentProtocol, num_perspectives: int = 3, enabled: bool = True, logger: Optional[MidoriAiLogger] = None):
        """Initialize the working awareness stage.
        
        Args:
            agent: The agent to use for reasoning
            num_perspectives: Number of parallel reasoning perspectives to generate
            enabled: Whether this stage should execute
            logger: Optional logger instance
        """
        super().__init__(enabled=enabled, logger=logger)
        self._agent = agent
        self._num_perspectives = num_perspectives

    @property
    def stage_type(self) -> StageType:
        """Return the stage type."""
        return StageType.WORKING_AWARENESS

    async def _execute(self, context: StageContext) -> str:
        """Generate multiple reasoning perspectives in parallel.
        
        This demonstrates:
        1. Creating multiple reasoning prompts with different angles
        2. Using asyncio.gather to execute them in parallel
        3. Handling errors in parallel execution
        4. Combining results into a unified output
        
        Args:
            context: Stage context with request and previous results
            
        Returns:
            Combined output from all reasoning perspectives
        """
        self._logger.info(f"Generating {self._num_perspectives} reasoning perspectives in parallel")

        preprocessed_input = self._get_preprocessed_input(context)

        perspective_prompts = self._generate_perspective_prompts(preprocessed_input)

        self._logger.debug(f"Created {len(perspective_prompts)} perspective prompts")

        perspective_tasks = [self._reason_from_perspective(prompt, i) for i, prompt in enumerate(perspective_prompts)]

        results = await asyncio.gather(*perspective_tasks, return_exceptions=True)

        valid_results = [r for r in results if isinstance(r, str)]

        errors = [r for r in results if isinstance(r, Exception)]

        if errors:
            self._logger.warning(f"Some perspectives failed: {len(errors)} errors")

        if not valid_results:
            raise RuntimeError("All reasoning perspectives failed")

        self._logger.info(f"Successfully generated {len(valid_results)} perspectives")

        combined_output = self._combine_perspectives(valid_results)

        return combined_output

    def _get_preprocessed_input(self, context: StageContext) -> str:
        """Extract the preprocessed input from previous stages.
        
        Args:
            context: Stage context with previous results
            
        Returns:
            Preprocessed input or original prompt if preprocessing was skipped
        """
        for result in reversed(context.previous_results):
            if result.stage_type == StageType.PREPROCESSING and result.output:
                return result.output

        return context.request.prompt

    def _generate_perspective_prompts(self, input_text: str) -> List[str]:
        """Generate prompts for different reasoning perspectives.
        
        This demonstrates how to create diverse reasoning approaches
        by framing the same problem from different angles.
        
        Args:
            input_text: The preprocessed input to reason about
            
        Returns:
            List of prompts for different reasoning perspectives
        """
        perspectives = [
            f"Analyze this problem from a logical, step-by-step perspective:\n{input_text}",
            f"Consider this problem from a creative, intuitive perspective:\n{input_text}",
            f"Examine this problem critically, identifying potential issues:\n{input_text}",
        ]

        return perspectives[: self._num_perspectives]

    async def _reason_from_perspective(self, prompt: str, perspective_index: int) -> str:
        """Reason from a single perspective.
        
        Args:
            prompt: The perspective prompt
            perspective_index: Index of this perspective (for logging)
            
        Returns:
            Reasoning output from this perspective
            
        Raises:
            Exception: If reasoning fails
        """
        self._logger.debug(f"Starting perspective {perspective_index}")

        payload = AgentPayload(prompt=prompt, max_tokens=1000, temperature=0.7)

        response = await self._agent.execute_with_reasoning(payload)

        self._logger.debug(f"Perspective {perspective_index} complete: {len(response.text)} chars")

        return response.text

    def _combine_perspectives(self, perspectives: List[str]) -> str:
        """Combine multiple reasoning perspectives into a unified output.
        
        This is a simple demonstration - a production system might use
        more sophisticated synthesis techniques.
        
        Args:
            perspectives: List of reasoning outputs from different perspectives
            
        Returns:
            Combined reasoning output
        """
        combined_parts = ["Multiple reasoning perspectives:"]

        for i, perspective in enumerate(perspectives, 1):
            combined_parts.append(f"\nPerspective {i}:\n{perspective}")

        return "\n".join(combined_parts)
