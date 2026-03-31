"""Reflection Mechanism — daily batch analysis of agent decisions.

Each night the system:
  1. Gathers all agent actions/decisions for the day
  2. Analyses outcomes (success vs failure patterns)
  3. Extracts insights / lessons learned
  4. Writes insights into long-term memory
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from fashion_agent.core.logging import get_logger

logger = get_logger(__name__)


class ReflectionEngine:
    """Nightly reflection that turns daily decisions into long-term wisdom."""

    def __init__(self, memory_manager: Any) -> None:
        self._mm = memory_manager

    async def record_decision(
        self,
        task_id: str,
        agent: str,
        decision_type: str,
        context: dict,
        outcome: dict,
    ) -> None:
        """Record an agent decision for later reflection."""
        today = date.today().isoformat()
        entry = {
            "task_id": task_id,
            "agent": agent,
            "decision_type": decision_type,
            "context": context,
            "outcome": outcome,
            "date": today,
        }
        await self._mm.short_term.append_to_session(
            f"decisions:{today}", "entries", entry
        )

    async def reflect(self, target_date: str | None = None) -> dict:
        """Run the reflection process for a given date."""
        dt = target_date or date.today().isoformat()
        logger.info("reflection_start", date=dt)

        decisions = await self._gather_decisions(dt)
        if not decisions:
            return {
                "date": dt,
                "total_decisions": 0,
                "insights": [],
                "message": "No decisions recorded for this date",
            }

        analysis = self._analyze_decisions(decisions)
        insights = self._extract_insights(analysis)

        await self._persist_insights(dt, insights)

        logger.info(
            "reflection_complete",
            date=dt,
            decisions=len(decisions),
            insights=len(insights),
        )

        return {
            "date": dt,
            "total_decisions": len(decisions),
            "analysis": analysis,
            "insights": insights,
        }

    async def _gather_decisions(self, dt: str) -> list[dict]:
        session = await self._mm.short_term.get_session(f"decisions:{dt}")
        return session.get("entries", [])

    def _analyze_decisions(self, decisions: list[dict]) -> dict:
        by_agent: dict[str, list] = {}
        by_type: dict[str, list] = {}
        successes = 0
        failures = 0

        for d in decisions:
            agent = d.get("agent", "unknown")
            dtype = d.get("decision_type", "unknown")
            by_agent.setdefault(agent, []).append(d)
            by_type.setdefault(dtype, []).append(d)

            outcome = d.get("outcome", {})
            if outcome.get("success", False):
                successes += 1
            else:
                failures += 1

        return {
            "total": len(decisions),
            "successes": successes,
            "failures": failures,
            "success_rate": round(successes / max(len(decisions), 1), 2),
            "by_agent": {
                a: {
                    "count": len(ds),
                    "success": sum(
                        1 for d in ds if d.get("outcome", {}).get("success")
                    ),
                }
                for a, ds in by_agent.items()
            },
            "by_type": {
                t: {"count": len(ds)}
                for t, ds in by_type.items()
            },
        }

    def _extract_insights(self, analysis: dict) -> list[dict]:
        insights = []

        rate = analysis.get("success_rate", 0)
        if rate < 0.7:
            insights.append({
                "type": "warning",
                "message": f"Low success rate ({rate:.0%}). Review failing agents.",
                "priority": "high",
            })
        elif rate >= 0.95:
            insights.append({
                "type": "positive",
                "message": f"Excellent success rate ({rate:.0%}). System performing well.",
                "priority": "low",
            })

        for agent, stats in analysis.get("by_agent", {}).items():
            count = stats["count"]
            success = stats["success"]
            if count > 0 and success / count < 0.5:
                insights.append({
                    "type": "agent_issue",
                    "agent": agent,
                    "message": f"{agent} has low success ({success}/{count}). Needs investigation.",
                    "priority": "high",
                })

        if analysis["total"] > 20:
            insights.append({
                "type": "volume",
                "message": f"High decision volume ({analysis['total']}). Consider scaling.",
                "priority": "medium",
            })

        if not insights:
            insights.append({
                "type": "normal",
                "message": "System operating within normal parameters.",
                "priority": "low",
            })

        return insights

    async def _persist_insights(self, dt: str, insights: list[dict]) -> None:
        insight_id = f"reflection:{dt}"
        await self._mm.long_term.add_node(insight_id, "Reflection", {
            "date": dt,
            "insights": insights,
        })

        await self._mm.remember(
            f"reflection:{dt}",
            {"date": dt, "insights": insights},
            ttl=86400 * 7,
        )

    async def get_recent_insights(self, days: int = 7) -> list[dict]:
        results = []
        today = date.today()
        for i in range(days):
            dt = (today - timedelta(days=i)).isoformat()
            data = await self._mm.recall(f"reflection:{dt}")
            if data:
                results.append(data)
        return results
