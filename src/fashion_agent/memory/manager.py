"""Unified memory manager — facade over short/mid/long-term memory layers."""

from __future__ import annotations

from typing import Any

from fashion_agent.core.config import get_settings
from fashion_agent.core.logging import get_logger
from fashion_agent.memory.long_term import LongTermMemory
from fashion_agent.memory.mid_term import MidTermMemory
from fashion_agent.memory.short_term import ShortTermMemory

logger = get_logger(__name__)


class MemoryManager:
    """Single entry point for all memory operations across three layers.

    - **short_term** (Redis / in-memory): session context, task state  [TTL: 24h]
    - **mid_term** (Milvus / in-memory): SKU vector embeddings         [TTL: 90d]
    - **long_term** (Neo4j / in-memory): entity knowledge graph         [permanent]
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.short_term = ShortTermMemory(redis_url=settings.redis_url)
        self.mid_term = MidTermMemory(
            milvus_host=settings.milvus_host,
            milvus_port=settings.milvus_port,
        )
        self.long_term = LongTermMemory(
            neo4j_uri=settings.neo4j_uri,
            neo4j_user=settings.neo4j_user,
            neo4j_password=settings.neo4j_password,
        )

    async def initialize(self) -> None:
        await self.short_term.connect()
        await self.mid_term.connect()
        await self.long_term.connect()
        logger.info("memory_manager_initialized")

    async def shutdown(self) -> None:
        await self.short_term.close()
        await self.mid_term.close()
        await self.long_term.close()

    # ── Short-term convenience ────────────────────────────────

    async def remember(self, key: str, value: Any, ttl: int | None = None) -> None:
        await self.short_term.set(key, value, ttl=ttl)

    async def recall(self, key: str) -> Any | None:
        return await self.short_term.get(key)

    async def forget(self, key: str) -> None:
        await self.short_term.delete(key)

    # ── Session / task helpers ────────────────────────────────

    async def get_task_context(self, task_id: str) -> dict:
        return (await self.short_term.get(f"task:{task_id}")) or {}

    async def save_task_context(self, task_id: str, context: dict) -> None:
        await self.short_term.set(f"task:{task_id}", context, ttl=3600)

    async def log_agent_action(
        self, task_id: str, agent: str, action: str, result: Any
    ) -> None:
        await self.short_term.append_to_session(
            f"task:{task_id}:log",
            "actions",
            {"agent": agent, "action": action, "result": result},
        )

    # ── Mid-term convenience ─────────────────────────────────

    async def store_sku_embedding(
        self, article_id: str, text: str, metadata: dict | None = None
    ) -> None:
        await self.mid_term.upsert_sku(article_id, text, metadata)

    async def find_similar(self, query: str, top_k: int = 5) -> list[dict]:
        return await self.mid_term.search_similar(query, top_k)

    # ── Cross-layer helpers ──────────────────────────────────

    async def get_memory_stats(self) -> dict:
        graph_stats = await self.long_term.stats()
        vector_count = await self.mid_term.count()
        return {
            "short_term": "connected",
            "mid_term": {
                "backend": "milvus" if self.mid_term._milvus else "in-memory",
                "vectors_stored": vector_count,
            },
            "long_term": {
                "backend": "neo4j" if self.long_term._driver else "in-memory",
                **graph_stats,
            },
        }
