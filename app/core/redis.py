"""
Redis client configuration for caching and session management.
"""

from typing import Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings


class RedisClient:
    """Redis client wrapper for async operations."""

    _client: Optional[Redis] = None

    @classmethod
    async def get_client(cls) -> Redis:
        """Get or create Redis client."""
        if cls._client is None:
            cls._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return cls._client

    @classmethod
    async def close(cls) -> None:
        """Close Redis connection."""
        if cls._client:
            await cls._client.close()
            cls._client = None


async def get_redis() -> Redis:
    """Dependency to get Redis client."""
    return await RedisClient.get_client()


# Cache key prefixes
class CacheKeys:
    """Cache key constants."""

    USER_SESSION = "session:"
    USER_PROFILE = "user:"
    AD_DETAIL = "ad:"
    AD_LIST = "ads:"
    CATEGORY = "category:"
    BRAND = "brand:"
    MODEL = "model:"
    GENERATION = "gen:"
    MODIFICATION = "mod:"
    LOCATION = "location:"
    ONLINE_USERS = "online:"
    RATE_LIMIT = "rate:"


async def cache_get(key: str) -> Optional[str]:
    """Get value from cache."""
    client = await RedisClient.get_client()
    return await client.get(key)


async def cache_set(
    key: str,
    value: str,
    ttl: Optional[int] = None,
) -> None:
    """Set value in cache with optional TTL."""
    client = await RedisClient.get_client()
    if ttl:
        await client.setex(key, ttl, value)
    else:
        await client.set(key, value)


async def cache_delete(key: str) -> None:
    """Delete value from cache."""
    client = await RedisClient.get_client()
    await client.delete(key)


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching pattern."""
    client = await RedisClient.get_client()
    async for key in client.scan_iter(match=pattern):
        await client.delete(key)

