"""Configuration for the reasoning pipeline.

This module demonstrates how to build flexible, well-documented configuration
systems for LRM pipelines. Each option includes extensive documentation
explaining when and why to use it.
"""

import tomllib as _toml

from dataclasses import dataclass
from dataclasses import field

from pathlib import Path

from typing import Dict
from typing import Optional

from .enums import CacheStrategy


@dataclass
class PipelineConfig:
    """Configuration for the reasoning pipeline.
    
    This configuration demonstrates how to make pipelines flexible and
    adaptable to different use cases without changing code.
    
    Stage Toggles (enable/disable specific processing steps):
        enable_preprocessing: Enable preprocessing stage (input validation, formatting)
            - Use when: Input needs normalization or validation
            - Demo: Shows agent-base protocol usage
        
        enable_working_awareness: Enable working awareness stage (parallel reasoning)
            - Use when: Complex problems benefit from multiple perspectives
            - Demo: Shows parallel execution with asyncio.gather
        
        enable_compaction: Enable compaction stage (deduplicate/consolidate outputs)
            - Use when: Multiple reasoning outputs need consolidation
            - Demo: Shows midori-ai-compactor integration
        
        enable_reranking: Enable reranking stage (prioritize results)
            - Use when: Multiple candidate results need quality ranking
            - Demo: Shows midori-ai-reranker integration
    
    Execution Behavior:
        parallel_execution: Run independent stages in parallel when possible
            - Use when: Stages don't depend on each other's outputs
            - Trade-off: Faster but uses more resources
        
        max_retries: Number of times to retry failed stages
            - Use when: Transient failures are possible (API timeouts, etc.)
            - Demo: Shows resilient error handling
        
        timeout_seconds: Maximum time to wait for a stage
            - Use when: You need to bound execution time
            - Demo: Shows timeout handling patterns
    
    Caching Configuration:
        cache_strategy: Which caching approach to use
            - NONE: Always recompute (best for testing)
            - MEMORY: Fast in-memory cache (lost on restart)
            - PERSISTENT: Disk-based cache (survives restarts)
            - VECTOR: Semantic cache using context-bridge
        
        cache_ttl_seconds: How long cached results remain valid
            - Use when: Results can become stale over time
            - Demo: Shows cache expiration patterns
    
    Integration Configuration:
        vector_collection: Name of vector collection for context storage
            - Demo: Shows midori-ai-vector-manager usage
        
        compactor_prompt: Custom prompt for output consolidation
            - Demo: Shows midori-ai-compactor customization
        
        reranker_model: Model to use for reranking results
            - Demo: Shows midori-ai-reranker backend selection
    
    Observability:
        enable_metrics: Collect and expose metrics
            - Use when: You need performance monitoring
            - Demo: Shows metrics collection patterns
        
        enable_tracing: Enable distributed tracing
            - Use when: You need detailed execution visibility
            - Demo: Shows tracing integration hooks
        
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR)
            - Use when: You need to control log verbosity
            - Demo: Shows midori_ai_logger usage
    """

    enable_preprocessing: bool = True
    enable_working_awareness: bool = True
    enable_compaction: bool = True
    enable_reranking: bool = True
    parallel_execution: bool = True
    max_retries: int = 3
    timeout_seconds: float = 60.0
    cache_strategy: CacheStrategy = CacheStrategy.MEMORY
    cache_ttl_seconds: int = 3600
    vector_collection: str = "reasoning_context"
    compactor_prompt: Optional[str] = None
    reranker_model: str = "cross-encoder"
    enable_metrics: bool = True
    enable_tracing: bool = False
    log_level: str = "INFO"
    custom_stage_config: Dict[str, dict] = field(default_factory=dict)


def _find_config_file(name: str = "config.toml") -> Optional[Path]:
    """Search upward from this file for a TOML config file and return its Path.
    
    This pattern allows configuration to live at the project root while
    still being discoverable from package code.
    
    Returns:
        Path to config file if found, None otherwise
    """
    here = Path(__file__).resolve()

    for parent in (here, *here.parents):
        candidate = parent / name

        if candidate.exists():
            return candidate

    return None


def load_pipeline_config() -> PipelineConfig:
    """Load pipeline configuration from TOML file.
    
    Loads settings from `[midori_ai_agents_demo]` section.
    Falls back to defaults if config file not found or section missing.
    
    Example config.toml:
        [midori_ai_agents_demo]
        enable_preprocessing = true
        enable_working_awareness = true
        parallel_execution = true
        cache_strategy = "vector"
        log_level = "DEBUG"
    
    Returns:
        PipelineConfig with loaded values or defaults
    """
    path = _find_config_file()

    if path is None:
        return PipelineConfig()

    try:
        with path.open("rb") as f:
            data = _toml.load(f)
    except Exception:
        return PipelineConfig()

    section = data.get("midori_ai_agents_demo")

    if section is None or not isinstance(section, dict):
        return PipelineConfig()

    cache_strategy_str = section.get("cache_strategy", "memory")

    cache_strategy = CacheStrategy.MEMORY

    try:
        cache_strategy = CacheStrategy(cache_strategy_str)
    except ValueError:
        pass

    return PipelineConfig(
        enable_preprocessing=section.get("enable_preprocessing", True),
        enable_working_awareness=section.get("enable_working_awareness", True),
        enable_compaction=section.get("enable_compaction", True),
        enable_reranking=section.get("enable_reranking", True),
        parallel_execution=section.get("parallel_execution", True),
        max_retries=section.get("max_retries", 3),
        timeout_seconds=section.get("timeout_seconds", 60.0),
        cache_strategy=cache_strategy,
        cache_ttl_seconds=section.get("cache_ttl_seconds", 3600),
        vector_collection=section.get("vector_collection", "reasoning_context"),
        compactor_prompt=section.get("compactor_prompt"),
        reranker_model=section.get("reranker_model", "cross-encoder"),
        enable_metrics=section.get("enable_metrics", True),
        enable_tracing=section.get("enable_tracing", False),
        log_level=section.get("log_level", "INFO"),
        custom_stage_config=section.get("custom_stage_config", {}),
    )
