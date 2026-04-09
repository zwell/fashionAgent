"""Tests for mid-term vector memory (in-memory fallback)."""

from __future__ import annotations

import pytest

from fashion_agent.memory.mid_term import MidTermMemory


@pytest.fixture
async def mem():
    m = MidTermMemory(
        milvus_host="localhost",
        milvus_port=19530,
        connect_timeout=5.0,
    )
    await m.connect()
    yield m
    await m.close()


class TestMidTermMemory:
    async def test_upsert_and_search(self, mem: MidTermMemory):
        await mem.upsert_sku("A001", "Black cotton T-shirt casual wear")
        await mem.upsert_sku("A002", "Red silk evening dress formal")
        await mem.upsert_sku("A003", "Blue denim jeans casual")

        results = await mem.search_similar("cotton T-shirt", top_k=2)
        assert len(results) >= 1
        assert results[0]["article_id"] == "A001"

    async def test_search_empty(self, mem: MidTermMemory):
        results = await mem.search_similar("anything", top_k=5)
        assert results == []

    async def test_count(self, mem: MidTermMemory):
        assert await mem.count() == 0
        await mem.upsert_sku("A001", "test item")
        assert await mem.count() == 1

    async def test_get_vector(self, mem: MidTermMemory):
        await mem.upsert_sku("A001", "test text")
        vec = await mem.get_sku_vector("A001")
        assert vec is not None
        assert vec["text"] == "test text"

    async def test_get_nonexistent(self, mem: MidTermMemory):
        vec = await mem.get_sku_vector("NOPE")
        assert vec is None

    async def test_similarity_ranking(self, mem: MidTermMemory):
        await mem.upsert_sku("A001", "Black cotton T-shirt short sleeve casual")
        await mem.upsert_sku("A002", "White cotton T-shirt round neck basic")
        await mem.upsert_sku("A003", "Red silk evening gown formal luxury")
        await mem.upsert_sku("A004", "Blue denim jacket outerwear rugged")

        results = await mem.search_similar("cotton T-shirt basic", top_k=4)
        ids = [r["article_id"] for r in results]
        assert ids[0] in ("A001", "A002")
