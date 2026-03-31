"""Task submission and query endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from fashion_agent.core.models import TaskRequest, TaskType
from fashion_agent.gateway.dependencies import get_master_agent

router = APIRouter()


@router.post("/tasks")
async def submit_task(request: TaskRequest):
    """Submit a new task to the Master Agent for orchestration."""
    master = get_master_agent()

    result = await master.run(
        task_type=request.task_type.value,
        instruction=request.instruction,
        params=request.params,
    )

    return result


@router.post("/tasks/copywriting")
async def generate_copy(article_id: str, style: str = "product_description"):
    """Quick endpoint: generate copy for a product."""
    master = get_master_agent()
    return await master.run(
        task_type=TaskType.COPYWRITING.value,
        instruction=f"Generate {style} copy for article {article_id}",
        params={"article_id": article_id, "preferred_style": style},
    )


@router.post("/tasks/restock")
async def check_restock(article_id: str, forecast_days: int = 30):
    """Quick endpoint: get restock recommendation."""
    master = get_master_agent()
    return await master.run(
        task_type=TaskType.RESTOCK.value,
        instruction=f"Restock analysis for article {article_id}",
        params={"article_id": article_id, "forecast_days": forecast_days},
    )


@router.post("/tasks/clearance")
async def check_clearance(article_id: str):
    """Quick endpoint: get clearance decision."""
    master = get_master_agent()
    return await master.run(
        task_type=TaskType.CLEARANCE.value,
        instruction=f"Clearance analysis for article {article_id}",
        params={"article_id": article_id},
    )


@router.post("/tasks/trend")
async def analyze_trend(season: str = "spring"):
    """Quick endpoint: get trend analysis for a season."""
    master = get_master_agent()
    return await master.run(
        task_type=TaskType.TREND_ANALYSIS.value,
        instruction=f"Trend analysis for {season}",
        params={"season": season},
    )


@router.post("/tasks/launch")
async def launch_product(article_id: str, season: str = "spring"):
    """Quick endpoint: new product launch workflow."""
    master = get_master_agent()
    return await master.run(
        task_type=TaskType.NEW_PRODUCT_LAUNCH.value,
        instruction=f"Launch product {article_id} for {season}",
        params={"article_id": article_id, "season": season},
    )
