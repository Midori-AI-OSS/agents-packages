"""Base cache protocol for the reasoning pipeline.

This demonstrates how to design flexible caching abstractions
that can be implemented with different backends.
"""

from abc import ABC
from abc import abstractmethod

from typing import Optional


class CacheProtocol(ABC):
    """Abstract base class for cache implementations.
    
    This protocol demonstrates how to design flexible caching systems
    that can be swapped between in-memory, persistent, or vector-based
    backends without changing the pipeline code.
    
    Implementations should handle:
    - Key-value storage and retrieval
    - TTL and expiration
    - Cache invalidation
    - Error handling
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Retrieve a value from the cache.
        
        Args:
            key: The cache key to look up
            
        Returns:
            The cached value if found and not expired, None otherwise
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> None:
        """Store a value in the cache.
        
        Args:
            key: The cache key to store under
            value: The value to cache
            ttl_seconds: Optional time-to-live in seconds (None = no expiration)
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a value from the cache.
        
        Args:
            key: The cache key to delete
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all values from the cache.
        
        Use with caution - this removes all cached data.
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.
        
        Args:
            key: The cache key to check
            
        Returns:
            True if the key exists and is not expired, False otherwise
        """
        pass
