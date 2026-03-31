"""Short-term memory backed by Redis (with in-memory fallback)."""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from fashion_agent.core.logging import get_logger

logger = get_logger(__name__)


class ShortTermMemory:
    """Session-scoped short-term memory.

    Uses Redis when available, falls back to an in-memory dict for local dev.
    """

    def __init__(self, redis_url: str | None = None, default_ttl: int = 86400):
        self._redis = None
        self._fallback: dict[str, Any] = {}
        self._default_ttl = default_ttl
        self._redis_url = redis_url

    async def connect(self) -> None:
        if not self._redis_url:
            logger.info("short_term_memory_fallback", msg="No Redis URL, using in-memory store")
            return
        try:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info("short_term_memory_connected", url=self._redis_url)
        except Exception as e:
            logger.warning(
                "redis_connection_failed", error=str(e), msg="in-memory fallback"
            )
            self._redis = None

    async def get(self, key: str) -> Any | None:
        if self._redis:
            raw = await self._redis.get(key)
            return json.loads(raw) if raw else None
        return self._fallback.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl = ttl or self._default_ttl
        if self._redis:
            await self._redis.set(key, json.dumps(value, default=str), ex=timedelta(seconds=ttl))
        else:
            self._fallback[key] = value

    async def delete(self, key: str) -> None:
        if self._redis:
            await self._redis.delete(key)
        else:
            self._fallback.pop(key, None)

    async def exists(self, key: str) -> bool:
        if self._redis:
            return bool(await self._redis.exists(key))
        return key in self._fallback

    async def get_session(self, session_id: str) -> dict:
        return (await self.get(f"session:{session_id}")) or {}

    async def set_session(self, session_id: str, data: dict) -> None:
        await self.set(f"session:{session_id}", data)

    async def append_to_session(self, session_id: str, key: str, value: Any) -> None:
        session = await self.get_session(session_id)
        if key not in session:
            session[key] = []
        session[key].append(value)
        await self.set_session(session_id, session)

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()
