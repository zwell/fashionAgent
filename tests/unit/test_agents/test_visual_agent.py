"""Tests for the Visual Agent."""

from __future__ import annotations

import pytest

from fashion_agent.agents.visual_agent import VisualAgent
from fashion_agent.memory.manager import MemoryManager
from fashion_agent.skills.registry import get_registry


@pytest.fixture
async def agent():
    memory = MemoryManager()
    await memory.initialize()
    a = VisualAgent(skill_registry=get_registry(), memory=memory)
    yield a
    await memory.shutdown()


class TestVisualAgent:
    async def test_generate_images_for_article(self, agent: VisualAgent):
        result = await agent.execute(
            task_id="test-v01",
            instruction="Generate images",
            params={"article_id": "0126589003"},
        )
        assert result["success"] is True
        assert result["agent"] == "visual_agent"
        assert result["total_images"] >= 3
        assert "product_shot" in [i["type"] for i in result["images"]]

    async def test_custom_image_types(self, agent: VisualAgent):
        result = await agent.execute(
            task_id="test-v02",
            instruction="Generate flat lay",
            params={
                "article_id": "0130025001",
                "image_types": ["flat_lay", "detail_closeup"],
            },
        )
        assert result["success"] is True
        types = [i["type"] for i in result["images"]]
        assert "product_shot" in types
        assert "flat_lay" in types

    async def test_quality_summary(self, agent: VisualAgent):
        result = await agent.execute(
            task_id="test-v03",
            instruction="Generate images",
            params={"article_id": "0108775015"},
        )
        assert "quality_summary" in result
        qs = result["quality_summary"]
        assert qs["total"] == result["total_images"]
        assert qs["high_quality"] + qs["needs_review"] == qs["total"]
