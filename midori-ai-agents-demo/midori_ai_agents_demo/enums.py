"""Enumerations for the reasoning pipeline."""

from enum import Enum


class StageType(str, Enum):
    """Types of pipeline stages.
    
    Each stage represents a distinct phase in the reasoning process,
    demonstrating different aspects of package integration.
    """

    PREPROCESSING = "preprocessing"
    WORKING_AWARENESS = "working_awareness"
    COMPACTION = "compaction"
    RERANKING = "reranking"
    FINAL_RESPONSE = "final_response"


class StageStatus(str, Enum):
    """Status of a pipeline stage execution.
    
    Used for observability and debugging in the demo pipeline.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CacheStrategy(str, Enum):
    """Caching strategies for different pipeline stages.
    
    Demonstrates when to use different caching approaches:
    - NONE: No caching (always recompute)
    - MEMORY: Fast in-memory cache (lost on restart)
    - PERSISTENT: Disk-based cache (survives restarts)
    - VECTOR: Vector-based semantic cache (context-bridge pattern)
    """

    NONE = "none"
    MEMORY = "memory"
    PERSISTENT = "persistent"
    VECTOR = "vector"
