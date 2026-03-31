"""L2 Composite Skill: Restock Workflow — combines inventory + forecast + supplier lookup."""

from __future__ import annotations

from fashion_agent.core.data_loader import get_article_by_id, get_supplier_for_garment_group
from fashion_agent.skills.base import skill
from fashion_agent.skills.l1_atomic.erp_inventory import erp_inventory_query
from fashion_agent.skills.l1_atomic.sales_forecast import sales_forecast


@skill(
    name="智能补货",
    description="结合库存状态、销量预测和供应商信息，生成智能补货建议",
    tags=["补货", "供应链", "库存", "预测"],
    examples=[
        "这款商品需要补货吗",
        "生成补货建议",
        "帮我做一个补货计划",
    ],
    level="L2",
)
async def restock_workflow(article_id: str, forecast_days: int = 30) -> dict:
    inventory_result = await erp_inventory_query(article_id=article_id)
    if not inventory_result.get("success"):
        return inventory_result

    forecast_result = await sales_forecast(article_id=article_id, days=forecast_days)

    article = get_article_by_id(article_id)
    supplier = get_supplier_for_garment_group(article.garment_group_name) if article else None

    total_stock = inventory_result["total_quantity"]
    predicted_demand = forecast_result.get("predicted_sales_next_days", 0)

    days_of_stock = round(total_stock / max(forecast_result.get("avg_daily_sales", 0.1), 0.1))
    reorder_qty = max(predicted_demand - total_stock + 50, 0)

    if supplier and reorder_qty > 0:
        reorder_qty = max(reorder_qty, supplier.min_order_quantity)

    urgency = "low"
    if inventory_result.get("any_low_stock"):
        urgency = "high"
    elif days_of_stock < forecast_days:
        urgency = "medium"

    recommendation = {
        "should_reorder": reorder_qty > 0,
        "reorder_quantity": reorder_qty,
        "urgency": urgency,
        "estimated_cost": (
            round(reorder_qty * inventory_result.get("unit_cost", 0), 2) if reorder_qty else 0
        ),
        "days_of_stock_remaining": days_of_stock,
    }

    if supplier:
        recommendation["supplier"] = {
            "name": supplier.name,
            "lead_time_days": supplier.lead_time_days,
            "min_order_quantity": supplier.min_order_quantity,
            "reliability_score": supplier.reliability_score,
        }

    return {
        "success": True,
        "article_id": article_id,
        "prod_name": inventory_result.get("prod_name", ""),
        "current_inventory": inventory_result,
        "sales_forecast": forecast_result,
        "recommendation": recommendation,
    }
