"""Data Agent — sales forecasting, user profiling, trend insights.

Reasoning paradigm: Chain of Thought (CoT) — step-by-step data analysis.
"""

from __future__ import annotations

from fashion_agent.agents.base import BaseAgent


class DataAgent(BaseAgent):
    name = "data_agent"
    description = "数据分析：销量预测、用户画像分析、市场趋势"

    async def execute(self, task_id: str, instruction: str, params: dict) -> dict:
        article_id = params.get("article_id")
        analysis_type = params.get("analysis_type", "forecast")

        self.logger.info(
            "data_task_start",
            task_id=task_id,
            article_id=article_id,
            analysis_type=analysis_type,
        )

        if analysis_type == "forecast" and article_id:
            return await self._forecast(task_id, article_id, params)
        elif analysis_type == "trend":
            return await self._trend(task_id, params)
        elif analysis_type == "competitor" and article_id:
            return await self._competitor(task_id, article_id)
        else:
            return {"success": False, "error": f"Unknown analysis type: {analysis_type}"}

    async def _forecast(self, task_id: str, article_id: str, params: dict) -> dict:
        # CoT Step 1: gather sales data
        forecast = await self.invoke_skill(
            "销量预测",
            article_id=article_id,
            days=params.get("forecast_days", 30),
        )

        # CoT Step 2: contextualize with inventory
        inventory = await self.invoke_skill("查询库存", article_id=article_id)

        # CoT Step 3: synthesize insight
        total_stock = inventory.get("total_quantity", 0)
        predicted = forecast.get("predicted_sales_next_days", 0)
        sellthrough_days = round(total_stock / max(predicted / 30, 0.01))

        result = {
            "success": True,
            "agent": self.name,
            "analysis_type": "forecast",
            "article_id": article_id,
            "forecast": forecast,
            "inventory_context": {
                "total_stock": total_stock,
                "sellthrough_days": sellthrough_days,
            },
            "insight": (
                f"CoT analysis: current stock {total_stock} units, "
                f"predicted {predicted} sales in next {params.get('forecast_days', 30)} days. "
                f"At current rate, stock lasts ~{sellthrough_days} days."
            ),
        }
        await self.save_result(task_id, result)
        return result

    async def _trend(self, task_id: str, params: dict) -> dict:
        season = params.get("season", "spring")
        trend = await self.invoke_skill("趋势分析", season=season)

        result = {
            "success": True,
            "agent": self.name,
            "analysis_type": "trend",
            "trend_data": trend,
        }
        await self.save_result(task_id, result)
        return result

    async def _competitor(self, task_id: str, article_id: str) -> dict:
        comp = await self.invoke_skill("竞品分析", article_id=article_id)

        result = {
            "success": True,
            "agent": self.name,
            "analysis_type": "competitor",
            "article_id": article_id,
            "competitor_data": comp,
        }
        await self.save_result(task_id, result)
        return result
