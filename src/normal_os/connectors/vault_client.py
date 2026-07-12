"""
VaultClient — Client für den zentralen Fusion-Hero-OS Secrets-Broker (Supabase).

Prinzip: Agenten sehen nie Rohsecrets aus einer Konfigdatei. Jeder Bedarf
löst eine Anfrage an die `request_credential`-RPC aus, die Agent-Token +
Grant serverseitig prüft und eine kurzlebige Lease zurückgibt. Leases werden
nur im Prozessspeicher gehalten (nie auf Platte geschrieben) und kurz vor
Ablauf automatisch erneuert.

Konfiguration ausschließlich über Umgebungsvariablen (siehe
~/.fusion_agent_credentials auf jedem Node):
  FUSION_VAULT_URL, FUSION_AGENT_ID, FUSION_AGENT_TOKEN
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

import httpx

# Publishable Key ist bewusst kein Geheimnis: RLS sperrt jeden Tabellenzugriff,
# einzig request_credential() ist aufrufbar und prüft Agent-Token + Grant selbst.
_DEFAULT_PUBLISHABLE_KEY = "sb_publishable_Ckz8bhAXdoqA8siyA5bF5A_oq0xUPol"


class VaultAuthError(Exception):
    """Agent-Identität/Token vom Broker abgelehnt."""


class VaultGrantError(Exception):
    """Agent ist authentifiziert, hat aber keinen gültigen Grant für den Service."""


@dataclass
class _Lease:
    secret_value: str
    expires_at: float  # unix timestamp


class VaultClient:
    def __init__(
        self,
        vault_url: Optional[str] = None,
        agent_id: Optional[str] = None,
        agent_token: Optional[str] = None,
        publishable_key: Optional[str] = None,
    ):
        self.vault_url = (vault_url or os.environ.get("FUSION_VAULT_URL", "")).rstrip("/")
        self.agent_id = agent_id or os.environ.get("FUSION_AGENT_ID")
        self.agent_token = agent_token or os.environ.get("FUSION_AGENT_TOKEN")
        self.publishable_key = (
            publishable_key
            or os.environ.get("FUSION_VAULT_PUBLISHABLE_KEY")
            or _DEFAULT_PUBLISHABLE_KEY
        )
        self._cache: Dict[str, _Lease] = {}

    def is_configured(self) -> bool:
        return bool(self.vault_url and self.agent_id and self.agent_token)

    async def get_credential(
        self, service_key: str, lease_minutes: int = 15, force_refresh: bool = False
    ) -> str:
        """Liefert das aktuelle Secret für service_key. Verwendet eine gecachte
        Lease bis 30s vor Ablauf, danach automatischer Refresh gegen den Broker."""
        cached = self._cache.get(service_key)
        if not force_refresh and cached and cached.expires_at - 30 > time.time():
            return cached.secret_value

        if not self.is_configured():
            raise VaultAuthError(
                "Vault nicht konfiguriert — FUSION_VAULT_URL/FUSION_AGENT_ID/"
                "FUSION_AGENT_TOKEN fehlen (siehe ~/.fusion_agent_credentials)"
            )

        url = f"{self.vault_url}/rest/v1/rpc/request_credential"
        headers = {
            "apikey": self.publishable_key,
            "Authorization": f"Bearer {self.publishable_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "p_agent_id": self.agent_id,
            "p_agent_token": self.agent_token,
            "p_service_key": service_key,
            "p_lease_minutes": lease_minutes,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=payload)

        if resp.status_code != 200:
            detail = resp.text
            if "nicht autorisiert" in detail:
                raise VaultAuthError(f"Agent-Token ungültig für '{self.agent_id}'")
            if "kein gueltiger Grant" in detail or "kein gültiger Grant" in detail:
                raise VaultGrantError(f"'{self.agent_id}' hat keinen Grant für '{service_key}'")
            if "kein Secret" in detail:
                raise VaultGrantError(f"Für '{service_key}' ist noch kein Secret hinterlegt")
            raise RuntimeError(f"Vault-Anfrage fehlgeschlagen ({resp.status_code}): {detail}")

        rows = resp.json()
        if not rows:
            raise VaultGrantError(f"Leere Antwort für '{service_key}'")
        row = rows[0]
        lease = _Lease(
            secret_value=row["secret_value"],
            expires_at=_parse_iso(row["lease_expires_at"]),
        )
        self._cache[service_key] = lease
        return lease.secret_value

    def forget(self, service_key: Optional[str] = None) -> None:
        """Verwirft gecachte Lease(s) sofort (z.B. bei Verdacht auf Kompromittierung)."""
        if service_key is None:
            self._cache.clear()
        else:
            self._cache.pop(service_key, None)


def _parse_iso(ts: str) -> float:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()


_default_client: Optional[VaultClient] = None


def get_default_vault_client() -> VaultClient:
    global _default_client
    if _default_client is None:
        _default_client = VaultClient()
    return _default_client
