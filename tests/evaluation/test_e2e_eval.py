"""End-to-end evaluation: run all tasks through master agent and score them."""

from __future__ import annotations

import pytest

from fashion_agent.evaluation.runner import run_evaluation
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


class TestEndToEndEvaluation:
    async def test_full_eval_suite(self, master: MasterAgent):
        """Run the complete evaluation suite and verify quality."""
        result = await run_evaluation(master)

        assert result["total_cases"] == 9
        assert result["pass_rate"] >= 0.8, (
            f"Pass rate {result['pass_rate']} below threshold. "
            f"Failed: {result['failed']}/{result['total_cases']}"
        )
        assert result["average_score"] >= 0.7

        for report in result["reports"]:
            assert "overall_score" in report
            assert "metrics" in report

    async def test_individual_case_scores(self, master: MasterAgent):
        result = await run_evaluation(master)
        for report in result["reports"]:
            assert report["overall_score"] >= 0.5, (
                f"Case '{report['name']}' scored {report['overall_score']}"
            )
