"""Tests for the Design Agent."""

from __future__ import annotations

import pytest

from fashion_agent.agents.design_agent import DesignAgent
from fashion_agent.memory.manager import MemoryManager
from fashion_agent.skills.registry import get_registry


@pytest.fixture
async def agent():
    memory = MemoryManager()
    await memory.initialize()
    a = DesignAgent(skill_registry=get_registry(), memory=memory)
    yield a
    await memory.shutdown()


class TestDesignAgent:
    async def test_basic_proposal(self, agent: DesignAgent):
        result = await agent.execute(
            task_id="test-d01",
            instruction="Design a spring dress",
            params={"category": "Dress", "season": "spring"},
        )
        assert result["success"] is True
        assert result["agent"] == "design_agent"
        assert "design_proposal" in result
        assert result["design_proposal"]["season"] == "spring"
        assert result["design_proposal"]["product_category"] == "Dress"

    async def test_with_reference_article(self, agent: DesignAgent):
        result = await agent.execute(
            task_id="test-d02",
            instruction="Design upgrade based on cotton dress",
            params={
                "category": "Dress",
                "season": "summer",
                "article_id": "0126589003",
            },
        )
        assert result["success"] is True
        assert result["reference_article"] is not None
        assert result["competitor_context"] is not None

    async def test_different_categories(self, agent: DesignAgent):
        for cat in ["T-shirt", "Jacket", "Hoodie"]:
            result = await agent.execute(
                task_id=f"test-d-{cat}",
                instruction=f"Design a {cat}",
                params={"category": cat, "season": "autumn"},
            )
            assert result["success"] is True
            assert result["design_proposal"]["product_category"] == cat
