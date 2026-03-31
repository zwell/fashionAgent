"""Tests for the Marketing Agent."""

from __future__ import annotations

import pytest

from fashion_agent.agents.marketing_agent import MarketingAgent
from fashion_agent.memory.manager import MemoryManager
from fashion_agent.skills.registry import get_registry


@pytest.fixture
async def agent():
    memory = MemoryManager()
    await memory.initialize()
    a = MarketingAgent(skill_registry=get_registry(), memory=memory)
    yield a
    await memory.shutdown()


class TestMarketingAgent:
    async def test_generate_all_variants(self, agent: MarketingAgent):
        result = await agent.execute(
            task_id="test-001",
            instruction="Generate copy for article",
            params={"article_id": "0126589003"},
        )
        assert result["success"] is True
        assert "all_variants" in result
        assert len(result["all_variants"]) == 3

    async def test_missing_article_id(self, agent: MarketingAgent):
        result = await agent.execute(
            task_id="test-002",
            instruction="Generate copy",
            params={},
        )
        assert result["success"] is False

    async def test_preferred_style(self, agent: MarketingAgent):
        result = await agent.execute(
            task_id="test-003",
            instruction="Generate promo copy",
            params={"article_id": "0130025001", "preferred_style": "promotion"},
        )
        assert result["success"] is True
        assert result["selected_style"] == "promotion"
        assert "特惠" in result["selected_copy"]
