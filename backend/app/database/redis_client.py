"""
Redis Connection for Caching and Sessions
"""

import redis.asyncio as redis
from app.config import settings

# Redis client instance
_redis_client: redis.Redis = None


async def init_redis():
    """Initialize Redis connection."""
    global _redis_client
    _redis_client = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    # Test connection
    await _redis_client.ping()


async def close_redis():
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()


def get_redis() -> redis.Redis:
    """Get Redis client instance."""
    return _redis_client


# Utility functions for common operations
async def cache_set(key: str, value: str, expire_seconds: int = 3600):
    """Set a cached value with expiration."""
    await _redis_client.setex(key, expire_seconds, value)


async def cache_get(key: str) -> str | None:
    """Get a cached value."""
    return await _redis_client.get(key)


async def cache_delete(key: str):
    """Delete a cached value."""
    await _redis_client.delete(key)


async def blacklist_token(token: str, expire_seconds: int = 86400):
    """Add a token to the blacklist (for logout)."""
    await _redis_client.setex(f"blacklist:{token}", expire_seconds, "1")


async def is_token_blacklisted(token: str) -> bool:
    """Check if a token is blacklisted."""
    result = await _redis_client.get(f"blacklist:{token}")
    return result is not None
