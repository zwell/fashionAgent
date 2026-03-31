"""Tests for Entity Memory (unified SKU profiles)."""

from __future__ import annotations

import pytest

from fashion_agent.memory.entity import EntityMemory
from fashion_agent.memory.manager import MemoryManager


@pytest.fixture
async def entity():
    mm = MemoryManager()
    await mm.initialize()
    em = EntityMemory(mm)
    yield em
    await mm.shutdown()


class TestEntityMemory:
    async def test_build_profile(self, entity: EntityMemory):
        result = await entity.build_sku_profile("0126589003")
        assert result["success"] is True
        p = result["profile"]
        assert p["article_id"] == "0126589003"
        assert p["basic_info"]["name"] == "Cotton dress"
        assert p["inventory"]["total_stock"] > 0
        assert p["sales"]["total_transactions"] > 0

    async def test_build_profile_nonexistent(self, entity: EntityMemory):
        result = await entity.build_sku_profile("NONEXIST")
        assert result["success"] is False

    async def test_get_profile_cached(self, entity: EntityMemory):
        await entity.build_sku_profile("0108775015")
        cached = await entity.get_profile("0108775015")
        assert cached is not None
        assert cached["basic_info"]["name"] == "Strap top"

    async def test_find_similar_skus(self, entity: EntityMemory):
        for aid in ["0108775015", "0108775044", "0126589003", "0130025001"]:
            await entity.build_sku_profile(aid)

        similar = await entity.find_similar_skus("0108775015", top_k=3)
        assert len(similar) >= 1
        assert all(s["article_id"] != "0108775015" for s in similar)

    async def test_sku_relationships(self, entity: EntityMemory):
        await entity.build_sku_profile("0126589003")
        graph = await entity.get_sku_relationships("0126589003")
        assert graph["sku"] is not None
        assert graph["total_connections"] > 0

    async def test_add_feedback(self, entity: EntityMemory):
        await entity.build_sku_profile("0130025001")
        await entity.add_feedback("0130025001", "return_reason", "色差严重")

        graph = await entity.get_sku_relationships("0130025001")
        feedback_rels = [
            r for r in graph["relationships"] if r["relation"] == "HAS_FEEDBACK"
        ]
        assert len(feedback_rels) == 1
