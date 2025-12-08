"""Configuration for the context bridge package.

This module defines decay configuration and model types for
time-based memory corruption.
"""

from dataclasses import dataclass

from enum import Enum

from typing import Optional


class ModelType(Enum):
    """Type of model for different decay rates.

    PREPROCESSING: Fast-decaying tactical memory (30 min decay, 90 min removal)
    WORKING_AWARENESS: Slow-decaying strategic memory (12 hour decay, 36 hour removal)
    """

    PREPROCESSING = "preprocessing"
    WORKING_AWARENESS = "working_awareness"


@dataclass
class DecayConfig:
    """Configuration for time-based memory decay.

    Attributes:
        decay_minutes: Minutes before corruption begins
        removal_multiplier: Multiplier for decay_minutes to get removal threshold
        corruption_intensity: Maximum corruption intensity (0.0 to 1.0)
    """

    decay_minutes: int
    removal_multiplier: float = 3.0
    corruption_intensity: float = 0.3

    @property
    def removal_minutes(self) -> float:
        """Return the removal threshold in minutes."""
        return self.decay_minutes * self.removal_multiplier


DEFAULT_DECAY_CONFIGS = {
    ModelType.PREPROCESSING: DecayConfig(decay_minutes=30, removal_multiplier=3.0, corruption_intensity=0.3),
    ModelType.WORKING_AWARENESS: DecayConfig(decay_minutes=720, removal_multiplier=3.0, corruption_intensity=0.3),
}


@dataclass
class BridgeConfig:
    """Configuration for the ContextBridge.

    Attributes:
        max_tokens_per_summary: Maximum tokens for summarized context
        chroma_collection_name: Name for the ChromaDB collection
        preprocessing_decay: Decay config for preprocessing model type
        working_awareness_decay: Decay config for working awareness model type
    """

    max_tokens_per_summary: int = 500
    chroma_collection_name: str = "context_bridge"
    preprocessing_decay: Optional[DecayConfig] = None
    working_awareness_decay: Optional[DecayConfig] = None

    def __post_init__(self) -> None:
        """Initialize default decay configs if not provided."""
        if self.preprocessing_decay is None:
            self.preprocessing_decay = DEFAULT_DECAY_CONFIGS[ModelType.PREPROCESSING]
        if self.working_awareness_decay is None:
            self.working_awareness_decay = DEFAULT_DECAY_CONFIGS[ModelType.WORKING_AWARENESS]

    def get_decay_config(self, model_type: ModelType) -> DecayConfig:
        """Get the decay config for a given model type.

        Args:
            model_type: The model type to get config for

        Returns:
            DecayConfig for the specified model type
        """
        if model_type == ModelType.PREPROCESSING:
            return self.preprocessing_decay or DEFAULT_DECAY_CONFIGS[ModelType.PREPROCESSING]
        return self.working_awareness_decay or DEFAULT_DECAY_CONFIGS[ModelType.WORKING_AWARENESS]
