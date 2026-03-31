"""L1 Skill: Image Generation — simulate product image generation.

In production this would call DALL-E / Midjourney / Stable Diffusion.
For the demo we return structured metadata describing the generated images.
"""

from __future__ import annotations

import hashlib
import random

from fashion_agent.core.data_loader import get_article_by_id
from fashion_agent.skills.base import skill


@skill(
    name="图片生成",
    description="根据设计描述或商品信息生成商品图、模特图和场景图的元数据",
    tags=["图片", "视觉", "生成", "AI"],
    examples=[
        "生成一张红色连衣裙的商品图",
        "生成模特穿搭图",
        "创建一组商品展示图",
    ],
)
async def image_generation(
    article_id: str | None = None,
    description: str = "",
    image_types: list[str] | None = None,
    style: str = "commercial",
) -> dict:
    if article_id:
        article = get_article_by_id(article_id)
        if article is None:
            return {"success": False, "message": f"Article {article_id} not found"}
        description = description or (
            f"{article.colour_group_name} {article.prod_name}, "
            f"{article.graphical_appearance_name} pattern, "
            f"{article.detail_desc}"
        )
        color = article.colour_group_name
        category = article.product_type_name
    else:
        color = "Unknown"
        category = "Product"

    if not description:
        return {"success": False, "message": "Either article_id or description is required"}

    types = image_types or ["product_shot", "model_shot", "lifestyle"]
    images = []

    for img_type in types:
        seed = hashlib.md5(f"{description}{img_type}{style}".encode()).hexdigest()[:8]
        w, h = _get_dimensions(img_type)

        prompt = _build_prompt(description, img_type, style, color, category)

        images.append({
            "type": img_type,
            "prompt": prompt,
            "dimensions": {"width": w, "height": h},
            "seed": seed,
            "placeholder_url": f"https://placehold.co/{w}x{h}/EEE/333?text={img_type}",
            "generation_params": {
                "model": "stable-diffusion-xl",
                "style": style,
                "steps": 30,
                "cfg_scale": 7.5,
            },
            "quality_score": round(random.uniform(0.82, 0.98), 2),
        })

    return {
        "success": True,
        "description": description,
        "total_images": len(images),
        "images": images,
    }


def _get_dimensions(img_type: str) -> tuple[int, int]:
    dims = {
        "product_shot": (1024, 1024),
        "model_shot": (768, 1152),
        "lifestyle": (1152, 768),
        "detail_closeup": (1024, 1024),
        "flat_lay": (1024, 1024),
    }
    return dims.get(img_type, (1024, 1024))


def _build_prompt(
    description: str, img_type: str, style: str, color: str, category: str
) -> str:
    base = f"{description}, {style} photography"

    modifiers = {
        "product_shot": (
            f"studio product photograph of {color} {category}, "
            f"clean white background, soft studio lighting, "
            f"high-resolution, e-commerce ready"
        ),
        "model_shot": (
            f"fashion editorial photograph, model wearing {color} {category}, "
            f"neutral studio background, full-body shot, "
            f"professional lighting, lookbook style"
        ),
        "lifestyle": (
            f"lifestyle photograph featuring {color} {category}, "
            f"natural setting, warm lighting, "
            f"aspirational mood, editorial quality"
        ),
        "detail_closeup": (
            f"macro detail shot of {color} {category}, "
            f"fabric texture visible, high detail, "
            f"studio lighting"
        ),
        "flat_lay": (
            f"flat lay arrangement of {color} {category} "
            f"with complementary accessories, "
            f"clean background, overhead shot"
        ),
    }

    specific = modifiers.get(img_type, base)
    return f"{specific}. {description}"
