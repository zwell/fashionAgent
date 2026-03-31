"""Integration tests for the memory API endpoints."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from fashion_agent.gateway.app import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestMemoryStatsEndpoint:
    async def test_stats(self, client: AsyncClient):
        r = await client.get("/api/v1/memory/stats")
        assert r.status_code == 200
        d = r.json()
        assert "short_term" in d
        assert "mid_term" in d
        assert "long_term" in d
        assert isinstance(d["mid_term"]["vectors_stored"], int)


class TestSKUProfileEndpoint:
    async def test_get_profile(self, client: AsyncClient):
        r = await client.get("/api/v1/memory/sku/0126589003/profile")
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert d["profile"]["basic_info"]["name"] == "Cotton dress"

    async def test_profile_nonexistent(self, client: AsyncClient):
        r = await client.get("/api/v1/memory/sku/NONEXIST/profile")
        assert r.status_code == 200
        assert r.json()["success"] is False


class TestSimilarSKUEndpoint:
    async def test_find_similar(self, client: AsyncClient):
        r = await client.get("/api/v1/memory/sku/0108775015/similar?top_k=3")
        assert r.status_code == 200
        d = r.json()
        assert d["article_id"] == "0108775015"
        assert len(d["similar"]) >= 1


class TestSemanticSearchEndpoint:
    async def test_semantic_search(self, client: AsyncClient):
        r = await client.get("/api/v1/memory/search?q=black+dress&top_k=3")
        assert r.status_code == 200
        d = r.json()
        assert d["query"] == "black dress"
        assert len(d["results"]) >= 1


class TestSKUGraphEndpoint:
    async def test_sku_graph(self, client: AsyncClient):
        r = await client.get("/api/v1/memory/sku/0126589003/graph")
        assert r.status_code == 200
        d = r.json()
        assert d["sku"] is not None
        assert d["total_connections"] >= 2


class TestFeedbackEndpoint:
    async def test_add_feedback(self, client: AsyncClient):
        r = await client.post(
            "/api/v1/memory/sku/0130025001/feedback"
            "?feedback_type=return_reason&content=size_issue"
        )
        assert r.status_code == 200
        assert r.json()["success"] is True


class TestReflectionEndpoint:
    async def test_run_reflection(self, client: AsyncClient):
        r = await client.post("/api/v1/memory/reflection")
        assert r.status_code == 200
        d = r.json()
        assert "total_decisions" in d

    async def test_recent_insights(self, client: AsyncClient):
        r = await client.get("/api/v1/memory/reflection/recent?days=3")
        assert r.status_code == 200
        assert "insights" in r.json()


class TestGraphStatsEndpoint:
    async def test_graph_stats(self, client: AsyncClient):
        r = await client.get("/api/v1/memory/graph/stats")
        assert r.status_code == 200
        d = r.json()
        assert "total_nodes" in d
        assert "total_edges" in d
