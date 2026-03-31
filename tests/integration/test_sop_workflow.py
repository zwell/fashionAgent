"""Integration tests for the New Product SOP workflow."""

from __future__ import annotations

import pytest

from fashion_agent.memory.manager import MemoryManager
from fashion_agent.orchestrator.workflows.new_product import NewProductWorkflow
from fashion_agent.skills.registry import get_registry


@pytest.fixture
async def workflow():
    memory = MemoryManager()
    await memory.initialize()
    wf = NewProductWorkflow(skill_registry=get_registry(), memory=memory)
    yield wf
    await memory.shutdown()


class TestNewProductSOPWorkflow:
    async def test_full_sop_flow(self, workflow: NewProductWorkflow):
        """Design → parallel(visual+marketing) → review → aggregate."""
        result = await workflow.run(
            instruction="Launch cotton dress for spring",
            params={
                "article_id": "0126589003",
                "season": "spring",
                "category": "Dress",
            },
        )
        assert result["status"] == "completed"
        assert result["workflow"] == "new_product_sop"

        # Design output
        assert "design" in result
        assert result["design"]["proposal"] != {}

        # Visual output (ran in parallel with marketing)
        assert "visuals" in result
        assert result["visuals"]["total_images"] >= 3

        # Marketing output (ran in parallel with visual)
        assert "marketing" in result
        assert result["marketing"]["selected_copy"] != ""

        # Review
        assert result["review_status"] in ("approved", "auto_approved")

        # Checklist
        checklist = result["launch_checklist"]
        assert len(checklist) == 4
        items = {c["item"] for c in checklist}
        assert items == {"设计提案", "商品图片", "营销文案", "人工审核"}

    async def test_sop_with_different_category(self, workflow: NewProductWorkflow):
        result = await workflow.run(
            instruction="Launch hoodie for autumn",
            params={
                "article_id": "0130025001",
                "season": "autumn",
                "category": "Hoodie",
            },
        )
        assert result["status"] == "completed"
        assert result["design"]["proposal"]["product_category"] == "Hoodie"

    async def test_sop_with_review_approved(self, workflow: NewProductWorkflow):
        result = await workflow.run(
            instruction="Launch dress",
            params={"article_id": "0126589003", "season": "spring"},
            review_status="approved",
        )
        assert result["status"] == "completed"
        assert result["review_status"] == "approved"

    async def test_parallel_execution_produces_both_results(
        self, workflow: NewProductWorkflow
    ):
        """Verify visual and marketing agents both produce output."""
        result = await workflow.run(
            instruction="Launch puffer jacket for winter",
            params={
                "article_id": "0142702004",
                "season": "winter",
                "category": "Jacket",
            },
        )
        assert result["visuals"]["total_images"] >= 3
        variants = result["marketing"]["all_variants"]
        assert "product_description" in variants
        assert "promotion" in variants
        assert "social_media" in variants
