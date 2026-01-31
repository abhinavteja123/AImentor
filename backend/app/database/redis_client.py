"""
Redis Connection for Caching and Sessions
"""

import logging
import redis.asyncio as redis
from ..config import settings

logger = logging.getLogger(__name__)

# Redis client instance
_redis_client: redis.Redis = None
_connection_failed: bool = False


async def init_redis():
    """Initialize Redis connection with error handling for serverless."""
    global _redis_client, _connection_failed
    
    try:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        # Test connection
        await _redis_client.ping()
        logger.info("Redis connected successfully")
        _connection_failed = False
        
    except Exception as e:
        logger.warning(f"Redis connection failed (non-critical): {str(e)[:200]}")
        logger.info("Application will continue without Redis (caching disabled)")
        _connection_failed = True
        # Don't raise - allow app to start without Redis


async def close_redis():
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()


def get_redis() -> redis.Redis:
    """Get Redis client instance."""
    if _connection_failed or _redis_client is None:
        return None
    return _redis_client


def is_redis_available() -> bool:
    """Check if Redis is available."""
    return not _connection_failed and _redis_client is not None


# Utility functions for common operations
async def cache_set(key: str, value: str, expire_seconds: int = 3600):
    """Set a cached value with expiration."""
    if not is_redis_available():
        return
    try:
        await _redis_client.setex(key, expire_seconds, value)
    except Exception as e:
        logger.warning(f"Redis cache_set failed: {e}")


async def cache_get(key: str) -> str | None:
    """Get a cached value."""
    if not is_redis_available():
        return None
    try:
        return await _redis_client.get(key)
    except Exception as e:
        logger.warning(f"Redis cache_get failed: {e}")
        return None


async def cache_delete(key: str):
    """Delete a cached value."""
    if not is_redis_available():
        return
    try:
        await _redis_client.delete(key)
    except Exception as e:
        logger.warning(f"Redis cache_delete failed: {e}")


async def blacklist_token(token: str, expire_seconds: int = 86400):
    """Add a token to the blacklist (for logout)."""
    if not is_redis_available():
        logger.warning("Redis not available, token blacklist disabled")
        return
    try:
        await _redis_client.setex(f"blacklist:{token}", expire_seconds, "1")
    except Exception as e:
        logger.warning(f"Redis blacklist_token failed: {e}")


async def is_token_blacklisted(token: str) -> bool:
    """Check if a token is blacklisted."""
    if not is_redis_available():
        return False  # If Redis unavailable, assume not blacklisted
    try:
        result = await _redis_client.get(f"blacklist:{token}")
        return result is not None
    except Exception as e:
        logger.warning(f"Redis is_token_blacklisted failed: {e}")
        return False
