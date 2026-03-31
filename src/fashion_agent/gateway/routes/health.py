"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from fashion_agent import __version__
from fashion_agent.skills.registry import get_registry

router = APIRouter()


@router.get("/health")
async def health_check():
    registry = get_registry()
    return {
        "status": "healthy",
        "version": __version__,
        "skills_registered": len(registry.list_skills()),
    }
