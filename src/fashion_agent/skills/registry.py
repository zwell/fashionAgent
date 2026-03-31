"""Skill registry — central hub for discovering and invoking skills."""

from __future__ import annotations

from typing import Any

from fashion_agent.core.exceptions import SkillExecutionError, SkillNotFoundError
from fashion_agent.core.logging import get_logger
from fashion_agent.skills.base import SkillDescriptor

logger = get_logger(__name__)


class SkillRegistry:
    """Singleton registry that holds all registered skills."""

    def __init__(self) -> None:
        self._skills: dict[str, SkillDescriptor] = {}

    def register(self, descriptor: SkillDescriptor) -> None:
        self._skills[descriptor.name] = descriptor
        logger.info("skill_registered", name=descriptor.name, level=descriptor.level)

    def get(self, name: str) -> SkillDescriptor:
        if name not in self._skills:
            raise SkillNotFoundError(name)
        return self._skills[name]

    def list_skills(
        self, level: str | None = None, tag: str | None = None
    ) -> list[SkillDescriptor]:
        results = list(self._skills.values())
        if level:
            results = [s for s in results if s.level == level]
        if tag:
            results = [s for s in results if tag in s.tags]
        return results

    def search(self, query: str) -> list[SkillDescriptor]:
        """Simple keyword-based search across name, description, tags, and examples."""
        query_lower = query.lower()
        scored: list[tuple[int, SkillDescriptor]] = []
        for s in self._skills.values():
            score = 0
            if query_lower in s.name.lower():
                score += 10
            if query_lower in s.description.lower():
                score += 5
            for tag in s.tags:
                if query_lower in tag.lower():
                    score += 3
            for ex in s.examples:
                if query_lower in ex.lower():
                    score += 2
            if score > 0:
                scored.append((score, s))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored]

    async def invoke(self, name: str, **kwargs: Any) -> Any:
        descriptor = self.get(name)
        if descriptor.func is None:
            raise SkillExecutionError(name, "Skill has no callable function")
        try:
            if descriptor.is_async:
                return await descriptor.func(**kwargs)
            return descriptor.func(**kwargs)
        except Exception as e:
            raise SkillExecutionError(name, str(e)) from e

    def to_tool_schemas(self) -> list[dict]:
        return [s.to_tool_schema() for s in self._skills.values()]


_registry: SkillRegistry | None = None


def get_registry() -> SkillRegistry:
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry
