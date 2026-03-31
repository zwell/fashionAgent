"""Integration tests for the Master Agent orchestrator."""

from __future__ import annotations

import pytest

from fashion_agent.core.models import TaskType
from fashion_agent.memory.manager import MemoryManager
from fashion_agent.orchestrator.master_agent import MasterAgent
from fashion_agent.skills.registry import get_registry


@pytest.fixture
async def master():
    memory = MemoryManager()
    await memory.initialize()
    agent = MasterAgent(skill_registry=get_registry(), memory=memory)
    yield agent
    await memory.shutdown()


class TestMasterAgentOrchestration:
    async def test_copywriting_task(self, master: MasterAgent):
        result = await master.run(
            task_type=TaskType.COPYWRITING.value,
            instruction="Generate copy for red dress",
            params={"article_id": "0126589003"},
        )
        assert result["status"] == "completed"
        assert result["all_success"] is True
        assert len(result["results"]) == 1
        assert result["results"][0]["agent"] == "marketing_agent"

    async def test_restock_task(self, master: MasterAgent):
        result = await master.run(
            task_type=TaskType.RESTOCK.value,
            instruction="Check restock for hoodie",
            params={"article_id": "0130025001"},
        )
        assert result["status"] == "completed"
        assert result["all_success"] is True

    async def test_clearance_task(self, master: MasterAgent):
        result = await master.run(
            task_type=TaskType.CLEARANCE.value,
            instruction="Clearance analysis for puffer jacket",
            params={"article_id": "0142702004"},
        )
        assert result["status"] == "completed"
        assert len(result["agents_involved"]) == 2

    async def test_trend_analysis_task(self, master: MasterAgent):
        result = await master.run(
            task_type=TaskType.TREND_ANALYSIS.value,
            instruction="Spring trends",
            params={"season": "spring"},
        )
        assert result["status"] == "completed"

    async def test_new_product_launch_sop(self, master: MasterAgent):
        """Test the full SOP workflow: design → parallel visual+marketing → review → aggregate."""
        result = await master.run(
            task_type=TaskType.NEW_PRODUCT_LAUNCH.value,
            instruction="Launch cotton dress for spring",
            params={"article_id": "0126589003", "season": "spring"},
        )
        assert result["status"] == "completed"
        assert result["workflow"] == "new_product_sop"
        assert "design" in result
        assert "visuals" in result
        assert "marketing" in result
        assert result["visuals"]["total_images"] >= 3
        assert result["marketing"]["selected_copy"] != ""
        assert len(result["launch_checklist"]) == 4
        assert all(c["done"] for c in result["launch_checklist"])
