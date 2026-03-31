"""L2 Composite Skill: Clearance Workflow — decide whether to discount slow-moving stock."""

from __future__ import annotations

from fashion_agent.core.data_loader import get_article_by_id
from fashion_agent.skills.base import skill
from fashion_agent.skills.l1_atomic.competitor import competitor_analysis
from fashion_agent.skills.l1_atomic.copywriting import generate_copywriting
from fashion_agent.skills.l1_atomic.erp_inventory import erp_inventory_query
from fashion_agent.skills.l1_atomic.sales_forecast import sales_forecast


@skill(
    name="清仓决策",
    description="综合库存积压、竞品价格和销量趋势，制定清仓策略并生成促销文案",
    tags=["清仓", "促销", "库存", "竞品"],
    examples=[
        "这款商品是否需要清仓",
        "帮我制定清仓策略",
        "滞销品怎么处理",
    ],
    level="L2",
)
async def clearance_workflow(article_id: str) -> dict:
    article = get_article_by_id(article_id)
    if article is None:
        return {"success": False, "message": f"Article {article_id} not found"}

    inventory_result = await erp_inventory_query(article_id=article_id)
    forecast_result = await sales_forecast(article_id=article_id, days=30)
    competitor_result = await competitor_analysis(article_id=article_id)

    total_stock = inventory_result.get("total_quantity", 0)
    predicted_sales = forecast_result.get("predicted_sales_next_days", 0)
    retail_price = inventory_result.get("retail_price", 0)
    unit_cost = inventory_result.get("unit_cost", 0)

    overstock_ratio = total_stock / max(predicted_sales, 1)
    avg_comp_price = competitor_result.get("avg_competitor_price", retail_price)

    if overstock_ratio > 3:
        strategy = "deep_discount"
        discount_pct = 0.40
        reasoning = f"库存是预测销量的{overstock_ratio:.1f}倍，建议大幅折扣清仓"
    elif overstock_ratio > 2:
        strategy = "moderate_discount"
        discount_pct = 0.25
        reasoning = f"库存偏高（{overstock_ratio:.1f}倍），适度促销加速消化"
    elif retail_price > avg_comp_price * 1.2:
        strategy = "price_match"
        discount_pct = round(1 - avg_comp_price / retail_price, 2)
        reasoning = f"定价高于竞品均价（¥{avg_comp_price:.2f}），建议调价"
    else:
        strategy = "hold"
        discount_pct = 0
        reasoning = "库存和定价均在合理范围，暂不需要清仓"

    promo_copy = None
    if strategy != "hold":
        copy_result = await generate_copywriting(
            article_id=article_id,
            style="promotion",
            price=retail_price,
            discount_pct=discount_pct,
        )
        promo_copy = copy_result.get("copy_text")

    return {
        "success": True,
        "article_id": article_id,
        "prod_name": article.prod_name,
        "strategy": strategy,
        "discount_pct": discount_pct,
        "reasoning": reasoning,
        "overstock_ratio": round(overstock_ratio, 2),
        "financials": {
            "current_retail_price": retail_price,
            "sale_price": round(retail_price * (1 - discount_pct), 2),
            "unit_cost": unit_cost,
            "margin_after_discount": round(retail_price * (1 - discount_pct) - unit_cost, 2),
        },
        "promo_copy": promo_copy,
    }
