"""LangGraph state definition for the Master Agent orchestrator."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """Global state shared across all nodes in the orchestration graph."""

    task_id: str
    task_type: str
    instruction: str
    params: dict[str, Any]

    # Routing
    current_agent: str
    next_agents: list[str]

    # Results from each agent
    agent_results: Annotated[list[dict], lambda a, b: a + b]

    # Human review
    review_status: Literal["pending", "approved", "rejected", "not_required"]
    review_feedback: str

    # Final output
    status: Literal["running", "waiting_review", "completed", "failed"]
    final_result: dict[str, Any]

    # Message history (for LangGraph compatibility)
    messages: Annotated[list, add_messages]
