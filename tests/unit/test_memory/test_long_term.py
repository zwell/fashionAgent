"""Tests for long-term knowledge graph memory (in-memory fallback)."""

from __future__ import annotations

import pytest

from fashion_agent.memory.long_term import LongTermMemory


@pytest.fixture
async def graph():
    g = LongTermMemory()
    await g.connect()
    yield g
    await g.close()


class TestLongTermMemory:
    async def test_add_and_get_node(self, graph: LongTermMemory):
        await graph.add_node("SKU001", "SKU", {"name": "T-shirt"})
        node = await graph.get_node("SKU001")
        assert node is not None
        assert node["label"] == "SKU"
        assert node["name"] == "T-shirt"

    async def test_get_nonexistent_node(self, graph: LongTermMemory):
        assert await graph.get_node("NOPE") is None

    async def test_add_edge_and_neighbors(self, graph: LongTermMemory):
        await graph.add_node("SKU001", "SKU", {"name": "Dress"})
        await graph.add_node("CAT001", "Category", {"name": "Garment Full body"})
        await graph.add_node("SUP001", "Supplier", {"name": "Factory A"})
        await graph.add_edge("SKU001", "CAT001", "BELONGS_TO")
        await graph.add_edge("SKU001", "SUP001", "SUPPLIED_BY")

        neighbors = await graph.get_neighbors("SKU001")
        assert len(neighbors) == 2
        relations = {n["relation"] for n in neighbors}
        assert relations == {"BELONGS_TO", "SUPPLIED_BY"}

    async def test_filter_neighbors_by_relation(self, graph: LongTermMemory):
        await graph.add_node("SKU001", "SKU", {})
        await graph.add_node("CAT001", "Category", {})
        await graph.add_node("SUP001", "Supplier", {})
        await graph.add_edge("SKU001", "CAT001", "BELONGS_TO")
        await graph.add_edge("SKU001", "SUP001", "SUPPLIED_BY")

        cats = await graph.get_neighbors("SKU001", relation="BELONGS_TO")
        assert len(cats) == 1
        assert cats[0]["node"]["label"] == "Category"

    async def test_sku_graph(self, graph: LongTermMemory):
        await graph.add_node("SKU001", "SKU", {"name": "Coat"})
        await graph.add_node("CAT001", "Category", {"name": "Outerwear"})
        await graph.add_edge("SKU001", "CAT001", "BELONGS_TO")

        result = await graph.get_sku_graph("SKU001")
        assert result["sku"] is not None
        assert result["total_connections"] == 1

    async def test_query_by_label(self, graph: LongTermMemory):
        await graph.add_node("S1", "Supplier", {"name": "A"})
        await graph.add_node("S2", "Supplier", {"name": "B"})
        await graph.add_node("C1", "Category", {"name": "Tops"})

        suppliers = await graph.query_by_label("Supplier")
        assert len(suppliers) == 2

    async def test_stats(self, graph: LongTermMemory):
        await graph.add_node("N1", "SKU", {})
        await graph.add_node("N2", "Category", {})
        await graph.add_edge("N1", "N2", "BELONGS_TO")

        stats = await graph.stats()
        assert stats["total_nodes"] == 2
        assert stats["total_edges"] == 1
        assert stats["node_labels"]["SKU"] == 1
