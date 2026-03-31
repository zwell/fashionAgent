"""Base class for all sub-agents in the system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from fashion_agent.core.logging import get_logger
from fashion_agent.memory.manager import MemoryManager
from fashion_agent.skills.registry import SkillRegistry


class BaseAgent(ABC):
    """Every sub-agent inherits from this and gets access to skills + memory."""

    name: str = "base_agent"
    description: str = ""

    def __init__(self, skill_registry: SkillRegistry, memory: MemoryManager) -> None:
        self.skills = skill_registry
        self.memory = memory
        self.logger = get_logger(self.name)

    @abstractmethod
    async def execute(self, task_id: str, instruction: str, params: dict) -> dict:
        """Execute the agent's main task and return a result dict."""

    async def invoke_skill(self, skill_name: str, **kwargs: Any) -> Any:
        self.logger.info("invoking_skill", skill=skill_name, params=list(kwargs.keys()))
        result = await self.skills.invoke(skill_name, **kwargs)
        return result

    async def save_result(self, task_id: str, result: dict) -> None:
        await self.memory.log_agent_action(
            task_id=task_id,
            agent=self.name,
            action="execute",
            result=result,
        )
