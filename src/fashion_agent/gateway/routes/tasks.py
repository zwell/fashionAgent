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
    return await master.run(
        task_type=request.task_type.value,
        instruction=request.instruction,
        params=request.params,
    )


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
async def launch_product(
    article_id: str,
    season: str = "spring",
    category: str = "Dress",
):
    """New Product Launch SOP workflow.

    Runs Design Agent → [Visual + Marketing in parallel] → Review → Aggregate.
    """
    master = get_master_agent()
    return await master.run(
        task_type=TaskType.NEW_PRODUCT_LAUNCH.value,
        instruction=f"Launch product {article_id} for {season}",
        params={
            "article_id": article_id,
            "season": season,
            "category": category,
        },
    )


@router.post("/tasks/design")
async def design_product(
    category: str = "Dress",
    season: str = "spring",
    article_id: str | None = None,
):
    """Quick endpoint: generate a design proposal via Design Agent."""
    master = get_master_agent()
    params: dict = {"category": category, "season": season}
    if article_id:
        params["article_id"] = article_id
    return await master.run(
        task_type=TaskType.DESIGN.value,
        instruction=f"Design a {category} for {season}",
        params=params,
    )


@router.post("/tasks/visual")
async def generate_visuals(
    article_id: str,
    image_style: str = "commercial",
):
    """Quick endpoint: generate product images via Visual Agent."""
    master = get_master_agent()
    return await master.run(
        task_type=TaskType.VISUAL.value,
        instruction=f"Generate visuals for {article_id}",
        params={"article_id": article_id, "image_style": image_style},
    )
