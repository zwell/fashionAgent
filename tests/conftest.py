"""Shared test fixtures."""

from __future__ import annotations

import pytest

from fashion_agent.memory.manager import MemoryManager
from fashion_agent.skills.loader import register_all_skills
from fashion_agent.skills.registry import SkillRegistry, get_registry


@pytest.fixture(autouse=True)
def _setup_skills():
    """Ensure all skills are registered before every test."""
    register_all_skills()


@pytest.fixture
def skill_registry() -> SkillRegistry:
    return get_registry()


@pytest.fixture
async def memory() -> MemoryManager:
    mm = MemoryManager()
    await mm.initialize()
    yield mm
    await mm.shutdown()
