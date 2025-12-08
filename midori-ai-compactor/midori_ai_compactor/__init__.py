"""Midori AI Compactor - Flexible consolidation of multi-model reasoning outputs."""

from .compactor import ThinkingCompactor

from .config import CompactorConfig
from .config import load_compactor_config

from .prompts import DEFAULT_CONSOLIDATION_PROMPT
from .prompts import build_consolidation_prompt
from .prompts import format_outputs_for_prompt


__all__ = ["build_consolidation_prompt", "CompactorConfig", "DEFAULT_CONSOLIDATION_PROMPT", "format_outputs_for_prompt", "load_compactor_config", "ThinkingCompactor"]
