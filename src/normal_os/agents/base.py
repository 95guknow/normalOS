"""
BaseAgent for normalOS

All agents inherit from this. Now extended with optional
connector access so agents can autonomously use external services
(GitHub, Drive, Notion, PC-Bridge, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..connectors.registry import ConnectorRegistry


class BaseAgent(ABC):
    """Base class for all agents in normalOS."""

    def __init__(self, name: str, connector_registry: Optional[ConnectorRegistry] = None):
        self.name = name
        self.connector_registry = connector_registry or ConnectorRegistry()

    @abstractmethod
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's main logic."""
        pass

    def get_connector(self, name: str):
        """Convenience method for agents to access connectors."""
        return self.connector_registry.get(name)
