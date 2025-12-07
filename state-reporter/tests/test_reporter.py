"""Tests for the Midori AI state-reporter package."""

import json
import pytest
import asyncio

from unittest.mock import patch
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

from state_reporter import ServiceState
from state_reporter import ServiceStatus
from state_reporter import StateReporter

class TestServiceStatus:
    """Tests for ServiceStatus enum."""

    def test_general_statuses_exist(self) -> None:
        assert ServiceStatus.HEALTHY.value == "Healthy"
        assert ServiceStatus.UNHEALTHY.value == "Unhealthy"
        assert ServiceStatus.DEGRADED.value == "Degraded"
        assert ServiceStatus.OFFLINE.value == "Offline"
        assert ServiceStatus.UNKNOWN.value == "Unknown"

    def test_specific_statuses_exist(self) -> None:
        assert ServiceStatus.STARTING.value == "Starting"
        assert ServiceStatus.STOPPING.value == "Stopping"
        assert ServiceStatus.RESTARTING.value == "Restarting"
        assert ServiceStatus.UPDATING.value == "Updating"
        assert ServiceStatus.PROVISIONING.value == "Provisioning"
        assert ServiceStatus.MAINTENANCE.value == "Maintenance"
        assert ServiceStatus.RECOVERING.value == "Recovering"
        assert ServiceStatus.PAUSED.value == "Paused"
        assert ServiceStatus.FROZEN.value == "Frozen"

    def test_status_is_string_enum(self) -> None:
        assert isinstance(ServiceStatus.HEALTHY, str)
        assert ServiceStatus.HEALTHY == "Healthy"


class TestServiceState:
    """Tests for ServiceState model."""

    def test_basic_state(self) -> None:
        state = ServiceState(service="test-service", status=ServiceStatus.HEALTHY)
        assert state.service == "test-service"
        assert state.status == ServiceStatus.HEALTHY
        assert state.metadata is None

    def test_state_with_metadata(self) -> None:
        metadata = {"version": "1.0.0", "uptime": 3600}
        state = ServiceState(service="test-service", status=ServiceStatus.HEALTHY, metadata=metadata)
        assert state.metadata == metadata

    def test_to_json(self) -> None:
        metadata = {"version": "1.0.0"}
        state = ServiceState(service="test-service", status=ServiceStatus.HEALTHY, metadata=metadata)
        result = state.to_json()
        assert result == {"service": "test-service", "status": "Healthy", "metadata": {"version": "1.0.0"}}

    def test_to_json_serializable(self) -> None:
        state = ServiceState(service="test-service", status=ServiceStatus.HEALTHY)
        result = state.to_json()
        json_str = json.dumps(result)
        assert "test-service" in json_str
        assert "Healthy" in json_str


class TestStateReporter:
    """Tests for StateReporter class."""

    def test_init_default_values(self) -> None:
        reporter = StateReporter("test-service")
        assert reporter.service_name == "test-service"
        assert reporter.heartbeat_interval == 30
        assert reporter.health_check is None
        assert reporter.metadata_provider is None

    def test_init_custom_values(self) -> None:
        health_fn = lambda: True
        metadata_fn = lambda: {"key": "value"}
        reporter = StateReporter("test-service", logging_server_url="http://custom:9000", heartbeat_interval=60, health_check=health_fn, metadata_provider=metadata_fn)
        assert reporter.logging_server_url == "http://custom:9000"
        assert reporter.heartbeat_interval == 60
        assert reporter.health_check == health_fn
        assert reporter.metadata_provider == metadata_fn

    def test_init_uses_env_var(self) -> None:
        with patch.dict("os.environ", {"LOGGING_SERVER_URL": "http://envvar:8080"}):
            reporter = StateReporter("test-service")
            assert reporter.logging_server_url == "http://envvar:8080"

    def test_determine_status_no_health_check(self) -> None:
        reporter = StateReporter("test-service")
        assert reporter._determine_status() == ServiceStatus.HEALTHY

    def test_determine_status_healthy(self) -> None:
        reporter = StateReporter("test-service", health_check=lambda: True)
        assert reporter._determine_status() == ServiceStatus.HEALTHY

    def test_determine_status_unhealthy(self) -> None:
        reporter = StateReporter("test-service", health_check=lambda: False)
        assert reporter._determine_status() == ServiceStatus.UNHEALTHY

    def test_determine_status_exception(self) -> None:
        def failing_check() -> bool:
            raise RuntimeError("Check failed")

        reporter = StateReporter("test-service", health_check=failing_check)
        assert reporter._determine_status() == ServiceStatus.DEGRADED

    def test_build_state_basic(self) -> None:
        reporter = StateReporter("test-service")
        state = reporter._build_state(ServiceStatus.HEALTHY)
        assert state.service == "test-service"
        assert state.status == ServiceStatus.HEALTHY
        assert state.metadata is None

    def test_build_state_with_metadata(self) -> None:
        reporter = StateReporter("test-service", metadata_provider=lambda: {"version": "1.0"})
        state = reporter._build_state(ServiceStatus.HEALTHY)
        assert state.metadata == {"version": "1.0"}

    def test_build_state_metadata_error(self) -> None:
        def failing_metadata() -> dict:
            raise RuntimeError("Metadata failed")

        reporter = StateReporter("test-service", metadata_provider=failing_metadata)
        state = reporter._build_state(ServiceStatus.HEALTHY)
        assert state.metadata is None

    def test_backoff_delay_no_failures(self) -> None:
        reporter = StateReporter("test-service")
        reporter._consecutive_failures = 0
        assert reporter._get_backoff_delay() == 0

    def test_backoff_delay_one_failure(self) -> None:
        reporter = StateReporter("test-service")
        reporter._consecutive_failures = 1
        assert reporter._get_backoff_delay() == 2

    def test_backoff_delay_capped(self) -> None:
        reporter = StateReporter("test-service")
        reporter._consecutive_failures = 100
        assert reporter._get_backoff_delay() == 300


@pytest.mark.asyncio
class TestStateReporterAsync:
    """Async tests for StateReporter."""

    async def test_send_state_success(self) -> None:
        reporter = StateReporter("test-service", logging_server_url="http://test:8000")
        state = ServiceState(service="test-service", status=ServiceStatus.HEALTHY)

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await reporter._send_state(state)
            assert result is True
            assert reporter._consecutive_failures == 0

    async def test_send_state_failure(self) -> None:
        reporter = StateReporter("test-service", logging_server_url="http://test:8000")
        state = ServiceState(service="test-service", status=ServiceStatus.HEALTHY)

        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await reporter._send_state(state)
            assert result is False
            assert reporter._consecutive_failures == 1

    async def test_send_state_exception(self) -> None:
        reporter = StateReporter("test-service", logging_server_url="http://test:8000")
        state = ServiceState(service="test-service", status=ServiceStatus.HEALTHY)

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(side_effect=Exception("Connection error"))

            result = await reporter._send_state(state)
            assert result is False
            assert reporter._consecutive_failures == 1

    async def test_report_status(self) -> None:
        reporter = StateReporter("test-service", logging_server_url="http://test:8000")

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await reporter.report_status(ServiceStatus.STARTING)
            assert result is True

    async def test_start_and_stop(self) -> None:
        reporter = StateReporter("test-service", logging_server_url="http://test:8000", heartbeat_interval=1)

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            await reporter.start()
            assert reporter._running is True
            assert reporter._task is not None

            await asyncio.sleep(0.1)

            await reporter.stop()
            assert reporter._running is False
