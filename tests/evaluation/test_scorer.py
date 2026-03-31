"""Tests for the evaluation scoring framework."""

from __future__ import annotations

from fashion_agent.evaluation.scorer import AgentEvaluator


class TestEvalScorer:
    def test_copywriting_eval(self):
        evaluator = AgentEvaluator()
        result = {
            "task_id": "t1",
            "status": "completed",
            "results": [{
                "success": True,
                "agent": "marketing_agent",
                "selected_copy": "这是一段足够长的促销文案" * 5,
                "all_variants": {
                    "product_description": "desc",
                    "promotion": "promo",
                    "social_media": "social",
                },
            }],
        }
        report = evaluator.evaluate("copywriting", result)
        assert report.all_passed
        assert report.overall_score >= 0.8

    def test_launch_eval(self):
        evaluator = AgentEvaluator()
        result = {
            "task_id": "t2",
            "status": "completed",
            "design": {
                "proposal": {"product_category": "Dress", "season": "spring"},
                "description": "A spring dress",
            },
            "visuals": {
                "total_images": 3,
                "images": [{"type": "product_shot"}, {"type": "model_shot"}, {"type": "lifestyle"}],
            },
            "marketing": {
                "selected_copy": "Beautiful spring dress",
                "all_variants": {"product_description": "x", "promotion": "y"},
            },
            "launch_checklist": [
                {"item": "设计提案", "done": True},
                {"item": "商品图片", "done": True},
                {"item": "营销文案", "done": True},
                {"item": "人工审核", "done": True},
            ],
        }
        report = evaluator.evaluate("new_product_launch", result)
        assert report.all_passed
        assert report.overall_score >= 0.9

    def test_restock_eval(self):
        evaluator = AgentEvaluator()
        result = {
            "task_id": "t3",
            "status": "completed",
            "results": [{
                "success": True,
                "restock_recommendation": {
                    "should_reorder": True,
                    "urgency": "high",
                    "reorder_quantity": 500,
                },
            }],
        }
        report = evaluator.evaluate("restock", result)
        assert report.all_passed

    def test_failed_task(self):
        evaluator = AgentEvaluator()
        result = {"task_id": "t4", "status": "failed", "results": []}
        report = evaluator.evaluate("copywriting", result)
        assert not report.all_passed
        assert report.overall_score < 0.5

    def test_trend_eval(self):
        evaluator = AgentEvaluator()
        result = {
            "task_id": "t5",
            "status": "completed",
            "results": [{
                "trend_data": {
                    "trending_colors": ["Lavender", "Sage", "Pink", "Blue"],
                    "summary": "Spring trends emphasize pastel tones",
                },
            }],
        }
        report = evaluator.evaluate("trend_analysis", result)
        assert report.all_passed

    def test_report_to_dict(self):
        evaluator = AgentEvaluator()
        result = {"task_id": "t6", "status": "completed", "results": []}
        report = evaluator.evaluate("general", result)
        d = report.to_dict()
        assert "overall_score" in d
        assert "metrics" in d
        assert isinstance(d["metrics"], list)
