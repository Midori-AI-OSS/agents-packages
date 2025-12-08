"""In-memory cache implementation for the reasoning pipeline.

This demonstrates a simple, fast cache using Python dictionaries.
For production use, consider Redis, Memcached, or context-bridge.
"""

import time

from dataclasses import dataclass

from typing import Dict
from typing import Optional

from .base import CacheProtocol


@dataclass
class CacheEntry:
    """A cached entry with value and expiration.
    
    Attributes:
        value: The cached value
        expires_at: Unix timestamp when this entry expires (None = never)
    """

    value: str
    expires_at: Optional[float]


class MemoryCache(CacheProtocol):
    """Simple in-memory cache using a dictionary.
    
    This demonstrates basic caching patterns:
    - Key-value storage
    - TTL-based expiration
    - Automatic cleanup on access
    
    Note: This is a demo implementation. For production use:
    - Use Redis or Memcached for distributed caching
    - Use midori-ai-context-bridge for semantic/vector caching
    - Implement proper memory limits and eviction policies
    - Add monitoring and metrics
    
    This cache:
    - Is fast (in-process)
    - Is simple (no external dependencies)
    - Loses all data on restart
    - Doesn't handle memory limits
    """

    def __init__(self):
        """Initialize the memory cache."""
        self._cache: Dict[str, CacheEntry] = {}

    async def get(self, key: str) -> Optional[str]:
        """Retrieve a value from the cache.
        
        Args:
            key: The cache key to look up
            
        Returns:
            The cached value if found and not expired, None otherwise
        """
        entry = self._cache.get(key)

        if entry is None:
            return None

        if entry.expires_at is not None and time.time() > entry.expires_at:
            await self.delete(key)

            return None

        return entry.value

    async def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> None:
        """Store a value in the cache.
        
        Args:
            key: The cache key to store under
            value: The value to cache
            ttl_seconds: Optional time-to-live in seconds (None = no expiration)
        """
        expires_at = None

        if ttl_seconds is not None:
            expires_at = time.time() + ttl_seconds

        self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    async def delete(self, key: str) -> None:
        """Delete a value from the cache.
        
        Args:
            key: The cache key to delete
        """
        self._cache.pop(key, None)

    async def clear(self) -> None:
        """Clear all values from the cache."""
        self._cache.clear()

    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.
        
        Args:
            key: The cache key to check
            
        Returns:
            True if the key exists and is not expired, False otherwise
        """
        value = await self.get(key)

        return value is not None
