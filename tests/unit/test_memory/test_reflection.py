"""Tests for the Reflection Engine."""

from __future__ import annotations

import pytest

from fashion_agent.memory.manager import MemoryManager
from fashion_agent.memory.reflection import ReflectionEngine


@pytest.fixture
async def engine():
    mm = MemoryManager()
    await mm.initialize()
    e = ReflectionEngine(mm)
    yield e
    await mm.shutdown()


class TestReflectionEngine:
    async def test_record_and_reflect(self, engine: ReflectionEngine):
        await engine.record_decision(
            task_id="t1",
            agent="marketing_agent",
            decision_type="copywriting",
            context={"article_id": "0126589003"},
            outcome={"success": True},
        )
        await engine.record_decision(
            task_id="t2",
            agent="supply_chain_agent",
            decision_type="restock",
            context={"article_id": "0130025001"},
            outcome={"success": True},
        )

        result = await engine.reflect()
        assert result["total_decisions"] == 2
        assert result["analysis"]["successes"] == 2
        assert result["analysis"]["success_rate"] == 1.0
        assert len(result["insights"]) >= 1

    async def test_reflect_no_decisions(self, engine: ReflectionEngine):
        result = await engine.reflect(target_date="2020-01-01")
        assert result["total_decisions"] == 0

    async def test_low_success_rate_insight(self, engine: ReflectionEngine):
        for i in range(5):
            await engine.record_decision(
                task_id=f"t{i}",
                agent="data_agent",
                decision_type="forecast",
                context={},
                outcome={"success": i < 1},
            )

        result = await engine.reflect()
        assert result["analysis"]["success_rate"] < 0.5
        warnings = [ins for ins in result["insights"] if ins["type"] == "warning"]
        assert len(warnings) >= 1

    async def test_agent_issue_detection(self, engine: ReflectionEngine):
        for i in range(4):
            await engine.record_decision(
                task_id=f"ok{i}",
                agent="marketing_agent",
                decision_type="copy",
                context={},
                outcome={"success": True},
            )
        for i in range(4):
            await engine.record_decision(
                task_id=f"fail{i}",
                agent="visual_agent",
                decision_type="image",
                context={},
                outcome={"success": False},
            )

        result = await engine.reflect()
        agent_issues = [
            ins for ins in result["insights"] if ins.get("type") == "agent_issue"
        ]
        assert len(agent_issues) >= 1
        assert agent_issues[0]["agent"] == "visual_agent"

    async def test_recent_insights(self, engine: ReflectionEngine):
        await engine.record_decision(
            task_id="t1",
            agent="marketing_agent",
            decision_type="copy",
            context={},
            outcome={"success": True},
        )
        await engine.reflect()

        recent = await engine.get_recent_insights(days=1)
        assert len(recent) >= 1
