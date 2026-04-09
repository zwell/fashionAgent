"""Unified memory manager — facade over short/mid/long-term memory layers."""

from __future__ import annotations

from typing import Any

from fashion_agent.core.config import get_settings
from fashion_agent.core.logging import get_logger
from fashion_agent.memory.graphiti_store import GraphitiStore
from fashion_agent.memory.long_term import LongTermMemory
from fashion_agent.memory.mid_term import MidTermMemory
from fashion_agent.memory.short_term import ShortTermMemory

logger = get_logger(__name__)


class MemoryManager:
    """Single entry point for all memory operations across three layers.

    - **short_term** (Redis / in-memory): session context, task state  [TTL: 24h]
    - **mid_term** (Milvus / in-memory): SKU vector embeddings         [TTL: 90d]
    - **long_term** (Neo4j / in-memory): entity knowledge graph         [permanent]

    When ``MEMORY_BACKEND=zep`` is enabled, mid+long are served by a shared
    Graphiti adapter while preserving the same public method contracts.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.backend = settings.memory_backend
        self.short_term = ShortTermMemory(redis_url=settings.redis_url)
        if self.backend == "zep":
            graphiti = GraphitiStore(
                api_key=settings.zep_api_key,
                public_graph_id=settings.zep_public_graph_id,
                default_user_id=settings.zep_default_user_id,
                timeout_seconds=settings.zep_timeout_seconds,
            )
            # Keep call sites stable during migration: mid_term/long_term share adapter.
            self.mid_term = graphiti
            self.long_term = graphiti
        else:
            self.mid_term = MidTermMemory(
                milvus_host=settings.milvus_host,
                milvus_port=settings.milvus_port,
                milvus_uri=(settings.milvus_uri or None),
                connect_timeout=settings.milvus_connect_timeout,
                extend_no_proxy=settings.milvus_extend_no_proxy,
            )
            self.long_term = LongTermMemory(
                neo4j_uri=settings.neo4j_uri,
                neo4j_user=settings.neo4j_user,
                neo4j_password=settings.neo4j_password,
            )

    async def initialize(self) -> None:
        await self.short_term.connect()
        await self.mid_term.connect()
        if self.long_term is not self.mid_term:
            await self.long_term.connect()
        logger.info("memory_manager_initialized")

    async def shutdown(self) -> None:
        await self.short_term.close()
        await self.mid_term.close()
        if self.long_term is not self.mid_term:
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
        mid_backend = "graphiti" if self.backend == "zep" else (
            "milvus" if getattr(self.mid_term, "_milvus", None) else "in-memory"
        )
        long_backend = "graphiti" if self.backend == "zep" else (
            "neo4j" if getattr(self.long_term, "_driver", None) else "in-memory"
        )
        return {
            "short_term": "connected",
            "mid_term": {
                "backend": mid_backend,
                "vectors_stored": vector_count,
            },
            "long_term": {
                "backend": long_backend,
                **graph_stats,
            },
        }
