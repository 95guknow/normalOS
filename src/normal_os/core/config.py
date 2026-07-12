"""
Central Configuration for normalOS

Deepened configuration system that covers all layers
(LLM, Connectors, Executor, Persistence, Bridge etc.).
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class LLMConfig(BaseModel):
    default_provider: str = "openai"
    timeout: int = 60
    max_retries: int = 3
    structured_output_repair: bool = True


class ConnectorConfig(BaseModel):
    enabled: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3
    auto_connect_on_start: bool = True


class ExecutorConfig(BaseModel):
    max_workers: int = 8
    max_memory_mb: int = 2048
    default_timeout: int = 300
    enable_cancellation: bool = True


class PersistenceConfig(BaseModel):
    db_path: str = "./data/normalos.db"
    enable_faden_store: bool = True
    enable_context_store: bool = True


class BridgeConfig(BaseModel):
    enabled: bool = True
    default_url: str = "http://127.0.0.1:8765"
    auto_reconnect: bool = True


class NormalOSConfig(BaseModel):
    """Root configuration for the entire system."""
    app_name: str = "normalOS"
    environment: str = "development"
    llm: LLMConfig = Field(default_factory=LLMConfig)
    connectors: ConnectorConfig = Field(default_factory=ConnectorConfig)
    executor: ExecutorConfig = Field(default_factory=ExecutorConfig)
    persistence: PersistenceConfig = Field(default_factory=PersistenceConfig)
    bridge: BridgeConfig = Field(default_factory=BridgeConfig)
    extra: Dict[str, Any] = Field(default_factory=dict)


# Globale Singleton-Instanz — wird von CLI und Dashboard importiert
settings = NormalOSConfig()
