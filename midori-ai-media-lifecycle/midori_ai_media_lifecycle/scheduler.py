"""Background scheduler for periodic media cleanup."""

import asyncio

from typing import Callable

from midori_ai_logger import MidoriAiLogger

from .lifecycle import LifecycleManager


_logger = MidoriAiLogger(__name__)


class CleanupScheduler:
    """Schedules periodic cleanup of aged-out media.

    Runs as an async background task that periodically cleans up
    media that has passed the ageout threshold.
    """

    def __init__(self, lifecycle_manager: LifecycleManager, interval_seconds: float = 300.0, on_cleanup: Callable[[list[str]], None] | None = None) -> None:
        """Initialize cleanup scheduler.

        Args:
            lifecycle_manager: LifecycleManager to perform cleanup
            interval_seconds: Seconds between cleanup runs (default 5 minutes)
            on_cleanup: Optional callback called with list of deleted IDs
        """
        self.lifecycle_manager = lifecycle_manager
        self.interval_seconds = interval_seconds
        self.on_cleanup = on_cleanup
        self._task: asyncio.Task[None] | None = None
        self._running = False

    @property
    def is_running(self) -> bool:
        """Check if scheduler is currently running."""
        return self._running

    async def _run_cleanup_loop(self) -> None:
        """Internal loop that runs periodic cleanup."""
        while self._running:
            try:
                deleted_ids = await self.lifecycle_manager.cleanup_aged_media()
                if deleted_ids:
                    await _logger.print(f"Cleaned up {len(deleted_ids)} aged media: {deleted_ids}", mode="debug")
                    if self.on_cleanup:
                        self.on_cleanup(deleted_ids)
            except Exception as e:
                await _logger.print(f"Error during media cleanup: {e}", mode="error")
            await asyncio.sleep(self.interval_seconds)

    def start(self) -> None:
        """Start the background cleanup task.

        Creates an asyncio task that runs the cleanup loop.
        Safe to call multiple times - does nothing if already running.
        """
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_cleanup_loop())
        _logger.rprint(f"Cleanup scheduler started (interval: {self.interval_seconds}s)", mode="debug")

    async def stop(self) -> None:
        """Stop the background cleanup task.

        Gracefully stops the cleanup loop and waits for task completion.
        Safe to call multiple times - does nothing if not running.
        """
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        await _logger.print("Cleanup scheduler stopped", mode="debug")

    async def run_once(self) -> list[str]:
        """Run cleanup once without scheduling.

        Useful for manual cleanup triggers.

        Returns:
            List of deleted media IDs
        """
        return await self.lifecycle_manager.cleanup_aged_media()
