"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from fashion_agent.core.data_loader import load_articles, load_suppliers
from fashion_agent.core.logging import get_logger, setup_logging
from fashion_agent.gateway.dependencies import (
    get_entity_memory,
    get_master_agent,
    get_memory,
)
from fashion_agent.gateway.middleware.error_handler import ErrorHandlerMiddleware
from fashion_agent.gateway.middleware.rate_limit import RateLimitMiddleware
from fashion_agent.gateway.routes.data import router as data_router
from fashion_agent.gateway.routes.evaluation import router as eval_router
from fashion_agent.gateway.routes.health import router as health_router
from fashion_agent.gateway.routes.memory import router as memory_router
from fashion_agent.gateway.routes.skills import router as skills_router
from fashion_agent.gateway.routes.tasks import router as tasks_router
from fashion_agent.skills.loader import register_all_skills

STATIC_DIR = Path(__file__).resolve().parent / "static"

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("starting_fashion_agent")

    register_all_skills()
    logger.info("skills_registered")

    memory = get_memory()
    await memory.initialize()
    logger.info("memory_initialized")

    await _seed_memory(memory)
    logger.info("memory_seeded")

    get_master_agent()
    logger.info("master_agent_ready")

    yield

    await memory.shutdown()
    logger.info("fashion_agent_stopped")


async def _seed_memory(mm) -> None:
    """Populate vector store and knowledge graph from seed data on startup."""
    entity = get_entity_memory()
    articles = load_articles()
    suppliers = load_suppliers()

    for sup in suppliers:
        await mm.long_term.add_node(sup.supplier_id, "Supplier", {
            "name": sup.name,
            "region": sup.region,
            "specialties": sup.specialties,
        })

    for article in articles:
        await entity.build_sku_profile(article.article_id)


def create_app() -> FastAPI:
    app = FastAPI(
        title="FashionAgent API",
        description="Fashion e-commerce multi-agent system powered by LangGraph",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(RateLimitMiddleware, max_concurrent=20, requests_per_second=50)

    app.include_router(health_router, tags=["health"])
    app.include_router(tasks_router, prefix="/api/v1", tags=["tasks"])
    app.include_router(skills_router, prefix="/api/v1", tags=["skills"])
    app.include_router(data_router, prefix="/api/v1", tags=["data"])
    app.include_router(memory_router, prefix="/api/v1", tags=["memory"])
    app.include_router(eval_router, prefix="/api/v1", tags=["evaluation"])

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(str(STATIC_DIR / "index.html"))

    return app


app = create_app()
