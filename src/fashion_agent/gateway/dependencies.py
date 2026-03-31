"""Shared dependency singletons for the gateway layer."""

from __future__ import annotations

from functools import lru_cache

from fashion_agent.memory.manager import MemoryManager
from fashion_agent.orchestrator.master_agent import MasterAgent
from fashion_agent.skills.registry import get_registry


@lru_cache
def get_memory() -> MemoryManager:
    return MemoryManager()


@lru_cache
def get_master_agent() -> MasterAgent:
    return MasterAgent(
        skill_registry=get_registry(),
        memory=get_memory(),
    )
