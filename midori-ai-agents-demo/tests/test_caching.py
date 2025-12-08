"""Tests for caching functionality."""

import pytest

from midori_ai_agents_demo.caching import MemoryCache


@pytest.mark.asyncio
async def test_memory_cache_get_set():
    """Test basic get and set operations."""
    cache = MemoryCache()

    await cache.set("key1", "value1")

    result = await cache.get("key1")

    assert result == "value1"


@pytest.mark.asyncio
async def test_memory_cache_get_nonexistent():
    """Test getting a nonexistent key."""
    cache = MemoryCache()

    result = await cache.get("nonexistent")

    assert result is None


@pytest.mark.asyncio
async def test_memory_cache_ttl():
    """Test TTL expiration."""
    import asyncio

    cache = MemoryCache()

    await cache.set("key1", "value1", ttl_seconds=1)

    result1 = await cache.get("key1")

    assert result1 == "value1"

    await asyncio.sleep(1.1)

    result2 = await cache.get("key1")

    assert result2 is None


@pytest.mark.asyncio
async def test_memory_cache_delete():
    """Test deleting a key."""
    cache = MemoryCache()

    await cache.set("key1", "value1")

    await cache.delete("key1")

    result = await cache.get("key1")

    assert result is None


@pytest.mark.asyncio
async def test_memory_cache_exists():
    """Test checking key existence."""
    cache = MemoryCache()

    await cache.set("key1", "value1")

    exists = await cache.exists("key1")

    assert exists is True

    exists_not = await cache.exists("nonexistent")

    assert exists_not is False


@pytest.mark.asyncio
async def test_memory_cache_clear():
    """Test clearing the cache."""
    cache = MemoryCache()

    await cache.set("key1", "value1")
    await cache.set("key2", "value2")

    await cache.clear()

    result1 = await cache.get("key1")
    result2 = await cache.get("key2")

    assert result1 is None
    assert result2 is None
