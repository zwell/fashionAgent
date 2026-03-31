"""Tests for L2 composite skills."""

from __future__ import annotations

from fashion_agent.skills.l2_composite.clearance import clearance_workflow
from fashion_agent.skills.l2_composite.product_launch import product_launch_workflow
from fashion_agent.skills.l2_composite.restock import restock_workflow


class TestRestockWorkflow:
    async def test_restock_with_data(self):
        result = await restock_workflow(article_id="0108775015", forecast_days=30)
        assert result["success"] is True
        assert "recommendation" in result
        rec = result["recommendation"]
        assert "should_reorder" in rec
        assert "urgency" in rec

    async def test_restock_low_stock_item(self):
        result = await restock_workflow(article_id="0126589003")
        assert result["success"] is True
        assert result["recommendation"]["urgency"] == "high"

    async def test_restock_nonexistent(self):
        result = await restock_workflow(article_id="NONEXIST")
        assert result["success"] is False


class TestClearanceWorkflow:
    async def test_clearance_decision(self):
        result = await clearance_workflow(article_id="0108775015")
        assert result["success"] is True
        assert "strategy" in result
        assert result["strategy"] in ["deep_discount", "moderate_discount", "price_match", "hold"]

    async def test_clearance_nonexistent(self):
        result = await clearance_workflow(article_id="NONEXIST")
        assert result["success"] is False


class TestProductLaunchWorkflow:
    async def test_launch_product(self):
        result = await product_launch_workflow(article_id="0126589003", season="spring")
        assert result["success"] is True
        assert "product_description" in result
        assert "social_media_copy" in result
        assert "launch_checklist" in result
        assert "trend_analysis" in result
