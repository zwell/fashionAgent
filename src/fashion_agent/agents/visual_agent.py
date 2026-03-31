"""Visual Agent — generates product images, model shots, and lifestyle photos.

Reasoning paradigm: ReAct (Reason + Act)
  Observe: read the design proposal or article information
  Think:   determine which image types are needed
  Act:     invoke image generation for each type
  Evaluate: check quality scores and retry if needed
"""

from __future__ import annotations

from fashion_agent.agents.base import BaseAgent


class VisualAgent(BaseAgent):
    name = "visual_agent"
    description = "视觉生产：生成商品图、模特图、场景图"

    async def execute(self, task_id: str, instruction: str, params: dict) -> dict:
        article_id = params.get("article_id")
        description = params.get("description", "")
        image_types = params.get(
            "image_types", ["product_shot", "model_shot", "lifestyle"]
        )
        style = params.get("image_style", "commercial")

        self.logger.info(
            "visual_task_start",
            task_id=task_id,
            article_id=article_id,
            types=image_types,
        )

        # ReAct: Observe — gather product information
        product_desc = description
        if article_id and not product_desc:
            inv_result = await self.invoke_skill("查询库存", article_id=article_id)
            product_desc = inv_result.get("prod_name", "fashion product")
            self.logger.info("react_observe", step="product_info_gathered")

        # ReAct: Think — decide image generation strategy
        if "product_shot" not in image_types:
            image_types = ["product_shot"] + image_types
        self.logger.info(
            "react_think", step="strategy_decided", types=image_types
        )

        # ReAct: Act — generate images
        gen_result = await self.invoke_skill(
            "图片生成",
            article_id=article_id,
            description=product_desc,
            image_types=image_types,
            style=style,
        )
        self.logger.info(
            "react_act",
            step="images_generated",
            count=gen_result.get("total_images", 0),
        )

        # ReAct: Evaluate — check quality
        images = gen_result.get("images", [])
        low_quality = [
            img for img in images if img.get("quality_score", 0) < 0.85
        ]

        result = {
            "success": gen_result.get("success", False),
            "agent": self.name,
            "task_id": task_id,
            "total_images": len(images),
            "images": images,
            "quality_summary": {
                "total": len(images),
                "high_quality": len(images) - len(low_quality),
                "needs_review": len(low_quality),
            },
            "reasoning": (
                f"ReAct visual generation: Observed product info, "
                f"decided on {len(image_types)} image types, "
                f"generated {len(images)} images. "
                f"{len(low_quality)} image(s) below quality threshold."
            ),
        }

        await self.save_result(task_id, result)
        return result
