"""Base Agent class and simple registry.

Clean, extensible agent system.
"""
from abc import ABC, abstractmethod
from typing import Any

from ..core.models import Task


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    name: str = "base"
    description: str = "Base agent"

    @abstractmethod
    async def run(self, task: Task, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute the task. Must be implemented by subclasses."""
        pass


class AgentRegistry:
    """Simple in-memory agent registry."""

    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent):
        self._agents[agent.name] = agent

    def get(self, name: str) -> BaseAgent | None:
        return self._agents.get(name)

    def list_agents(self) -> list[str]:
        return list(self._agents.keys())


# Global registry instance
registry = AgentRegistry()