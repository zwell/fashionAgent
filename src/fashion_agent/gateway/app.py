"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from fashion_agent.core.config import get_settings
from fashion_agent.core.logging import get_logger, setup_logging
from fashion_agent.gateway.dependencies import get_master_agent, get_memory
from fashion_agent.gateway.routes.health import router as health_router
from fashion_agent.gateway.routes.skills import router as skills_router
from fashion_agent.gateway.routes.tasks import router as tasks_router
from fashion_agent.memory.manager import MemoryManager
from fashion_agent.skills.loader import register_all_skills

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

    # Pre-warm the master agent
    get_master_agent()
    logger.info("master_agent_ready")

    yield

    await memory.shutdown()
    logger.info("fashion_agent_stopped")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="FashionAgent API",
        description="Fashion e-commerce multi-agent system powered by LangGraph",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(health_router, tags=["health"])
    app.include_router(tasks_router, prefix="/api/v1", tags=["tasks"])
    app.include_router(skills_router, prefix="/api/v1", tags=["skills"])

    return app


app = create_app()
