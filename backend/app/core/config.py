from __future__ import annotations

import json
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


Capability = Literal["monitor", "channel-control", "audit", "collector", "hrd"]
Environment = Literal["production", "quality", "development", "sandbox"]


class PoServer(BaseModel):
    sid: str = Field(pattern=r"^[A-Z][A-Z0-9]{1,7}$")
    display_name: str = Field(min_length=1, max_length=100)
    environment: Environment
    base_url: str
    port: int = Field(default=50000, ge=1, le=65535)
    enabled: bool = True
    capabilities: list[Capability] = Field(default_factory=lambda: ["monitor"])

    @field_validator("sid", mode="before")
    @classmethod
    def normalize_sid(cls, value: str) -> str:
        return value.upper()

    def public_view(self) -> dict:
        return {
            "sid": self.sid,
            "display_name": self.display_name,
            "environment": self.environment,
            "enabled": self.enabled,
            "capabilities": self.capabilities,
        }


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "PO Monitor Main"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    demo_mode: bool = True
    secret_key: str = "change-me-before-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 480
    cors_origins_raw: str = "http://localhost:3000"

    database_url: str = "postgresql+psycopg://po_monitor:change-me@localhost:5432/po_monitor"
    database_connect_on_startup: bool = False

    po_servers_json: str = "[]"
    sap_po_user: str = ""
    sap_po_password: str = ""
    sap_verify_tls: bool = True

    demo_admin_username: str = "admin"
    demo_admin_password: str = "demo1234"

    @property
    def cors_origins(self) -> list[str]:
        return [value.strip() for value in self.cors_origins_raw.split(",") if value.strip()]

    @property
    def po_servers(self) -> list[PoServer]:
        raw = json.loads(self.po_servers_json or "[]")
        servers = [PoServer.model_validate(item) for item in raw]
        seen: set[str] = set()
        for server in servers:
            if server.sid in seen:
                raise ValueError(f"PO_SERVERS_JSON duplicate sid: {server.sid}")
            seen.add(server.sid)
        return servers


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
