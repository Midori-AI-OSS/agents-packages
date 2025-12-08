"""Data models for the reasoning pipeline.

This module defines the core data structures used throughout the demo pipeline,
showing how to build type-safe, well-documented APIs.
"""

from dataclasses import dataclass
from dataclasses import field

from datetime import datetime

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from .enums import StageStatus
from .enums import StageType


@dataclass
class PipelineRequest:
    """Input to the reasoning pipeline.
    
    This demonstrates how to structure requests for LRM pipelines,
    including context, constraints, and metadata.
    
    Attributes:
        prompt: The main reasoning task or question
        context: Optional background context or conversation history
        constraints: Optional list of constraints or requirements
        metadata: Optional metadata for tracking and observability
        max_tokens: Optional token limit for generation
        temperature: Optional temperature for generation (0.0-1.0)
    """

    prompt: str
    context: Optional[str] = None
    constraints: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


@dataclass
class StageResult:
    """Result from a single pipeline stage.
    
    This structure enables detailed observability and debugging,
    showing what each stage produced and how long it took.
    
    Attributes:
        stage_type: Which stage produced this result
        status: Execution status (completed, failed, skipped, etc.)
        output: The stage's output (text, data structure, etc.)
        thinking: Optional internal reasoning or explanation
        duration_ms: How long the stage took to execute
        error: Optional error message if stage failed
        metadata: Optional stage-specific metadata
    """

    stage_type: StageType
    status: StageStatus
    output: Optional[str] = None
    thinking: Optional[str] = None
    duration_ms: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResponse:
    """Output from the reasoning pipeline.
    
    This demonstrates a comprehensive response structure for LRM systems,
    including the final answer, intermediate stages, and observability data.
    
    Attributes:
        final_response: The synthesized final answer
        stages: Results from each stage that executed
        total_duration_ms: Total pipeline execution time
        request: The original request that was processed
        cache_hits: Number of cache hits during execution
        timestamp: When the pipeline completed
        metadata: Optional pipeline-level metadata
    """

    final_response: str
    stages: List[StageResult]
    total_duration_ms: float
    request: PipelineRequest
    cache_hits: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StageContext:
    """Context passed between pipeline stages.
    
    This demonstrates how to maintain state and share information
    across different stages in a modular pipeline architecture.
    
    Attributes:
        request: The original pipeline request
        previous_results: Results from stages that have already executed
        shared_data: Dictionary for sharing data between stages
        cache_enabled: Whether caching is enabled for this execution
    """

    request: PipelineRequest
    previous_results: List[StageResult] = field(default_factory=list)
    shared_data: Dict[str, Any] = field(default_factory=dict)
    cache_enabled: bool = True
