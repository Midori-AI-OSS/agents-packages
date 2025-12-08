"""Compaction stage for the reasoning pipeline.

This stage demonstrates:
- Integration with midori-ai-compactor package
- Consolidating multiple reasoning outputs
- Deduplication of redundant thinking
- Output synthesis
"""

from typing import List
from typing import Optional

from midori_ai_compactor import ThinkingCompactor
from midori_ai_logger import MidoriAiLogger

from ..enums import StageType
from ..models import StageContext

from .base import BaseStage


class CompactionStage(BaseStage):
    """Compaction stage that consolidates multiple reasoning outputs.
    
    This stage demonstrates how to:
    - Use the ThinkingCompactor from midori-ai-compactor
    - Extract outputs from previous stages
    - Deduplicate and consolidate thinking
    - Handle cases with single or multiple outputs
    
    In a real pipeline, this stage might:
    - Remove redundant reasoning steps
    - Identify contradictions
    - Synthesize a coherent narrative
    - Compress verbose outputs
    """

    def __init__(self, compactor: ThinkingCompactor, enabled: bool = True, logger: Optional[MidoriAiLogger] = None):
        """Initialize the compaction stage.
        
        Args:
            compactor: ThinkingCompactor instance to use
            enabled: Whether this stage should execute
            logger: Optional logger instance
        """
        super().__init__(enabled=enabled, logger=logger)
        self._compactor = compactor

    @property
    def stage_type(self) -> StageType:
        """Return the stage type."""
        return StageType.COMPACTION

    async def _execute(self, context: StageContext) -> str:
        """Compact multiple reasoning outputs into a consolidated result.
        
        This demonstrates:
        1. Extracting outputs from previous stages
        2. Using ThinkingCompactor to consolidate them
        3. Handling edge cases (no outputs, single output)
        4. Returning the compacted result
        
        Args:
            context: Stage context with previous stage results
            
        Returns:
            Compacted and consolidated reasoning output
        """
        self._logger.info("Starting compaction of reasoning outputs")

        outputs = self._extract_reasoning_outputs(context)

        self._logger.debug(f"Extracted {len(outputs)} outputs to compact")

        if not outputs:
            self._logger.warning("No outputs to compact, returning empty result")

            return "No reasoning outputs available for compaction"

        if len(outputs) == 1:
            self._logger.info("Only one output, no compaction needed")

            return outputs[0]

        self._logger.info(f"Compacting {len(outputs)} outputs using ThinkingCompactor")

        compacted = await self._compactor.compact(outputs)

        self._logger.info(f"Compaction complete, reduced {len(outputs)} outputs to consolidated result")

        return compacted

    def _extract_reasoning_outputs(self, context: StageContext) -> List[str]:
        """Extract reasoning outputs from previous stages.
        
        This gathers outputs from stages that produce reasoning content,
        such as working awareness or other reasoning stages.
        
        Args:
            context: Stage context with previous results
            
        Returns:
            List of reasoning outputs to compact
        """
        outputs = []

        reasoning_stages = {StageType.PREPROCESSING, StageType.WORKING_AWARENESS}

        for result in context.previous_results:
            if result.stage_type in reasoning_stages and result.output:
                outputs.append(result.output)

        return outputs
