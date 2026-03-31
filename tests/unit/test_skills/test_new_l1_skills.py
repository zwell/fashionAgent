"""Tests for Phase 2 L1 skills: design_proposal and image_generation."""

from __future__ import annotations

from fashion_agent.skills.l1_atomic.design_proposal import design_proposal
from fashion_agent.skills.l1_atomic.image_gen import image_generation


class TestDesignProposal:
    async def test_basic_proposal(self):
        result = await design_proposal(category="Dress", season="spring")
        assert result["success"] is True
        p = result["proposal"]
        assert p["product_category"] == "Dress"
        assert p["season"] == "spring"
        assert len(p["color_palette"]["options"]) > 0
        assert "description" in result

    async def test_with_reference(self):
        result = await design_proposal(
            category="Dress",
            season="summer",
            reference_article_id="0126589003",
        )
        assert result["success"] is True
        assert result["reference_article"] is not None
        assert result["reference_article"]["prod_name"] == "Cotton dress"

    async def test_style_keywords(self):
        result = await design_proposal(
            category="Blazer",
            season="autumn",
            style_keywords=["elegant", "优雅"],
        )
        assert result["success"] is True

    async def test_all_seasons(self):
        for season in ["spring", "summer", "autumn", "winter"]:
            result = await design_proposal(category="T-shirt", season=season)
            assert result["success"] is True
            assert result["proposal"]["season"] == season


class TestImageGeneration:
    async def test_generate_for_article(self):
        result = await image_generation(article_id="0126589003")
        assert result["success"] is True
        assert result["total_images"] == 3
        for img in result["images"]:
            assert "prompt" in img
            assert "placeholder_url" in img
            assert "quality_score" in img

    async def test_generate_with_description(self):
        result = await image_generation(
            description="Red floral summer dress, flowing fabric"
        )
        assert result["success"] is True
        assert result["total_images"] == 3

    async def test_custom_types(self):
        result = await image_generation(
            article_id="0130025001",
            image_types=["product_shot", "flat_lay"],
        )
        assert result["success"] is True
        assert result["total_images"] == 2
        types = {i["type"] for i in result["images"]}
        assert types == {"product_shot", "flat_lay"}

    async def test_missing_input(self):
        result = await image_generation()
        assert result["success"] is False

    async def test_nonexistent_article(self):
        result = await image_generation(article_id="NONEXIST")
        assert result["success"] is False
