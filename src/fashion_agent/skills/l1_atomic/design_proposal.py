"""L1 Skill: Design Proposal — generate a product design brief from trends + reference."""

from __future__ import annotations

from fashion_agent.core.data_loader import get_article_by_id
from fashion_agent.skills.base import skill
from fashion_agent.skills.l1_atomic.trend_analysis import trend_analysis


@skill(
    name="设计提案",
    description="基于时尚趋势和参考商品，生成新产品的设计提案（色彩、材质、版型、细节）",
    tags=["设计", "提案", "趋势", "创意"],
    examples=[
        "为春季设计一款连衣裙",
        "基于这款T恤设计一个升级版",
        "生成一份秋冬外套的设计brief",
    ],
)
async def design_proposal(
    category: str = "Dress",
    season: str = "spring",
    reference_article_id: str | None = None,
    style_keywords: list[str] | None = None,
) -> dict:
    trends = await trend_analysis(season=season)
    if not trends.get("success"):
        return trends

    reference = None
    if reference_article_id:
        article = get_article_by_id(reference_article_id)
        if article:
            reference = {
                "prod_name": article.prod_name,
                "product_type": article.product_type_name,
                "colour": article.colour_group_name,
                "appearance": article.graphical_appearance_name,
                "detail_desc": article.detail_desc,
            }

    colors = trends["trending_colors"]
    materials = trends["trending_materials"]
    styles = trends["trending_styles"]
    patterns = trends["trending_patterns"]

    keywords = style_keywords or []

    primary_color = colors[0] if colors else "Black"
    accent_color = colors[1] if len(colors) > 1 else "White"
    material = materials[0] if materials else "Cotton"
    silhouette = styles[0] if styles else "Regular"
    pattern = patterns[0] if patterns else "Solid"

    if "elegant" in keywords or "优雅" in keywords:
        silhouette = "Tailored" if "Tailored" in styles else silhouette
        pattern = "Solid"
    elif "casual" in keywords or "休闲" in keywords:
        silhouette = "Oversized" if "Oversized" in styles else silhouette
    elif "sporty" in keywords or "运动" in keywords:
        material = "Recycled Polyester" if "Recycled Polyester" in materials else material

    proposal = {
        "product_category": category,
        "season": season,
        "color_palette": {
            "primary": primary_color,
            "accent": accent_color,
            "options": colors,
        },
        "material": {
            "primary": material,
            "alternatives": materials,
        },
        "silhouette": silhouette,
        "pattern": pattern,
        "design_details": [
            f"{silhouette} silhouette in {material}",
            f"Primary color: {primary_color} with {accent_color} accents",
            f"Pattern: {pattern}",
            f"Inspired by {season} {trends['trending_styles'][1]} trend"
            if len(trends["trending_styles"]) > 1
            else "",
        ],
        "target_audience": _infer_audience(category),
        "estimated_price_range": _estimate_price(category),
    }

    description = (
        f"【{season.title()} {category} 设计提案】\n\n"
        f"主色调：{primary_color}，辅助色：{accent_color}\n"
        f"面料：{material}\n"
        f"版型：{silhouette}，图案：{pattern}\n\n"
        f"设计理念：融合{season}季{silhouette}轮廓趋势，"
        f"选用{material}面料，以{primary_color}为基调，"
        f"打造兼具时尚感与舒适度的{category}单品。"
    )

    return {
        "success": True,
        "proposal": proposal,
        "description": description,
        "reference_article": reference,
        "trend_basis": {
            "season": season,
            "colors": colors,
            "materials": materials,
            "styles": styles,
        },
    }


def _infer_audience(category: str) -> str:
    upper = category.lower()
    if any(w in upper for w in ["dress", "skirt", "blouse", "bodysuit"]):
        return "Women 20-40"
    if any(w in upper for w in ["blazer", "chino", "swim"]):
        return "Men 25-45"
    if any(w in upper for w in ["kid", "baby"]):
        return "Children 3-12"
    return "Unisex 18-45"


def _estimate_price(category: str) -> dict:
    ranges = {
        "T-shirt": (9.99, 19.99),
        "Dress": (24.99, 49.99),
        "Jacket": (39.99, 79.99),
        "Coat": (59.99, 129.99),
        "Blazer": (49.99, 89.99),
        "Hoodie": (19.99, 34.99),
        "Trousers": (24.99, 49.99),
        "Shorts": (14.99, 29.99),
        "Skirt": (19.99, 39.99),
        "Blouse": (19.99, 39.99),
        "Sweater": (24.99, 44.99),
    }
    low, high = ranges.get(category, (14.99, 39.99))
    return {"low": low, "high": high, "currency": "USD"}
