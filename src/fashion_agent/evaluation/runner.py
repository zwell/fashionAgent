"""Evaluation runner — execute tasks and score them end-to-end."""

from __future__ import annotations

from typing import Any

from fashion_agent.core.models import TaskType
from fashion_agent.evaluation.scorer import AgentEvaluator, EvalReport
from fashion_agent.orchestrator.master_agent import MasterAgent

EVAL_SUITE: list[dict[str, Any]] = [
    {
        "name": "copywriting_dress_promo",
        "task_type": TaskType.COPYWRITING,
        "instruction": "Generate promotion copy for red dress",
        "params": {"article_id": "0126589003", "preferred_style": "promotion"},
    },
    {
        "name": "copywriting_hoodie_social",
        "task_type": TaskType.COPYWRITING,
        "instruction": "Generate social media copy for grey hoodie",
        "params": {"article_id": "0130025001", "preferred_style": "social_media"},
    },
    {
        "name": "restock_low_stock",
        "task_type": TaskType.RESTOCK,
        "instruction": "Restock analysis for low-stock cotton dress",
        "params": {"article_id": "0126589003", "forecast_days": 30},
    },
    {
        "name": "restock_healthy",
        "task_type": TaskType.RESTOCK,
        "instruction": "Restock analysis for well-stocked strap top",
        "params": {"article_id": "0108775015", "forecast_days": 30},
    },
    {
        "name": "clearance_puffer",
        "task_type": TaskType.CLEARANCE,
        "instruction": "Clearance analysis for puffer jacket",
        "params": {"article_id": "0142702004"},
    },
    {
        "name": "trend_spring",
        "task_type": TaskType.TREND_ANALYSIS,
        "instruction": "Spring fashion trends",
        "params": {"season": "spring"},
    },
    {
        "name": "trend_winter",
        "task_type": TaskType.TREND_ANALYSIS,
        "instruction": "Winter fashion trends",
        "params": {"season": "winter"},
    },
    {
        "name": "launch_dress_spring",
        "task_type": TaskType.NEW_PRODUCT_LAUNCH,
        "instruction": "Launch cotton dress for spring",
        "params": {"article_id": "0126589003", "season": "spring", "category": "Dress"},
    },
    {
        "name": "launch_jacket_winter",
        "task_type": TaskType.NEW_PRODUCT_LAUNCH,
        "instruction": "Launch puffer jacket for winter",
        "params": {
            "article_id": "0142702004",
            "season": "winter",
            "category": "Jacket",
        },
    },
]


async def run_evaluation(master: MasterAgent) -> dict:
    """Execute the full evaluation suite and return aggregated results."""
    evaluator = AgentEvaluator()
    reports: list[dict] = []
    passed = 0
    failed = 0

    for case in EVAL_SUITE:
        result = await master.run(
            task_type=case["task_type"].value,
            instruction=case["instruction"],
            params=case["params"],
        )
        report: EvalReport = evaluator.evaluate(case["task_type"].value, result)
        entry = {
            "name": case["name"],
            **report.to_dict(),
        }
        reports.append(entry)
        if report.all_passed:
            passed += 1
        else:
            failed += 1

    total = len(reports)
    avg_score = (
        sum(r["overall_score"] for r in reports) / total if total else 0
    )

    return {
        "total_cases": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / max(total, 1), 3),
        "average_score": round(avg_score, 3),
        "reports": reports,
    }
