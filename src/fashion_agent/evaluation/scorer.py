"""Quality scoring framework for agent outputs.

Inspired by Ragas evaluation metrics, adapted for fashion e-commerce domain.
Evaluates agent outputs on multiple dimensions without requiring an external
LLM call — uses heuristic scoring suitable for unit testing and CI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fashion_agent.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EvalScore:
    """A single evaluation result."""

    metric: str
    score: float  # 0.0 – 1.0
    details: str = ""
    passed: bool = True


@dataclass
class EvalReport:
    """Aggregated evaluation report across multiple metrics."""

    task_type: str
    scores: list[EvalScore] = field(default_factory=list)

    @property
    def overall_score(self) -> float:
        if not self.scores:
            return 0.0
        return round(sum(s.score for s in self.scores) / len(self.scores), 3)

    @property
    def all_passed(self) -> bool:
        return all(s.passed for s in self.scores)

    def to_dict(self) -> dict:
        return {
            "task_type": self.task_type,
            "overall_score": self.overall_score,
            "all_passed": self.all_passed,
            "metrics": [
                {
                    "metric": s.metric,
                    "score": s.score,
                    "passed": s.passed,
                    "details": s.details,
                }
                for s in self.scores
            ],
        }


class AgentEvaluator:
    """Evaluate agent task outputs against quality criteria."""

    PASS_THRESHOLD = 0.6

    def evaluate(self, task_type: str, result: dict[str, Any]) -> EvalReport:
        report = EvalReport(task_type=task_type)

        report.scores.append(self._completeness(result))
        report.scores.append(self._success_rate(result))

        if task_type == "copywriting":
            report.scores.extend(self._eval_copywriting(result))
        elif task_type == "new_product_launch":
            report.scores.extend(self._eval_launch(result))
        elif task_type == "restock":
            report.scores.extend(self._eval_restock(result))
        elif task_type == "clearance":
            report.scores.extend(self._eval_clearance(result))
        elif task_type == "trend_analysis":
            report.scores.extend(self._eval_trend(result))

        logger.info(
            "evaluation_complete",
            task_type=task_type,
            overall=report.overall_score,
            passed=report.all_passed,
        )
        return report

    def _completeness(self, result: dict) -> EvalScore:
        """Check that required top-level fields are present."""
        required = {"task_id", "status"}
        present = required & set(result.keys())
        score = len(present) / max(len(required), 1)
        return EvalScore(
            metric="completeness",
            score=score,
            passed=score >= self.PASS_THRESHOLD,
            details=f"{len(present)}/{len(required)} required fields present",
        )

    def _success_rate(self, result: dict) -> EvalScore:
        status = result.get("status", "")
        score = 1.0 if status == "completed" else 0.0
        return EvalScore(
            metric="success",
            score=score,
            passed=score >= self.PASS_THRESHOLD,
            details=f"status={status}",
        )

    # ── Task-specific evaluators ─────────────────────────────

    def _eval_copywriting(self, result: dict) -> list[EvalScore]:
        scores = []
        results = result.get("results", [])
        if not results:
            return [EvalScore("copy_output", 0.0, "No agent results", False)]

        agent_out = results[0]
        copy = agent_out.get("selected_copy", "")
        variants = agent_out.get("all_variants", {})

        length_score = min(len(copy) / 50, 1.0)
        scores.append(EvalScore(
            "copy_length",
            round(length_score, 2),
            passed=length_score >= self.PASS_THRESHOLD,
            details=f"{len(copy)} chars",
        ))

        variety_score = len(variants) / 3.0
        scores.append(EvalScore(
            "copy_variety",
            round(min(variety_score, 1.0), 2),
            passed=variety_score >= self.PASS_THRESHOLD,
            details=f"{len(variants)} variants generated",
        ))

        return scores

    def _eval_launch(self, result: dict) -> list[EvalScore]:
        scores = []

        design = result.get("design", {})
        has_proposal = bool(design.get("proposal", {}).get("product_category"))
        scores.append(EvalScore(
            "design_proposal",
            1.0 if has_proposal else 0.0,
            passed=has_proposal,
            details="proposal present" if has_proposal else "missing",
        ))

        visuals = result.get("visuals", {})
        img_count = visuals.get("total_images", 0)
        img_score = min(img_count / 3, 1.0)
        scores.append(EvalScore(
            "visual_output",
            round(img_score, 2),
            passed=img_count >= 3,
            details=f"{img_count} images",
        ))

        marketing = result.get("marketing", {})
        has_copy = bool(marketing.get("selected_copy"))
        scores.append(EvalScore(
            "marketing_copy",
            1.0 if has_copy else 0.0,
            passed=has_copy,
            details="copy present" if has_copy else "missing",
        ))

        checklist = result.get("launch_checklist", [])
        done = sum(1 for c in checklist if c.get("done"))
        cl_score = done / max(len(checklist), 1)
        scores.append(EvalScore(
            "checklist_completion",
            round(cl_score, 2),
            passed=cl_score >= 0.75,
            details=f"{done}/{len(checklist)} items done",
        ))

        return scores

    def _eval_restock(self, result: dict) -> list[EvalScore]:
        scores = []
        results = result.get("results", [])
        if not results:
            return [EvalScore("restock_output", 0.0, "No results", False)]

        agent_out = results[0]
        rec = agent_out.get("restock_recommendation", {})
        has_rec = "should_reorder" in rec
        scores.append(EvalScore(
            "recommendation_present",
            1.0 if has_rec else 0.0,
            passed=has_rec,
            details="recommendation generated" if has_rec else "missing",
        ))

        has_urgency = "urgency" in rec
        scores.append(EvalScore(
            "urgency_classification",
            1.0 if has_urgency else 0.0,
            passed=has_urgency,
            details=f"urgency={rec.get('urgency', 'N/A')}",
        ))

        return scores

    def _eval_clearance(self, result: dict) -> list[EvalScore]:
        scores = []
        results = result.get("results", [])
        if not results:
            return [EvalScore("clearance_output", 0.0, "No results", False)]

        agent_out = results[0]
        clearance = agent_out.get("clearance_decision", {})
        strategy = clearance.get("strategy")
        valid_strategies = {"deep_discount", "moderate_discount", "price_match", "hold"}
        has_strategy = strategy in valid_strategies
        scores.append(EvalScore(
            "strategy_valid",
            1.0 if has_strategy else 0.0,
            passed=has_strategy,
            details=f"strategy={strategy}",
        ))

        has_financials = "financials" in clearance
        scores.append(EvalScore(
            "financial_analysis",
            1.0 if has_financials else 0.0,
            passed=has_financials,
        ))

        return scores

    def _eval_trend(self, result: dict) -> list[EvalScore]:
        scores = []
        results = result.get("results", [])
        if not results:
            return [EvalScore("trend_output", 0.0, "No results", False)]

        trend = results[0].get("trend_data", {})
        colors = trend.get("trending_colors", [])
        scores.append(EvalScore(
            "trend_colors",
            min(len(colors) / 3, 1.0),
            passed=len(colors) >= 3,
            details=f"{len(colors)} colors",
        ))

        has_summary = bool(trend.get("summary"))
        scores.append(EvalScore(
            "trend_summary",
            1.0 if has_summary else 0.0,
            passed=has_summary,
        ))

        return scores
