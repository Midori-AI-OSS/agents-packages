"""Reranking stage for the reasoning pipeline.

This stage demonstrates:
- Integration with midori-ai-reranker package
- Prioritizing and ranking results
- Quality assessment
- Result filtering
"""

from typing import List
from typing import Optional

from midori_ai_logger import MidoriAiLogger
from midori_ai_reranker import RerankerPipeline

from ..enums import StageType
from ..models import StageContext

from .base import BaseStage


class RerankingStage(BaseStage):
    """Reranking stage that prioritizes reasoning results by quality.
    
    This stage demonstrates how to:
    - Use the RerankerPipeline from midori-ai-reranker
    - Extract and parse multiple result candidates
    - Rank results by quality or relevance
    - Filter or prioritize outputs
    
    In a real pipeline, this stage might:
    - Rank solution candidates by correctness
    - Prioritize results by confidence
    - Filter out low-quality outputs
    - Select the best reasoning path
    """

    def __init__(self, reranker: RerankerPipeline, enabled: bool = True, logger: Optional[MidoriAiLogger] = None):
        """Initialize the reranking stage.
        
        Args:
            reranker: RerankerPipeline instance to use
            enabled: Whether this stage should execute
            logger: Optional logger instance
        """
        super().__init__(enabled=enabled, logger=logger)
        self._reranker = reranker

    @property
    def stage_type(self) -> StageType:
        """Return the stage type."""
        return StageType.RERANKING

    async def _execute(self, context: StageContext) -> str:
        """Rerank reasoning results by quality or relevance.
        
        This demonstrates:
        1. Extracting candidate results from previous stages
        2. Using RerankerPipeline to score and rank them
        3. Selecting or combining the best results
        4. Returning the prioritized output
        
        Args:
            context: Stage context with previous stage results
            
        Returns:
            The highest-quality or most relevant reasoning output
        """
        self._logger.info("Starting reranking of reasoning results")

        candidates = self._extract_candidates(context)

        self._logger.debug(f"Extracted {len(candidates)} candidates for reranking")

        if not candidates:
            self._logger.warning("No candidates to rerank, returning empty result")

            return "No candidates available for reranking"

        if len(candidates) == 1:
            self._logger.info("Only one candidate, no reranking needed")

            return candidates[0]

        self._logger.info(f"Reranking {len(candidates)} candidates using RerankerPipeline")

        query = context.request.prompt

        ranked_results = await self._reranker.rerank(query=query, documents=candidates)

        self._logger.info(f"Reranking complete, selected top result from {len(ranked_results)} candidates")

        top_result = ranked_results[0].document if ranked_results else candidates[0]

        return top_result

    def _extract_candidates(self, context: StageContext) -> List[str]:
        """Extract candidate results from previous stages.
        
        This gathers outputs that should be ranked, such as:
        - Compacted outputs
        - Individual reasoning perspectives
        - Alternative solutions
        
        Args:
            context: Stage context with previous results
            
        Returns:
            List of candidate result strings
        """
        candidates = []

        candidate_stages = {StageType.COMPACTION, StageType.WORKING_AWARENESS}

        for result in context.previous_results:
            if result.stage_type in candidate_stages and result.output:
                if result.stage_type == StageType.WORKING_AWARENESS:
                    parsed = self._parse_perspectives(result.output)

                    candidates.extend(parsed)
                else:
                    candidates.append(result.output)

        if not candidates:
            for result in context.previous_results:
                if result.output:
                    candidates.append(result.output)

        return candidates

    def _parse_perspectives(self, combined_output: str) -> List[str]:
        """Parse combined perspectives into individual candidates.
        
        The working awareness stage may combine multiple perspectives
        into a single output. This method splits them back out for
        individual ranking.
        
        Args:
            combined_output: Combined output with multiple perspectives
            
        Returns:
            List of individual perspective strings
        """
        if "Perspective 1:" not in combined_output:
            return [combined_output]

        perspectives = []

        parts = combined_output.split("Perspective ")

        for part in parts[1:]:
            if ":" in part:
                _, content = part.split(":", 1)

                perspectives.append(content.strip())

        return perspectives if perspectives else [combined_output]
