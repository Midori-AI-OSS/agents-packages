"""State reporter for sending heartbeats to the logging server."""
import httpx
import asyncio

from typing import Any
from typing import Dict
from typing import Callable
from typing import Optional

from .enums import ServiceStatus
from .models import ServiceState

from .config import MAX_BACKOFF_SECONDS
from .config import load_reporter_config
from .config import DEFAULT_HEARTBEAT_INTERVAL
from .config import DEFAULT_LOGGING_SERVER_URL

_GLOBAL_REPORTER_CONFIG = load_reporter_config()

class StateReporter:
    """Async state reporter that sends periodic heartbeats to the logging server."""

    def __init__(
        self,
        service_name: str,
        logging_server_url: Optional[str] = None,
        heartbeat_interval: Optional[int] = None,
        health_check: Optional[Callable[[], bool]] = None,
        metadata_provider: Optional[Callable[[], Dict[str, Any]]] = None,
        logger: Optional[Any] = None,
    ) -> None:
        """Initialize the state reporter.

        Args:
            service_name: Identifier for this service (e.g., "memory-server")
            logging_server_url: URL of the logging server. Defaults to config value or http://logging:8000
            heartbeat_interval: Seconds between heartbeat reports (default 30)
            health_check: Optional callable that returns True if service is healthy
            metadata_provider: Optional callable that returns additional metadata dict
            logger: Optional logger instance for debug output
        """
        self.service_name = service_name
        self._configure(logging_server_url, heartbeat_interval)
        self.health_check = health_check
        self.metadata_provider = metadata_provider
        self.logger = logger
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._consecutive_failures = 0

    def _configure(self, logging_server_url: Optional[str], heartbeat_interval: Optional[int]) -> None:
        config_logging_url = _GLOBAL_REPORTER_CONFIG.get("logging_server_url")
        resolved_logging_url = DEFAULT_LOGGING_SERVER_URL
        if config_logging_url is not None:
            resolved_logging_url = config_logging_url
        if logging_server_url is not None:
            resolved_logging_url = logging_server_url

        config_heartbeat = _GLOBAL_REPORTER_CONFIG.get("heartbeat_interval")
        resolved_heartbeat = DEFAULT_HEARTBEAT_INTERVAL
        if config_heartbeat is not None:
            resolved_heartbeat = config_heartbeat
        if heartbeat_interval is not None:
            resolved_heartbeat = heartbeat_interval

        self.logging_server_url = resolved_logging_url
        self.heartbeat_interval = int(resolved_heartbeat)
        self._max_backoff_seconds = int(_GLOBAL_REPORTER_CONFIG.get("max_backoff_seconds", MAX_BACKOFF_SECONDS))

    def _get_backoff_delay(self) -> float:
        """Calculate exponential backoff delay based on consecutive failures."""
        if self._consecutive_failures == 0:
            return 0
        delay = min(2 ** self._consecutive_failures, self._max_backoff_seconds)
        return float(delay)

    def _determine_status(self) -> ServiceStatus:
        """Determine current service status using health check if available."""
        if self.health_check is None:
            return ServiceStatus.HEALTHY
        try:
            is_healthy = self.health_check()
            return ServiceStatus.HEALTHY if is_healthy else ServiceStatus.UNHEALTHY
        except Exception:
            return ServiceStatus.DEGRADED

    def _build_state(self, status: ServiceStatus) -> ServiceState:
        """Build a ServiceState object with current metadata."""
        metadata = None
        if self.metadata_provider:
            try:
                metadata = self.metadata_provider()
            except Exception:
                pass
        return ServiceState(service=self.service_name, status=status, metadata=metadata)

    async def _log(self, message: str) -> None:
        """Log a message if a logger is available."""
        if self.logger is None:
            return

        try:
            if hasattr(self.logger, "print") and asyncio.iscoroutinefunction(self.logger.print):
                await self.logger.print(f"[StateReporter] {message}", mode="debug")
            elif hasattr(self.logger, "rprint"):
                self.logger.rprint(f"[StateReporter] {message}")
        except Exception:
            return

    async def _send_state(self, state: ServiceState) -> bool:
        """Send state to logging server. Returns True on success."""
        url = f"{self.logging_server_url}/state/register"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=state.to_json())
                if response.status_code == 200:
                    self._consecutive_failures = 0
                    if state.status != ServiceStatus.HEALTHY:
                        await self._log(f"State reported: {state.status.value}")
                    return True
                self._consecutive_failures += 1
                await self._log(f"State report failed with status {response.status_code}")
                return False
        except Exception as exc:
            self._consecutive_failures += 1
            await self._log(f"State report failed: {exc}")
            return False

    async def _heartbeat_loop(self) -> None:
        """Main heartbeat loop that runs while reporter is active."""
        while self._running:
            status = self._determine_status()
            state = self._build_state(status)
            await self._send_state(state)

            backoff = self._get_backoff_delay()
            wait_time = self.heartbeat_interval + backoff
            await asyncio.sleep(wait_time)

    async def report_status(self, status: ServiceStatus, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Send a one-time status report. Returns True on success."""
        state = ServiceState(service=self.service_name, status=status, metadata=metadata)
        return await self._send_state(state)

    async def start(self) -> None:
        """Start the heartbeat loop. Reports STARTING status first."""
        if self._running:
            return

        await self._log(f"Starting state reporter for {self.service_name}")
        await self.report_status(ServiceStatus.STARTING)

        self._running = True
        self._task = asyncio.create_task(self._heartbeat_loop())

    async def stop(self) -> None:
        """Stop the heartbeat loop. Reports STOPPING then OFFLINE status."""
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

        await self._log(f"Stopping state reporter for {self.service_name}")
        await self.report_status(ServiceStatus.STOPPING)
        await self.report_status(ServiceStatus.OFFLINE)
