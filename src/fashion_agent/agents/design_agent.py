"""Design Agent — generates product design proposals based on trends and references.

Reasoning paradigm: Chain of Thought (CoT)
  Step 1: Analyse trend data for the target season
  Step 2: Identify reference product characteristics (if provided)
  Step 3: Synthesise a design proposal with colour, material, silhouette
"""

from __future__ import annotations

from fashion_agent.agents.base import BaseAgent


class DesignAgent(BaseAgent):
    name = "design_agent"
    description = "设计引擎：根据趋势和参考商品生成产品设计提案"

    async def execute(self, task_id: str, instruction: str, params: dict) -> dict:
        category = params.get("category", "Dress")
        season = params.get("season", "spring")
        reference_id = params.get("article_id") or params.get("reference_article_id")
        keywords = params.get("style_keywords", [])

        self.logger.info(
            "design_task_start",
            task_id=task_id,
            category=category,
            season=season,
        )

        # CoT Step 1: analyse trends
        trend_result = await self.invoke_skill("趋势分析", season=season)
        self.logger.info("cot_step1", step="trends_analysed", season=season)

        # CoT Step 2: generate design proposal
        proposal_result = await self.invoke_skill(
            "设计提案",
            category=category,
            season=season,
            reference_article_id=reference_id,
            style_keywords=keywords,
        )
        self.logger.info("cot_step2", step="proposal_generated")

        # CoT Step 3: generate competitor context for pricing
        comp_result = None
        if reference_id:
            comp_result = await self.invoke_skill("竞品分析", article_id=reference_id)
            self.logger.info("cot_step3", step="competitor_context")

        result = {
            "success": proposal_result.get("success", False),
            "agent": self.name,
            "task_id": task_id,
            "design_proposal": proposal_result.get("proposal", {}),
            "design_description": proposal_result.get("description", ""),
            "trend_basis": proposal_result.get("trend_basis", {}),
            "reference_article": proposal_result.get("reference_article"),
            "competitor_context": comp_result if comp_result else None,
            "reasoning": (
                f"CoT design process: (1) Analysed {season} trends — "
                f"key colours {trend_result.get('trending_colors', [])[:2]}, "
                f"(2) Generated {category} proposal, "
                f"(3) {'Checked competitor pricing' if comp_result else 'No reference'}."
            ),
        }

        await self.save_result(task_id, result)
        return result
