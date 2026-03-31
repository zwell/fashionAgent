"""Evaluation endpoints — run quality scoring and view reports."""

from __future__ import annotations

from fastapi import APIRouter

from fashion_agent.evaluation.runner import run_evaluation
from fashion_agent.evaluation.scorer import AgentEvaluator
from fashion_agent.gateway.dependencies import get_master_agent

router = APIRouter()


@router.post("/eval/run")
async def run_eval_suite():
    """Execute the full evaluation suite across all task types."""
    master = get_master_agent()
    return await run_evaluation(master)


@router.post("/eval/score")
async def score_single(task_type: str, result: dict):
    """Score a single task result against quality criteria."""
    evaluator = AgentEvaluator()
    report = evaluator.evaluate(task_type, result)
    return report.to_dict()
