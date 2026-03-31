"""MCP-style skill base class and decorator for semantic skill registration."""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

from pydantic import BaseModel


class SkillInput(BaseModel):
    """Override in concrete skills to define typed inputs."""


class SkillOutput(BaseModel):
    """Override in concrete skills to define typed outputs."""
    success: bool = True
    data: dict = field(default_factory=dict) if False else {}  # noqa: kept for clarity
    message: str = ""


@dataclass
class SkillDescriptor:
    """Metadata for a registered skill, inspired by MCP tool descriptors."""

    name: str
    description: str
    tags: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    level: str = "L1"
    func: Callable[..., Coroutine[Any, Any, Any]] | None = None

    @property
    def is_async(self) -> bool:
        return self.func is not None and inspect.iscoroutinefunction(self.func)

    def to_tool_schema(self) -> dict:
        """Export as an MCP-compatible tool description."""
        return {
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "examples": self.examples,
            "level": self.level,
        }


def skill(
    name: str,
    description: str,
    tags: list[str] | None = None,
    examples: list[str] | None = None,
    level: str = "L1",
) -> Callable:
    """Decorator to register an async function as a semantic skill.

    Usage::

        @skill(
            name="查询库存",
            description="查询指定商品的当前库存",
            tags=["库存", "ERP"],
            examples=["查一下SKU12345的库存"],
        )
        async def erp_inventory_query(sku_id: str) -> dict:
            ...
    """

    def decorator(func: Callable) -> Callable:
        descriptor = SkillDescriptor(
            name=name,
            description=description,
            tags=tags or [],
            examples=examples or [],
            level=level,
            func=func,
        )
        func._skill_descriptor = descriptor  # type: ignore[attr-defined]
        return func

    return decorator
