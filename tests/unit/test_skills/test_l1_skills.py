"""Tests for L1 atomic skills."""

from __future__ import annotations

import pytest

from fashion_agent.skills.l1_atomic.competitor import competitor_analysis
from fashion_agent.skills.l1_atomic.copywriting import generate_copywriting
from fashion_agent.skills.l1_atomic.erp_inventory import erp_inventory_query
from fashion_agent.skills.l1_atomic.sales_forecast import sales_forecast
from fashion_agent.skills.l1_atomic.trend_analysis import trend_analysis


class TestERPInventory:
    async def test_valid_article(self):
        result = await erp_inventory_query(article_id="0108775015")
        assert result["success"] is True
        assert result["article_id"] == "0108775015"
        assert result["total_quantity"] > 0
        assert "warehouses" in result

    async def test_unknown_article(self):
        result = await erp_inventory_query(article_id="NONEXIST")
        assert result["success"] is False

    async def test_low_stock_detection(self):
        result = await erp_inventory_query(article_id="0126589003")
        assert result["success"] is True
        assert result["any_low_stock"] is True


class TestSalesForecast:
    async def test_forecast_with_history(self):
        result = await sales_forecast(article_id="0108775015", days=30)
        assert result["success"] is True
        assert "predicted_sales_next_days" in result
        assert result["confidence"] > 0

    async def test_forecast_no_history(self):
        result = await sales_forecast(article_id="0190112001", days=30)
        assert result["success"] is True


class TestCompetitor:
    async def test_competitor_analysis(self):
        result = await competitor_analysis(article_id="0120129001")
        assert result["success"] is True
        assert len(result["competitors"]) == 3
        assert "avg_competitor_price" in result


class TestTrendAnalysis:
    async def test_valid_season(self):
        result = await trend_analysis(season="spring")
        assert result["success"] is True
        assert len(result["trending_colors"]) > 0
        assert "summary" in result

    async def test_invalid_season(self):
        result = await trend_analysis(season="monsoon")
        assert result["success"] is False

    async def test_all_seasons(self):
        for season in ["spring", "summer", "autumn", "winter"]:
            result = await trend_analysis(season=season)
            assert result["success"] is True


class TestCopywriting:
    async def test_product_description(self):
        result = await generate_copywriting(article_id="0126589003", style="product_description")
        assert result["success"] is True
        assert "Cotton dress" in result["copy_text"] or "cotton" in result["copy_text"].lower()

    async def test_promotion(self):
        result = await generate_copywriting(
            article_id="0130025001", style="promotion", price=199.0, discount_pct=0.3
        )
        assert result["success"] is True
        assert "特惠" in result["copy_text"]

    async def test_social_media(self):
        result = await generate_copywriting(article_id="0132172001", style="social_media")
        assert result["success"] is True
        assert "#" in result["copy_text"]
