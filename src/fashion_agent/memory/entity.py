"""Entity Memory — unified SKU profile spanning all three memory layers.

Combines short-term context, mid-term vector embeddings, and long-term
knowledge graph data into a single coherent SKU profile.
"""

from __future__ import annotations

from typing import Any

from fashion_agent.core.data_loader import (
    get_article_by_id,
    get_inventory_for_article,
    get_supplier_for_garment_group,
    get_transactions_for_article,
)
from fashion_agent.core.logging import get_logger

logger = get_logger(__name__)


class EntityMemory:
    """Build and query unified SKU profiles."""

    def __init__(self, memory_manager: Any) -> None:
        self._mm = memory_manager

    async def build_sku_profile(self, article_id: str) -> dict:
        """Construct a complete profile for a SKU across all data sources."""
        article = get_article_by_id(article_id)
        if article is None:
            return {"success": False, "message": f"Article {article_id} not found"}

        inventory = get_inventory_for_article(article_id)
        transactions = get_transactions_for_article(article_id)
        supplier = get_supplier_for_garment_group(article.garment_group_name)

        total_stock = sum(inv.quantity for inv in inventory)
        total_sales = len(transactions)
        avg_price = (
            sum(t.price for t in transactions) / total_sales if total_sales else 0
        )
        channels = {}
        for t in transactions:
            ch = "online" if t.sales_channel_id == 1 else "offline"
            channels[ch] = channels.get(ch, 0) + 1

        profile = {
            "article_id": article_id,
            "basic_info": {
                "name": article.prod_name,
                "type": article.product_type_name,
                "group": article.product_group_name,
                "colour": article.colour_group_name,
                "department": article.department_name,
                "description": article.detail_desc,
            },
            "inventory": {
                "total_stock": total_stock,
                "warehouses": [
                    {
                        "warehouse": inv.warehouse,
                        "quantity": inv.quantity,
                        "is_low_stock": inv.is_low_stock,
                    }
                    for inv in inventory
                ],
                "retail_price": inventory[0].retail_price if inventory else 0,
                "unit_cost": inventory[0].unit_cost if inventory else 0,
            },
            "sales": {
                "total_transactions": total_sales,
                "average_price": round(avg_price, 2),
                "channel_breakdown": channels,
            },
            "supplier": (
                {
                    "name": supplier.name,
                    "region": supplier.region,
                    "lead_time_days": supplier.lead_time_days,
                    "reliability": supplier.reliability_score,
                }
                if supplier
                else None
            ),
        }

        # Store in short-term memory
        await self._mm.remember(
            f"sku_profile:{article_id}", profile, ttl=3600
        )

        # Store vector embedding in mid-term memory
        embedding_text = (
            f"{article.prod_name} {article.product_type_name} "
            f"{article.colour_group_name} {article.detail_desc}"
        )
        await self._mm.mid_term.upsert_sku(
            article_id=article_id,
            text=embedding_text,
            metadata={
                "type": article.product_type_name,
                "colour": article.colour_group_name,
            },
        )

        # Store in knowledge graph
        await self._build_graph_for_sku(article_id, article, supplier)

        return {"success": True, "profile": profile}

    async def _build_graph_for_sku(self, article_id, article, supplier) -> None:
        graph = self._mm.long_term

        await graph.add_node(article_id, "SKU", {
            "name": article.prod_name,
            "type": article.product_type_name,
            "colour": article.colour_group_name,
        })

        cat_id = f"cat:{article.product_group_name}"
        await graph.add_node(cat_id, "Category", {"name": article.product_group_name})
        await graph.add_edge(article_id, cat_id, "BELONGS_TO")

        dept_id = f"dept:{article.department_name}"
        await graph.add_node(dept_id, "Department", {"name": article.department_name})
        await graph.add_edge(article_id, dept_id, "IN_DEPARTMENT")

        if supplier:
            await graph.add_node(supplier.supplier_id, "Supplier", {
                "name": supplier.name,
                "region": supplier.region,
            })
            await graph.add_edge(article_id, supplier.supplier_id, "SUPPLIED_BY")

    async def get_profile(self, article_id: str) -> dict | None:
        cached = await self._mm.recall(f"sku_profile:{article_id}")
        if cached:
            return cached
        result = await self.build_sku_profile(article_id)
        if result.get("success"):
            return result["profile"]
        return None

    async def find_similar_skus(self, article_id: str, top_k: int = 5) -> list[dict]:
        article = get_article_by_id(article_id)
        if article is None:
            return []
        query = (
            f"{article.prod_name} {article.product_type_name} "
            f"{article.colour_group_name} {article.detail_desc}"
        )
        results = await self._mm.mid_term.search_similar(query, top_k=top_k + 1)
        return [r for r in results if r["article_id"] != article_id][:top_k]

    async def get_sku_relationships(self, article_id: str) -> dict:
        return await self._mm.long_term.get_sku_graph(article_id)

    async def add_feedback(
        self, article_id: str, feedback_type: str, content: str
    ) -> None:
        feedback_id = f"feedback:{article_id}:{feedback_type}"
        await self._mm.long_term.add_node(feedback_id, "Feedback", {
            "type": feedback_type,
            "content": content,
        })
        await self._mm.long_term.add_edge(article_id, feedback_id, "HAS_FEEDBACK")

        await self._mm.short_term.append_to_session(
            f"feedback:{article_id}", "items", {
                "type": feedback_type,
                "content": content,
            }
        )
