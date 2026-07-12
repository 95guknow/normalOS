"""
BaseConnector - Deepened version

Added connection state tracking, better error contracts,
and standardized metadata.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from .vault_client import VaultClient, VaultAuthError, VaultGrantError, get_default_vault_client


class ConnectorConfig(BaseModel):
    enabled: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3
    log_level: str = "INFO"
    auto_connect: bool = True


class ConnectorResult(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    connector_name: Optional[str] = None


class BaseConnector(ABC):
    """Deep base class for all connectors.

    DRY-RUN-Prinzip (uebernommen aus methodology/connectors.py): ein Connector
    darf NIE eine echte Aussenwirkung haben, solange kein echtes Credential
    ueber den Vault beschafft wurde. `require_credential()` ist der einzige
    vorgesehene Weg dahin — Connectoren duerfen Secrets nicht aus os.environ
    lesen oder sonstwie selbst cachen.
    """

    #: Service-Key im Vault-Katalog (public.services.service_key), z.B. "github".
    #: None = Connector braucht kein Secret (z.B. rein lokale Bridge mit eigenem Auth).
    service_key: Optional[str] = None

    def __init__(self, config: Optional[ConnectorConfig] = None, vault: Optional[VaultClient] = None):
        self.config = config or ConnectorConfig()
        self.name = self.__class__.__name__
        self._connected = False
        self._vault = vault or get_default_vault_client()

    @abstractmethod
    async def connect(self) -> ConnectorResult:
        pass

    @abstractmethod
    async def disconnect(self) -> ConnectorResult:
        pass

    @abstractmethod
    async def execute(self, action: str, params: Dict[str, Any]) -> ConnectorResult:
        pass

    def is_connected(self) -> bool:
        return self._connected

    def is_enabled(self) -> bool:
        return self.config.enabled

    async def require_credential(self) -> Optional[str]:
        """Fordert das Secret fuer self.service_key ueber den Vault an.

        Gibt bei Erfolg den Wert zurueck. Gibt None zurueck (statt zu werfen),
        wenn kein Vault konfiguriert ist, kein Grant existiert oder kein
        Secret hinterlegt ist — der Connector MUSS in diesem Fall im
        DRY-RUN-Modus bleiben (siehe dry_run_result()), niemals versuchen,
        trotzdem eine echte Anfrage zu stellen.
        """
        if not self.service_key:
            return None
        try:
            return await self._vault.get_credential(self.service_key)
        except (VaultAuthError, VaultGrantError):
            return None

    @staticmethod
    def dry_run_result(action: str, params: Dict[str, Any], reason: str, connector_name: str) -> "ConnectorResult":
        """Einheitliches DRY-RUN-Ergebnis, wenn kein echtes Credential vorliegt."""
        return ConnectorResult(
            success=True,
            data={
                "would_execute": False,
                "available": False,
                "action": action,
                "params": params,
                "reason": reason,
            },
            metadata={"connector": connector_name, "dry_run": True},
        )
