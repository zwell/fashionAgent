"""Master Agent — LangGraph-based orchestrator that routes tasks to sub-agents."""

from __future__ import annotations

import uuid
from typing import Any

from langgraph.graph import END, StateGraph

from fashion_agent.agents.base import BaseAgent
from fashion_agent.agents.data_agent import DataAgent
from fashion_agent.agents.marketing_agent import MarketingAgent
from fashion_agent.agents.supply_chain_agent import SupplyChainAgent
from fashion_agent.core.logging import get_logger
from fashion_agent.core.models import TaskStatus, TaskType
from fashion_agent.memory.manager import MemoryManager
from fashion_agent.orchestrator.state import AgentState
from fashion_agent.skills.registry import SkillRegistry

logger = get_logger(__name__)

# Maps task types to the agent(s) that should handle them
_TASK_ROUTING: dict[str, list[str]] = {
    TaskType.COPYWRITING: ["marketing_agent"],
    TaskType.INVENTORY_CHECK: ["supply_chain_agent"],
    TaskType.RESTOCK: ["supply_chain_agent"],
    TaskType.CLEARANCE: ["supply_chain_agent", "marketing_agent"],
    TaskType.TREND_ANALYSIS: ["data_agent"],
    TaskType.NEW_PRODUCT_LAUNCH: ["data_agent", "marketing_agent"],
    TaskType.GENERAL: ["data_agent"],
}


class MasterAgent:
    """Central orchestrator built on LangGraph's StateGraph."""

    def __init__(self, skill_registry: SkillRegistry, memory: MemoryManager) -> None:
        self.skill_registry = skill_registry
        self.memory = memory

        self._agents: dict[str, BaseAgent] = {
            "marketing_agent": MarketingAgent(skill_registry, memory),
            "supply_chain_agent": SupplyChainAgent(skill_registry, memory),
            "data_agent": DataAgent(skill_registry, memory),
        }

        self._graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(AgentState)

        graph.add_node("route", self._route_node)
        graph.add_node("execute_agents", self._execute_agents_node)
        graph.add_node("aggregate", self._aggregate_node)

        graph.set_entry_point("route")
        graph.add_edge("route", "execute_agents")
        graph.add_edge("execute_agents", "aggregate")
        graph.add_edge("aggregate", END)

        return graph.compile()

    async def _route_node(self, state: AgentState) -> dict[str, Any]:
        """Determine which agent(s) should handle this task."""
        task_type = state["task_type"]
        agents = _TASK_ROUTING.get(task_type, ["data_agent"])

        logger.info("routing_task", task_id=state["task_id"], task_type=task_type, agents=agents)

        return {
            "next_agents": agents,
            "status": "running",
            "messages": [{"role": "system", "content": f"Routing to agents: {agents}"}],
        }

    async def _execute_agents_node(self, state: AgentState) -> dict[str, Any]:
        """Execute the selected agent(s) sequentially."""
        results = []
        for agent_name in state["next_agents"]:
            agent = self._agents.get(agent_name)
            if agent is None:
                results.append({"agent": agent_name, "success": False, "error": "Agent not found"})
                continue

            logger.info("executing_agent", task_id=state["task_id"], agent=agent_name)

            params = dict(state.get("params", {}))
            if agent_name == "supply_chain_agent" and "action" not in params:
                task_type = state["task_type"]
                if task_type == TaskType.RESTOCK:
                    params["action"] = "restock"
                elif task_type == TaskType.CLEARANCE:
                    params["action"] = "clearance"
                else:
                    params["action"] = "check"

            if agent_name == "data_agent" and "analysis_type" not in params:
                task_type = state["task_type"]
                if task_type == TaskType.TREND_ANALYSIS:
                    params["analysis_type"] = "trend"
                elif task_type == TaskType.NEW_PRODUCT_LAUNCH:
                    params["analysis_type"] = "trend"
                else:
                    params["analysis_type"] = "forecast"

            try:
                result = await agent.execute(
                    task_id=state["task_id"],
                    instruction=state["instruction"],
                    params=params,
                )
                results.append(result)
            except Exception as e:
                logger.error("agent_execution_failed", agent=agent_name, error=str(e))
                results.append({"agent": agent_name, "success": False, "error": str(e)})

        return {"agent_results": results}

    async def _aggregate_node(self, state: AgentState) -> dict[str, Any]:
        """Combine results from all agents into a final output."""
        results = state.get("agent_results", [])
        all_success = all(r.get("success", False) for r in results)

        final = {
            "task_id": state["task_id"],
            "task_type": state["task_type"],
            "agents_involved": state.get("next_agents", []),
            "all_success": all_success,
            "results": results,
        }

        logger.info("task_completed", task_id=state["task_id"], success=all_success)

        return {
            "status": "completed" if all_success else "failed",
            "final_result": final,
            "messages": [{"role": "assistant", "content": f"Task completed. Success: {all_success}"}],
        }

    async def run(
        self,
        task_type: str,
        instruction: str,
        params: dict | None = None,
    ) -> dict[str, Any]:
        """Submit a task and run it through the orchestration graph."""
        task_id = str(uuid.uuid4())[:8]

        initial_state: AgentState = {
            "task_id": task_id,
            "task_type": task_type,
            "instruction": instruction,
            "params": params or {},
            "current_agent": "",
            "next_agents": [],
            "agent_results": [],
            "review_status": "not_required",
            "review_feedback": "",
            "status": "running",
            "final_result": {},
            "messages": [],
        }

        await self.memory.save_task_context(task_id, {
            "task_type": task_type,
            "instruction": instruction,
            "params": params or {},
            "status": TaskStatus.RUNNING,
        })

        result = await self._graph.ainvoke(initial_state)

        await self.memory.save_task_context(task_id, {
            "task_type": task_type,
            "instruction": instruction,
            "status": result.get("status", "completed"),
            "final_result": result.get("final_result", {}),
        })

        return {
            "task_id": task_id,
            "status": result.get("status", "completed"),
            **result.get("final_result", {}),
        }
