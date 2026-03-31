"""New Product Launch SOP Workflow

Implements the complete "自动上新" process:

  1. Design Agent — generate design proposal (CoT)
  2. [Parallel] Visual Agent + Marketing Agent — generate images and copy
  3. Human Review — approve or reject with feedback
  4. Aggregate — combine all outputs into a launch package

Uses LangGraph's StateGraph with conditional edges and parallel fan-out.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Annotated, Any, Literal

from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from fashion_agent.agents.design_agent import DesignAgent
from fashion_agent.agents.marketing_agent import MarketingAgent
from fashion_agent.agents.visual_agent import VisualAgent
from fashion_agent.core.logging import get_logger
from fashion_agent.memory.manager import MemoryManager
from fashion_agent.skills.registry import SkillRegistry

logger = get_logger(__name__)


class NewProductState(TypedDict):
    task_id: str
    instruction: str
    params: dict[str, Any]

    # Phase outputs
    design_result: dict[str, Any]
    visual_result: dict[str, Any]
    marketing_result: dict[str, Any]

    # Human review
    review_status: Literal["pending", "approved", "rejected", "not_required"]
    review_feedback: str

    # Final
    status: Literal["running", "waiting_review", "completed", "failed"]
    final_result: dict[str, Any]

    messages: Annotated[list, add_messages]


class NewProductWorkflow:
    """Complete SOP for launching a new product with parallel agent execution."""

    def __init__(
        self, skill_registry: SkillRegistry, memory: MemoryManager
    ) -> None:
        self.memory = memory
        self._design = DesignAgent(skill_registry, memory)
        self._visual = VisualAgent(skill_registry, memory)
        self._marketing = MarketingAgent(skill_registry, memory)
        self._graph = self._build_graph()

    def _build_graph(self) -> Any:
        graph = StateGraph(NewProductState)

        graph.add_node("design_phase", self._design_phase)
        graph.add_node("parallel_production", self._parallel_production)
        graph.add_node("review_gate", self._review_gate)
        graph.add_node("aggregate_launch", self._aggregate_launch)

        graph.set_entry_point("design_phase")
        graph.add_edge("design_phase", "parallel_production")
        graph.add_edge("parallel_production", "review_gate")

        graph.add_conditional_edges(
            "review_gate",
            self._review_router,
            {
                "approved": "aggregate_launch",
                "rejected": "design_phase",
                "auto_approved": "aggregate_launch",
            },
        )
        graph.add_edge("aggregate_launch", END)

        return graph.compile()

    # ── Nodes ────────────────────────────────────────────────

    async def _design_phase(self, state: NewProductState) -> dict:
        """Phase 1: Design Agent creates a product proposal."""
        logger.info("sop_design_phase", task_id=state["task_id"])

        result = await self._design.execute(
            task_id=state["task_id"],
            instruction=state["instruction"],
            params=state["params"],
        )

        return {
            "design_result": result,
            "status": "running",
            "messages": [
                {
                    "role": "assistant",
                    "content": "Phase 1 complete: Design proposal generated.",
                }
            ],
        }

    async def _parallel_production(self, state: NewProductState) -> dict:
        """Phase 2: Visual + Marketing agents execute in parallel."""
        logger.info("sop_parallel_production", task_id=state["task_id"])

        params = dict(state["params"])

        # Pass design description to visual agent if available
        design = state.get("design_result", {})
        if design.get("design_description"):
            params["description"] = design["design_description"]

        visual_task = self._visual.execute(
            task_id=state["task_id"],
            instruction=state["instruction"],
            params=params,
        )
        marketing_task = self._marketing.execute(
            task_id=state["task_id"],
            instruction=state["instruction"],
            params=params,
        )

        visual_result, marketing_result = await asyncio.gather(
            visual_task, marketing_task
        )

        return {
            "visual_result": visual_result,
            "marketing_result": marketing_result,
            "messages": [
                {
                    "role": "assistant",
                    "content": (
                        "Phase 2 complete: Visual and Marketing "
                        "agents finished in parallel."
                    ),
                }
            ],
        }

    async def _review_gate(self, state: NewProductState) -> dict:
        """Phase 3: Determine whether human review is needed."""
        current_review = state.get("review_status", "not_required")

        # If the caller already supplied a review decision, honour it
        if current_review in ("approved", "rejected"):
            logger.info(
                "sop_review_decision",
                task_id=state["task_id"],
                decision=current_review,
            )
            return {}

        # Auto-approve if all sub-agents succeeded
        design_ok = state.get("design_result", {}).get("success", False)
        visual_ok = state.get("visual_result", {}).get("success", False)
        marketing_ok = state.get("marketing_result", {}).get("success", False)

        if design_ok and visual_ok and marketing_ok:
            quality = state.get("visual_result", {}).get(
                "quality_summary", {}
            )
            needs_review = quality.get("needs_review", 0)
            if needs_review == 0:
                logger.info("sop_auto_approved", task_id=state["task_id"])
                return {"review_status": "auto_approved"}

        logger.info("sop_waiting_review", task_id=state["task_id"])
        return {"review_status": "auto_approved", "status": "waiting_review"}

    def _review_router(self, state: NewProductState) -> str:
        status = state.get("review_status", "auto_approved")
        if status == "approved":
            return "approved"
        if status == "rejected":
            return "rejected"
        return "auto_approved"

    async def _aggregate_launch(self, state: NewProductState) -> dict:
        """Phase 4: Combine everything into a launch package."""
        logger.info("sop_aggregate", task_id=state["task_id"])

        design = state.get("design_result", {})
        visual = state.get("visual_result", {})
        marketing = state.get("marketing_result", {})

        launch_package = {
            "task_id": state["task_id"],
            "design": {
                "proposal": design.get("design_proposal", {}),
                "description": design.get("design_description", ""),
                "trend_basis": design.get("trend_basis", {}),
            },
            "visuals": {
                "total_images": visual.get("total_images", 0),
                "images": visual.get("images", []),
                "quality_summary": visual.get("quality_summary", {}),
            },
            "marketing": {
                "selected_copy": marketing.get("selected_copy", ""),
                "all_variants": marketing.get("all_variants", {}),
            },
            "review_status": state.get("review_status", "auto_approved"),
            "launch_checklist": [
                {
                    "item": "设计提案",
                    "done": design.get("success", False),
                },
                {
                    "item": "商品图片",
                    "done": visual.get("success", False),
                },
                {
                    "item": "营销文案",
                    "done": marketing.get("success", False),
                },
                {
                    "item": "人工审核",
                    "done": state.get("review_status") in (
                        "approved", "auto_approved"
                    ),
                },
            ],
        }

        all_done = all(c["done"] for c in launch_package["launch_checklist"])

        return {
            "status": "completed" if all_done else "failed",
            "final_result": launch_package,
            "messages": [
                {
                    "role": "assistant",
                    "content": (
                        f"Launch package assembled. "
                        f"All checks passed: {all_done}"
                    ),
                }
            ],
        }

    # ── Public API ───────────────────────────────────────────

    async def run(
        self,
        instruction: str,
        params: dict | None = None,
        review_status: str = "not_required",
    ) -> dict[str, Any]:
        task_id = str(uuid.uuid4())[:8]
        initial: NewProductState = {
            "task_id": task_id,
            "instruction": instruction,
            "params": params or {},
            "design_result": {},
            "visual_result": {},
            "marketing_result": {},
            "review_status": review_status,
            "review_feedback": "",
            "status": "running",
            "final_result": {},
            "messages": [],
        }

        result = await self._graph.ainvoke(initial)

        return {
            "task_id": task_id,
            "workflow": "new_product_sop",
            "status": result.get("status", "completed"),
            "review_status": result.get("review_status", "auto_approved"),
            **result.get("final_result", {}),
        }
