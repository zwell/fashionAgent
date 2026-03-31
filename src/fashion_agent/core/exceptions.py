from __future__ import annotations


class FashionAgentError(Exception):
    """Base exception for FashionAgent."""


class SkillNotFoundError(FashionAgentError):
    """Raised when a requested skill is not found in the registry."""

    def __init__(self, skill_name: str):
        self.skill_name = skill_name
        super().__init__(f"Skill not found: {skill_name}")


class SkillExecutionError(FashionAgentError):
    """Raised when a skill execution fails."""

    def __init__(self, skill_name: str, reason: str):
        self.skill_name = skill_name
        self.reason = reason
        super().__init__(f"Skill '{skill_name}' failed: {reason}")


class AgentError(FashionAgentError):
    """Raised when an agent encounters an error."""

    def __init__(self, agent_name: str, reason: str):
        self.agent_name = agent_name
        self.reason = reason
        super().__init__(f"Agent '{agent_name}' error: {reason}")


class MemoryError(FashionAgentError):
    """Raised when a memory operation fails."""

    def __init__(self, layer: str, reason: str):
        self.layer = layer
        self.reason = reason
        super().__init__(f"Memory layer '{layer}' error: {reason}")


class TaskError(FashionAgentError):
    """Raised when task orchestration fails."""

    def __init__(self, task_id: str, reason: str):
        self.task_id = task_id
        self.reason = reason
        super().__init__(f"Task '{task_id}' error: {reason}")
