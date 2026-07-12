"""
GitHub Connector for normalOS

Referenzimplementierung des Vault-Broker-Musters: kein Secret aus os.environ,
kein Caching im Connector selbst. Jede execute()-Anfrage holt sich (ueber den
Vault-Client mit eigenem Lease-Cache) frisch ein kurzlebiges Credential; ist
keins verfuegbar (kein Grant, Vault nicht konfiguriert, Token abgelaufen),
bleibt der Connector im DRY-RUN — es findet garantiert kein echter API-Call
statt.
"""

from typing import Any, Dict, Optional

import httpx

from .base import BaseConnector, ConnectorConfig, ConnectorResult


class GitHubConnector(BaseConnector):
    """Connector fuer GitHub-Operationen, Credential kommt aus dem Vault."""

    service_key = "github"

    def __init__(self, config: Optional[ConnectorConfig] = None):
        super().__init__(config)
        self.name = "GitHubConnector"

    async def connect(self) -> ConnectorResult:
        token = await self.require_credential()
        self._connected = token is not None
        return ConnectorResult(
            success=True,
            data={"status": "connected" if token else "dry_run", "service": "github"},
            metadata={"connector": self.name, "has_credential": token is not None},
        )

    async def disconnect(self) -> ConnectorResult:
        self._connected = False
        return ConnectorResult(success=True, data={"status": "disconnected"})

    async def execute(self, action: str, params: Dict[str, Any]) -> ConnectorResult:
        """
        Unterstuetzte Aktionen (werden erweitert):
        - list_repos
        - get_repo_tree
        - get_file_contents
        """
        action = action.lower()
        token = await self.require_credential()

        if token is None:
            return self.dry_run_result(
                action, params,
                reason="Kein Vault-Grant/Credential fuer 'github' verfuegbar",
                connector_name=self.name,
            )

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                if action == "list_repos":
                    resp = await client.get("https://api.github.com/user/repos", headers=headers)
                elif action == "get_repo_tree":
                    owner, repo = params["owner"], params["repo"]
                    ref = params.get("ref", "HEAD")
                    resp = await client.get(
                        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}",
                        headers=headers, params={"recursive": params.get("recursive", "1")},
                    )
                elif action == "get_file_contents":
                    owner, repo, path = params["owner"], params["repo"], params["path"]
                    resp = await client.get(
                        f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
                        headers=headers,
                    )
                else:
                    return ConnectorResult(success=False, error=f"Unbekannte Aktion: {action}")

            if resp.status_code >= 400:
                return ConnectorResult(success=False, error=f"GitHub API {resp.status_code}: {resp.text}")
            return ConnectorResult(success=True, data=resp.json(), metadata={"connector": self.name})
        except Exception as e:  # noqa: BLE001
            return ConnectorResult(success=False, error=str(e))
