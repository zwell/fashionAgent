"""Skill registry query endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from fashion_agent.skills.registry import get_registry

router = APIRouter()


@router.get("/skills")
async def list_skills(level: str | None = None, tag: str | None = None):
    """List all registered skills, optionally filtered by level or tag."""
    registry = get_registry()
    skills = registry.list_skills(level=level, tag=tag)
    return {
        "total": len(skills),
        "skills": [s.to_tool_schema() for s in skills],
    }


@router.get("/skills/search")
async def search_skills(q: str):
    """Semantic search over skill names, descriptions, tags, and examples."""
    registry = get_registry()
    results = registry.search(q)
    return {
        "query": q,
        "total": len(results),
        "skills": [s.to_tool_schema() for s in results],
    }
