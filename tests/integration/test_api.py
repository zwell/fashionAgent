"""Integration tests for the FastAPI endpoints."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from fashion_agent.gateway.app import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestHealthEndpoint:
    async def test_health(self, client: AsyncClient):
        r = await client.get("/health")
        assert r.status_code == 200
        d = r.json()
        assert d["status"] == "healthy"
        assert d["skills_registered"] >= 5


class TestDataEndpoints:
    async def test_articles(self, client: AsyncClient):
        r = await client.get("/api/v1/data/articles")
        assert r.status_code == 200
        assert r.json()["total"] == 20

    async def test_article_detail(self, client: AsyncClient):
        r = await client.get("/api/v1/data/articles/0108775015")
        assert r.status_code == 200
        d = r.json()
        assert d["article"]["prod_name"] == "Strap top"
        assert len(d["inventory"]) > 0

    async def test_inventory(self, client: AsyncClient):
        r = await client.get("/api/v1/data/inventory")
        assert r.status_code == 200
        assert r.json()["total"] > 0

    async def test_low_stock(self, client: AsyncClient):
        r = await client.get("/api/v1/data/inventory/low-stock")
        assert r.status_code == 200
        assert r.json()["total"] > 0

    async def test_transactions(self, client: AsyncClient):
        r = await client.get("/api/v1/data/transactions")
        assert r.status_code == 200
        assert r.json()["total"] == 30

    async def test_customers(self, client: AsyncClient):
        r = await client.get("/api/v1/data/customers")
        assert r.status_code == 200
        assert r.json()["total"] == 15

    async def test_suppliers(self, client: AsyncClient):
        r = await client.get("/api/v1/data/suppliers")
        assert r.status_code == 200
        assert r.json()["total"] == 6


class TestSkillEndpoints:
    async def test_list_all(self, client: AsyncClient):
        r = await client.get("/api/v1/skills")
        assert r.status_code == 200
        assert r.json()["total"] >= 8

    async def test_filter_l1(self, client: AsyncClient):
        r = await client.get("/api/v1/skills?level=L1")
        assert r.status_code == 200
        assert r.json()["total"] >= 5

    async def test_filter_l2(self, client: AsyncClient):
        r = await client.get("/api/v1/skills?level=L2")
        assert r.status_code == 200
        assert r.json()["total"] >= 3

    async def test_search(self, client: AsyncClient):
        r = await client.get("/api/v1/skills/search?q=库存")
        assert r.status_code == 200
        assert r.json()["total"] >= 1


class TestTaskEndpoints:
    async def test_copywriting(self, client: AsyncClient):
        r = await client.post(
            "/api/v1/tasks/copywriting?article_id=0126589003&style=promotion"
        )
        assert r.status_code == 200
        d = r.json()
        assert d["status"] == "completed"

    async def test_restock(self, client: AsyncClient):
        r = await client.post(
            "/api/v1/tasks/restock?article_id=0130025001&forecast_days=30"
        )
        assert r.status_code == 200
        assert r.json()["status"] == "completed"

    async def test_clearance(self, client: AsyncClient):
        r = await client.post(
            "/api/v1/tasks/clearance?article_id=0142702004"
        )
        assert r.status_code == 200
        assert r.json()["status"] == "completed"

    async def test_trend(self, client: AsyncClient):
        r = await client.post("/api/v1/tasks/trend?season=summer")
        assert r.status_code == 200
        assert r.json()["status"] == "completed"

    async def test_launch(self, client: AsyncClient):
        r = await client.post(
            "/api/v1/tasks/launch?article_id=0126589003&season=spring"
        )
        assert r.status_code == 200
        assert r.json()["status"] == "completed"

    async def test_generic_task(self, client: AsyncClient):
        r = await client.post("/api/v1/tasks", json={
            "task_type": "copywriting",
            "instruction": "Generate copy for dress",
            "params": {"article_id": "0126589003"},
        })
        assert r.status_code == 200
        assert r.json()["status"] == "completed"
