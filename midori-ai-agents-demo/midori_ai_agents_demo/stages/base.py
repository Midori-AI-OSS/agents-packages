"""Base classes for pipeline stages.

This module demonstrates how to build extensible, modular pipeline architectures
where each stage is independent and can be customized or replaced.
"""

import time

from abc import ABC
from abc import abstractmethod

from typing import Optional

from midori_ai_logger import MidoriAiLogger

from ..enums import StageStatus
from ..enums import StageType
from ..models import StageContext
from ..models import StageResult


class BaseStage(ABC):
    """Abstract base class for pipeline stages.
    
    This demonstrates the Template Method pattern for building modular
    processing pipelines. Each stage:
    - Has a defined type and purpose
    - Can be enabled/disabled via configuration
    - Reports timing and status for observability
    - Handles errors gracefully
    
    Subclasses should implement:
    - `_execute()`: The core processing logic
    - `stage_type` property: Which stage this is
    
    The base class handles:
    - Timing and metrics
    - Error handling and status reporting
    - Logging and observability
    - Skip logic when stage is disabled
    """

    def __init__(self, enabled: bool = True, logger: Optional[MidoriAiLogger] = None):
        """Initialize the base stage.
        
        Args:
            enabled: Whether this stage should execute
            logger: Optional logger instance (creates one if not provided)
        """
        self._enabled = enabled
        self._logger = logger or MidoriAiLogger()

    @property
    @abstractmethod
    def stage_type(self) -> StageType:
        """The type of this stage.
        
        Must be implemented by subclasses to identify which stage this is.
        """
        pass

    @abstractmethod
    async def _execute(self, context: StageContext) -> str:
        """Execute the stage's core logic.
        
        This is where subclasses implement their specific processing.
        The method should return the stage's output as a string.
        
        Args:
            context: The stage context with request and previous results
            
        Returns:
            The stage's output text
            
        Raises:
            Exception: Any errors during execution (caught by execute())
        """
        pass

    async def execute(self, context: StageContext) -> StageResult:
        """Execute the stage with timing, error handling, and status tracking.
        
        This is the public interface for running a stage. It handles:
        - Skip logic when stage is disabled
        - Timing measurement
        - Error handling and reporting
        - Status tracking
        - Logging
        
        Args:
            context: The stage context with request and previous results
            
        Returns:
            StageResult with output, status, timing, and any errors
        """
        if not self._enabled:
            self._logger.info(f"Stage {self.stage_type.value} is disabled, skipping")

            return StageResult(stage_type=self.stage_type, status=StageStatus.SKIPPED)

        self._logger.info(f"Starting stage: {self.stage_type.value}")

        start_time = time.perf_counter()

        try:
            output = await self._execute(context)

            duration_ms = (time.perf_counter() - start_time) * 1000

            self._logger.info(f"Stage {self.stage_type.value} completed in {duration_ms:.2f}ms")

            return StageResult(stage_type=self.stage_type, status=StageStatus.COMPLETED, output=output, duration_ms=duration_ms)
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000

            error_msg = f"Stage {self.stage_type.value} failed: {str(e)}"

            self._logger.error(error_msg)

            return StageResult(stage_type=self.stage_type, status=StageStatus.FAILED, error=error_msg, duration_ms=duration_ms)
