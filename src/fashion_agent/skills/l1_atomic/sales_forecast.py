"""L1 Skill: Sales Forecast — predict future demand for a given SKU."""

from __future__ import annotations

import random
from collections import Counter

from fashion_agent.core.data_loader import (
    get_article_by_id,
    get_transactions_for_article,
)
from fashion_agent.skills.base import skill


@skill(
    name="销量预测",
    description="基于历史销售数据预测指定SKU的未来销量趋势",
    tags=["销量", "预测", "数据分析"],
    examples=[
        "预测SKU 0130025001未来30天的销量",
        "这款连衣裙下个月能卖多少",
    ],
)
async def sales_forecast(article_id: str, days: int = 30) -> dict:
    article = get_article_by_id(article_id)
    if article is None:
        return {"success": False, "message": f"Article {article_id} not found"}

    transactions = get_transactions_for_article(article_id)
    if not transactions:
        return {
            "success": True,
            "article_id": article_id,
            "historical_sales": 0,
            "predicted_sales": 0,
            "confidence": 0.0,
            "message": "No historical data — prediction unreliable",
        }

    daily_sales = Counter(t.t_dat for t in transactions)
    avg_daily = len(transactions) / max(len(daily_sales), 1)

    noise = random.uniform(0.85, 1.15)
    predicted = round(avg_daily * days * noise)
    channel_split = Counter(t.sales_channel_id for t in transactions)

    return {
        "success": True,
        "article_id": article_id,
        "prod_name": article.prod_name,
        "historical_total_sales": len(transactions),
        "avg_daily_sales": round(avg_daily, 2),
        "predicted_sales_next_days": predicted,
        "forecast_days": days,
        "confidence": round(min(0.5 + len(transactions) * 0.05, 0.95), 2),
        "channel_breakdown": {
            "online": channel_split.get(1, 0),
            "offline": channel_split.get(2, 0),
        },
    }
