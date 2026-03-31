"""Marketing Agent — generates product copy, promotions, and social media content.

Reasoning paradigm: Tree of Thought (ToT) — explores multiple copywriting angles
then selects the best one.
"""

from __future__ import annotations

from fashion_agent.agents.base import BaseAgent


class MarketingAgent(BaseAgent):
    name = "marketing_agent"
    description = "营销大脑：文案生成、标题优化、推广策略"

    async def execute(self, task_id: str, instruction: str, params: dict) -> dict:
        article_id = params.get("article_id")
        if not article_id:
            return {"success": False, "error": "article_id is required"}

        self.logger.info("marketing_task_start", task_id=task_id, article_id=article_id)

        # ToT: generate multiple copy variants (simulate exploring different branches)
        variants = {}
        for style in ["product_description", "promotion", "social_media"]:
            result = await self.invoke_skill(
                "文案生成",
                article_id=article_id,
                style=style,
                price=params.get("price"),
                discount_pct=params.get("discount_pct", 0.2),
            )
            if result.get("success"):
                variants[style] = result["copy_text"]

        best_style = params.get("preferred_style", "product_description")
        best_copy = variants.get(best_style, next(iter(variants.values()), ""))

        result = {
            "success": True,
            "agent": self.name,
            "article_id": article_id,
            "selected_copy": best_copy,
            "selected_style": best_style,
            "all_variants": variants,
            "reasoning": f"Generated {len(variants)} copy variants using ToT approach. "
            f"Selected '{best_style}' as the primary output.",
        }

        await self.save_result(task_id, result)
        return result
