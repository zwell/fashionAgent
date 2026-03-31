"""Unified memory manager — facade over short/mid/long-term memory layers."""

from __future__ import annotations

from typing import Any

from fashion_agent.core.config import get_settings
from fashion_agent.core.logging import get_logger
from fashion_agent.memory.short_term import ShortTermMemory

logger = get_logger(__name__)


class MemoryManager:
    """Single entry point for all memory operations.

    Phase 1: only short-term (Redis / in-memory).
    Phase 3 will add Milvus (mid-term) and Neo4j (long-term).
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.short_term = ShortTermMemory(redis_url=settings.redis_url)

    async def initialize(self) -> None:
        await self.short_term.connect()
        logger.info("memory_manager_initialized")

    async def shutdown(self) -> None:
        await self.short_term.close()

    # ── Short-term convenience methods ────────────────────────

    async def remember(self, key: str, value: Any, ttl: int | None = None) -> None:
        await self.short_term.set(key, value, ttl=ttl)

    async def recall(self, key: str) -> Any | None:
        return await self.short_term.get(key)

    async def forget(self, key: str) -> None:
        await self.short_term.delete(key)

    # ── Session helpers ───────────────────────────────────────

    async def get_task_context(self, task_id: str) -> dict:
        return (await self.short_term.get(f"task:{task_id}")) or {}

    async def save_task_context(self, task_id: str, context: dict) -> None:
        await self.short_term.set(f"task:{task_id}", context, ttl=3600)

    async def log_agent_action(self, task_id: str, agent: str, action: str, result: Any) -> None:
        await self.short_term.append_to_session(
            f"task:{task_id}:log",
            "actions",
            {"agent": agent, "action": action, "result": result},
        )
