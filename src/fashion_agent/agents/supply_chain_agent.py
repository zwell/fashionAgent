"""SupplyChain Agent — inventory management, restock decisions, logistics.

Reasoning paradigm: ReAct — observe inventory state, reason about actions,
execute restock or clearance workflows.
"""

from __future__ import annotations

from fashion_agent.agents.base import BaseAgent


class SupplyChainAgent(BaseAgent):
    name = "supply_chain_agent"
    description = "供应链管理：库存管理、补货建议、物流追踪"

    async def execute(self, task_id: str, instruction: str, params: dict) -> dict:
        article_id = params.get("article_id")
        action = params.get("action", "check")

        self.logger.info(
            "supply_chain_task_start",
            task_id=task_id,
            article_id=article_id,
            action=action,
        )

        if action == "restock" and article_id:
            return await self._handle_restock(task_id, article_id, params)
        elif action == "clearance" and article_id:
            return await self._handle_clearance(task_id, article_id)
        elif action == "check" and article_id:
            return await self._handle_inventory_check(task_id, article_id)
        else:
            return {"success": False, "error": f"Unknown action '{action}' or missing article_id"}

    async def _handle_restock(self, task_id: str, article_id: str, params: dict) -> dict:
        # ReAct: Observe → Think → Act
        # Observe: check current inventory
        inventory = await self.invoke_skill("查询库存", article_id=article_id)
        self.logger.info("react_observe", step="inventory_checked", result=inventory.get("any_low_stock"))

        # Think: get restock recommendation
        restock = await self.invoke_skill(
            "智能补货",
            article_id=article_id,
            forecast_days=params.get("forecast_days", 30),
        )
        self.logger.info("react_think", step="restock_analyzed", should_reorder=restock.get("recommendation", {}).get("should_reorder"))

        result = {
            "success": True,
            "agent": self.name,
            "action": "restock",
            "article_id": article_id,
            "inventory_status": inventory,
            "restock_recommendation": restock.get("recommendation", {}),
            "reasoning": (
                f"ReAct approach: Observed inventory ({inventory.get('total_quantity', 0)} units), "
                f"analyzed forecast, generated restock recommendation."
            ),
        }
        await self.save_result(task_id, result)
        return result

    async def _handle_clearance(self, task_id: str, article_id: str) -> dict:
        clearance = await self.invoke_skill("清仓决策", article_id=article_id)

        result = {
            "success": True,
            "agent": self.name,
            "action": "clearance",
            "article_id": article_id,
            "clearance_decision": clearance,
            "reasoning": (
                f"ReAct approach: Analyzed inventory, competitor prices, and sales forecast. "
                f"Strategy: {clearance.get('strategy', 'unknown')}."
            ),
        }
        await self.save_result(task_id, result)
        return result

    async def _handle_inventory_check(self, task_id: str, article_id: str) -> dict:
        inventory = await self.invoke_skill("查询库存", article_id=article_id)

        result = {
            "success": True,
            "agent": self.name,
            "action": "check",
            "article_id": article_id,
            "inventory": inventory,
        }
        await self.save_result(task_id, result)
        return result
