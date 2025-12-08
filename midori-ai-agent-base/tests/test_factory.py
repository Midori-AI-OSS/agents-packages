"""Tests for the factory function."""

import pytest

from midori_ai_agent_base import get_agent


class TestGetAgentFactory:
    """Tests for get_agent factory function."""

    def test_unknown_backend_raises_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown agent backend"):
            import asyncio
            asyncio.run(get_agent(backend="unknown", model="test", api_key="key"))


@pytest.mark.asyncio
class TestGetAgentFactoryAsync:
    """Async tests for get_agent factory function."""

    async def test_unknown_backend_async(self) -> None:
        with pytest.raises(ValueError, match="Unknown agent backend"):
            await get_agent(backend="invalid", model="test", api_key="key")
