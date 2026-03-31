"""L1 Skill: ERP Inventory Query — look up stock levels for a given SKU."""

from __future__ import annotations

from fashion_agent.core.data_loader import get_article_by_id, get_inventory_for_article
from fashion_agent.skills.base import skill


@skill(
    name="查询库存",
    description="查询指定商品的当前库存数量、仓库分布和可用状态",
    tags=["库存", "ERP", "供应链"],
    examples=[
        "帮我查一下SKU 0108775015的库存",
        "A仓还有多少件红色连衣裙",
        "哪些商品库存不足",
    ],
)
async def erp_inventory_query(article_id: str) -> dict:
    article = get_article_by_id(article_id)
    if article is None:
        return {"success": False, "message": f"Article {article_id} not found"}

    inventory = get_inventory_for_article(article_id)
    if not inventory:
        return {"success": False, "message": f"No inventory records for {article_id}"}

    total_qty = sum(inv.quantity for inv in inventory)
    warehouses = [
        {
            "warehouse": inv.warehouse,
            "quantity": inv.quantity,
            "is_low_stock": inv.is_low_stock,
            "needs_reorder": inv.needs_reorder,
        }
        for inv in inventory
    ]

    return {
        "success": True,
        "article_id": article_id,
        "prod_name": article.prod_name,
        "total_quantity": total_qty,
        "retail_price": inventory[0].retail_price,
        "unit_cost": inventory[0].unit_cost,
        "warehouses": warehouses,
        "any_low_stock": any(inv.is_low_stock for inv in inventory),
    }
