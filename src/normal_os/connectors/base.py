"""
Base Connector Abstraction for normalOS

All external connectors (GitHub, Google Drive, Notion, Gmail, etc.)
are built on this explicit interface so the Orchestrator and Agents
can use them uniformly and autonomously.

This is the clean, normalized extraction of connector patterns
previously implicit across heroic modules.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ConnectorConfig(BaseModel):
    """Base configuration for any connector."""
    enabled: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3
    log_level: str = "INFO"


class ConnectorResult(BaseModel):
    """Standard result wrapper for all connector operations."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class BaseConnector(ABC):
    """Abstract base for all external service connectors."""

    def __init__(self, config: Optional[ConnectorConfig] = None):
        self.config = config or ConnectorConfig()
        self.name = self.__class__.__name__

    @abstractmethod
    async def connect(self) -> ConnectorResult:
        """Establish connection / validate credentials."""
        pass

    @abstractmethod
    async def disconnect(self) -> ConnectorResult:
        """Cleanly close connection."""
        pass

    @abstractmethod
    async def execute(self, action: str, params: Dict[str, Any]) -> ConnectorResult:
        """Execute a named action on the connected service."""
        pass

    def is_enabled(self) -> bool:
        return self.config.enabled
