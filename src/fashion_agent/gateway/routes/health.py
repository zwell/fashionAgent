"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from fashion_agent import __version__
from fashion_agent.gateway.dependencies import get_memory
from fashion_agent.skills.registry import get_registry

router = APIRouter()


@router.get("/health")
async def health_check():
    registry = get_registry()
    mm = get_memory()
    mem_stats = await mm.get_memory_stats()
    return {
        "status": "healthy",
        "version": __version__,
        "skills_registered": len(registry.list_skills()),
        "agents": 5,
        "memory": {
            "short_term": "redis" if mm.short_term._redis else "in-memory",
            "mid_term": mem_stats["mid_term"]["backend"],
            "long_term": mem_stats["long_term"]["backend"],
        },
    }
