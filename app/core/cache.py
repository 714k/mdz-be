"""
Redis cache client for session storage and rate limiting.
"""

import redis.asyncio as aioredis
from typing import Any
import json
from app.config import settings


class RedisCache:
    """Async Redis cache wrapper."""

    def __init__(self):
        self.redis: aioredis.Redis | None = None

    async def connect(self):
        """Initialize Redis connection pool."""
        self.redis = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )

    async def disconnect(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Any:
        """Get value from cache."""
        if not self.redis:
            return None
        value = await self.redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def set(self, key: str, value: Any, expire: int = 3600):
        """Set value in cache with expiration (seconds)."""
        if not self.redis:
            return False

        if not isinstance(value, str):
            value = json.dumps(value)

        return await self.redis.set(key, value, ex=expire)

    async def delete(self, key: str):
        """Delete key from cache."""
        if not self.redis:
            return 0
        return await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self.redis:
            return False
        return await self.redis.exists(key) > 0


# Global cache instance
cache = RedisCache()
