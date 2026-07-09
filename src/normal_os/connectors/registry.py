"""
ConnectorRegistry for normalOS

Central registry for all external connectors.
Allows the Orchestrator and Agents to discover and use
GitHub, Google Drive, Notion, Gmail, Calendar, Bridge etc.
in a uniform way.

This is the explicit anchoring of all available Grok connectors
into the normalOS architecture.
"""

from typing import Dict, Type, Optional
from .base import BaseConnector, ConnectorConfig
from .github_connector import GitHubConnector
from .google_drive_connector import GoogleDriveConnector
from .notion_connector import NotionConnector


class ConnectorRegistry:
    """Registry holding all active connectors."""

    def __init__(self):
        self._connectors: Dict[str, BaseConnector] = {}
        self._register_defaults()

    def _register_defaults(self):
        """Register the core set of connectors autonomously."""
        self.register("github", GitHubConnector())
        self.register("google_drive", GoogleDriveConnector())
        self.register("notion", NotionConnector())
        # More connectors will be added autonomously (Gmail, Calendar, Bridge, etc.)

    def register(self, name: str, connector: BaseConnector):
        self._connectors[name.lower()] = connector

    def get(self, name: str) -> Optional[BaseConnector]:
        return self._connectors.get(name.lower())

    def list_connectors(self) -> list[str]:
        return list(self._connectors.keys())

    async def connect_all(self):
        results = {}
        for name, conn in self._connectors.items():
            if conn.is_enabled():
                results[name] = await conn.connect()
        return results
