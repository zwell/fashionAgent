"""L1 Skill: Competitor Analysis — simulated competitive intelligence."""

from __future__ import annotations

import random

from fashion_agent.core.data_loader import get_article_by_id
from fashion_agent.skills.base import skill

_COMPETITOR_BRANDS = ["ZARA", "UNIQLO", "GAP", "Mango", "ASOS"]


@skill(
    name="竞品分析",
    description="分析同品类竞品的价格、销量和市场定位",
    tags=["竞品", "市场分析", "定价"],
    examples=[
        "分析一下连衣裙品类的竞品情况",
        "ZARA同类产品卖多少钱",
    ],
)
async def competitor_analysis(article_id: str) -> dict:
    article = get_article_by_id(article_id)
    if article is None:
        return {"success": False, "message": f"Article {article_id} not found"}

    competitors = []
    for brand in random.sample(_COMPETITOR_BRANDS, k=3):
        base_price = random.uniform(8, 80)
        competitors.append(
            {
                "brand": brand,
                "similar_product": f"{brand} {article.product_type_name}",
                "price": round(base_price, 2),
                "estimated_monthly_sales": random.randint(500, 5000),
                "rating": round(random.uniform(3.5, 4.8), 1),
            }
        )

    avg_competitor_price = sum(c["price"] for c in competitors) / len(competitors)

    return {
        "success": True,
        "article_id": article_id,
        "prod_name": article.prod_name,
        "product_type": article.product_type_name,
        "competitors": competitors,
        "avg_competitor_price": round(avg_competitor_price, 2),
        "market_position": (
            "premium" if avg_competitor_price < 20
            else "mid-range" if avg_competitor_price < 50
            else "luxury"
        ),
    }
