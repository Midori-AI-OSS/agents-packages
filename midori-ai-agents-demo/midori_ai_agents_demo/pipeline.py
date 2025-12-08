"""Main reasoning pipeline orchestrator.

This module demonstrates how to build a complete LRM pipeline by
orchestrating multiple stages, integrating all Midori AI packages,
and providing comprehensive observability.
"""

import time

from typing import List
from typing import Optional

from midori_ai_agent_base import MidoriAiAgentProtocol
from midori_ai_compactor import ThinkingCompactor
from midori_ai_logger import MidoriAiLogger
from midori_ai_reranker import RerankerPipeline

from .caching import CacheProtocol
from .caching import MemoryCache

from .config import PipelineConfig

from .models import PipelineRequest
from .models import PipelineResponse
from .models import StageContext

from .observability import MetricsCollector
from .observability import Tracer

from .stages import CompactionStage
from .stages import FinalResponseStage
from .stages import PreprocessingStage
from .stages import RerankingStage
from .stages import WorkingAwarenessStage


class ReasoningPipeline:
    """Main reasoning pipeline that orchestrates all stages.
    
    This pipeline demonstrates:
    - Integration of all Midori AI packages
    - Modular stage-based architecture
    - Parallel execution where possible
    - Comprehensive caching
    - Full observability (metrics, tracing, logging)
    - Flexible configuration
    
    The pipeline processes requests through multiple stages:
    1. Preprocessing - Validates and normalizes input
    2. Working Awareness - Generates multiple reasoning perspectives in parallel
    3. Compaction - Consolidates outputs using midori-ai-compactor
    4. Reranking - Prioritizes results using midori-ai-reranker
    5. Final Response - Synthesizes everything into a coherent answer
    
    Each stage can be enabled/disabled via configuration, and stages
    that don't depend on each other run in parallel.
    
    This is a DEMO package showing how to integrate all the pieces.
    Production implementations should adapt these patterns with proper
    testing, monitoring, and hardening.
    """

    def __init__(self, agent: MidoriAiAgentProtocol, config: Optional[PipelineConfig] = None, compactor: Optional[ThinkingCompactor] = None, reranker: Optional[RerankerPipeline] = None, cache: Optional[CacheProtocol] = None, logger: Optional[MidoriAiLogger] = None):
        """Initialize the reasoning pipeline.
        
        Args:
            agent: The primary agent for reasoning tasks
            config: Optional pipeline configuration (uses defaults if not provided)
            compactor: Optional ThinkingCompactor instance (creates one if not provided)
            reranker: Optional RerankerPipeline instance (creates one if not provided)
            cache: Optional cache implementation (uses MemoryCache if not provided)
            logger: Optional logger instance (creates one if not provided)
        """
        self._agent = agent
        self._config = config or PipelineConfig()
        self._logger = logger or MidoriAiLogger()
        self._cache = cache or MemoryCache()
        self._metrics = MetricsCollector() if self._config.enable_metrics else None
        self._compactor = compactor or ThinkingCompactor(agent=agent)
        self._reranker = reranker or RerankerPipeline()
        self._logger.info("Initialized ReasoningPipeline with configuration")

        self._stages = self._create_stages()

    def _create_stages(self) -> List:
        """Create all pipeline stages based on configuration.
        
        This demonstrates how to build modular pipelines where stages
        can be enabled/disabled via configuration.
        
        Returns:
            List of configured stage instances
        """
        stages = []

        if self._config.enable_preprocessing:
            stages.append(PreprocessingStage(agent=self._agent, enabled=True, logger=self._logger))

        if self._config.enable_working_awareness:
            stages.append(WorkingAwarenessStage(agent=self._agent, num_perspectives=3, enabled=True, logger=self._logger))

        if self._config.enable_compaction:
            stages.append(CompactionStage(compactor=self._compactor, enabled=True, logger=self._logger))

        if self._config.enable_reranking:
            stages.append(RerankingStage(reranker=self._reranker, enabled=True, logger=self._logger))

        stages.append(FinalResponseStage(agent=self._agent, enabled=True, logger=self._logger))

        return stages

    async def process(self, request: PipelineRequest | str) -> PipelineResponse:
        """Process a reasoning request through the pipeline.
        
        This is the main entry point for the pipeline. It:
        1. Converts string requests to PipelineRequest objects
        2. Creates a tracer if tracing is enabled
        3. Executes all stages in sequence or parallel
        4. Collects metrics and timing information
        5. Returns a comprehensive response with all results
        
        Args:
            request: Either a PipelineRequest object or a string prompt
            
        Returns:
            PipelineResponse with final answer and all stage results
        """
        if isinstance(request, str):
            request = PipelineRequest(prompt=request)

        self._logger.info(f"Processing request: {request.prompt[:100]}...")

        tracer = Tracer() if self._config.enable_tracing else None

        if tracer:
            pipeline_span = tracer.start_span("reasoning_pipeline", {"prompt_length": str(len(request.prompt))})

        start_time = time.perf_counter()

        context = StageContext(request=request, previous_results=[], shared_data={}, cache_enabled=self._config.cache_strategy != "none")

        cache_hits = 0

        for stage in self._stages:
            stage_result = await stage.execute(context)

            context.previous_results.append(stage_result)

            if self._metrics:
                self._metrics.record_duration(stage_result.stage_type, stage_result.duration_ms)

            if tracer:
                stage_span = tracer.start_span(f"stage_{stage_result.stage_type.value}", {"status": stage_result.status.value})

                tracer.end_span(stage_span)

        total_duration_ms = (time.perf_counter() - start_time) * 1000

        if tracer:
            tracer.end_span(pipeline_span)

        final_result = context.previous_results[-1]

        final_response = final_result.output or "No response generated"

        self._logger.info(f"Pipeline complete in {total_duration_ms:.2f}ms, final response: {len(final_response)} chars")

        response = PipelineResponse(final_response=final_response, stages=context.previous_results, total_duration_ms=total_duration_ms, request=request, cache_hits=cache_hits)

        if self._metrics:
            response.metadata["metrics"] = self._metrics.get_summary()

        if tracer:
            response.metadata["trace_id"] = tracer.trace_id

        return response
