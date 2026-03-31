"""L2 Composite Skill: Product Launch — combine trends + copywriting for new product launch."""

from __future__ import annotations

from fashion_agent.core.data_loader import get_article_by_id
from fashion_agent.skills.base import skill
from fashion_agent.skills.l1_atomic.copywriting import generate_copywriting
from fashion_agent.skills.l1_atomic.trend_analysis import trend_analysis


@skill(
    name="新品上架",
    description="结合时尚趋势分析和文案生成，为新品上架提供完整方案",
    tags=["新品", "上架", "趋势", "文案"],
    examples=[
        "准备春季新品上架方案",
        "新品上线需要哪些准备",
    ],
    level="L2",
)
async def product_launch_workflow(article_id: str, season: str = "spring") -> dict:
    article = get_article_by_id(article_id)
    if article is None:
        return {"success": False, "message": f"Article {article_id} not found"}

    trend_result = await trend_analysis(season=season)

    desc_copy = await generate_copywriting(article_id=article_id, style="product_description")
    social_copy = await generate_copywriting(article_id=article_id, style="social_media")

    trend_alignment = []
    if trend_result.get("success"):
        colors = trend_result.get("trending_colors", [])
        for color in colors:
            if color.lower() in article.colour_group_name.lower():
                trend_alignment.append(f"颜色 {color} 符合{season}趋势")

        styles = trend_result.get("trending_styles", [])
        for s in styles:
            if s.lower() in article.detail_desc.lower():
                trend_alignment.append(f"版型 {s} 符合{season}趋势")

    return {
        "success": True,
        "article_id": article_id,
        "prod_name": article.prod_name,
        "season": season,
        "trend_analysis": trend_result,
        "trend_alignment": trend_alignment or ["该商品与当季趋势无直接关联，可作为基础款推广"],
        "product_description": desc_copy.get("copy_text", ""),
        "social_media_copy": social_copy.get("copy_text", ""),
        "launch_checklist": [
            "✅ 商品描述文案已生成",
            "✅ 社交媒体文案已生成",
            "✅ 趋势匹配度分析完成",
            "⬜ 商品图片（需 Visual Agent）",
            "⬜ 模特图片（需 Visual Agent）",
            "⬜ 定价策略确认",
            "⬜ 库存到位确认",
        ],
    }
