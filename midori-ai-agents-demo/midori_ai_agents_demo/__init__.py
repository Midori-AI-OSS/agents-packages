"""Midori AI Agents Demo - Demo showcase of complete LRM pipeline integration.

This package demonstrates how to build a complete Large Reasoning Model (LRM)
pipeline by integrating all Midori AI packages in a modular, observable,
and configurable architecture.

🚨 This is a DEMO/SHOWCASE Package 🚨

Purpose:
- Educational reference for the Midori AI package ecosystem
- Integration blueprint for building LRM pipelines
- Best practices for async patterns, caching, and observability
- NOT intended as production-ready code

Key Components:
- Pipeline: Main orchestrator integrating all stages
- Stages: Modular processing steps (preprocessing, working awareness, etc.)
- Config: Flexible configuration system
- Caching: Pluggable cache implementations
- Observability: Metrics and distributed tracing

Example:
    from midori_ai_agents_demo import ReasoningPipeline, PipelineConfig
    from midori_ai_agent_base import get_agent
    
    agent = await get_agent(backend="langchain", model="gpt-4")
    config = PipelineConfig(enable_all=True, parallel_execution=True)
    pipeline = ReasoningPipeline(agent=agent, config=config)
    
    result = await pipeline.process("Explain quantum computing")
    print(result.final_response)
"""

from .config import PipelineConfig
from .config import load_pipeline_config

from .enums import CacheStrategy
from .enums import StageStatus
from .enums import StageType

from .models import PipelineRequest
from .models import PipelineResponse
from .models import StageContext
from .models import StageResult

from .pipeline import ReasoningPipeline


__all__ = ["CacheStrategy", "load_pipeline_config", "PipelineConfig", "PipelineRequest", "PipelineResponse", "ReasoningPipeline", "StageContext", "StageResult", "StageStatus", "StageType"]

__version__ = "0.1.0"
