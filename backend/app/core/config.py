from __future__ import annotations

import json
from urllib.parse import urlsplit, urlunsplit
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


Capability = Literal["monitor", "channel-control", "audit", "collector", "hrd"]
Environment = Literal["production", "quality", "development", "sandbox"]
SapPoEndpointName = Literal[
    "channels",
    "channel_admin",
    "adapter_monitor",
    "aae_monitor",
    "systatus",
    "business_system",
    "interface_monitor",
    "directory",
    "hrd_test",
    "keystore_help",
    "keystore_certificates",
]
CollectorSource = Literal["hana"]
CollectorDeliverySemantics = Literal["BE", "EO"]


class RtimsCollectorProfile(BaseModel):
    collector_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{1,31}$")
    oracle_instance_id: int = Field(gt=0)
    enabled: bool = True
    source: CollectorSource = "hana"
    delivery_semantics: CollectorDeliverySemantics = "BE"
    interval_seconds: int = Field(default=300, ge=30, le=86400)
    limit: int = Field(default=500, ge=100, le=5000)
    initial_lookback_seconds: int = Field(default=0, ge=0, le=86400)
    pending_search_minutes: int = Field(default=30, ge=2, le=1440)
    persist_duration_days: int = Field(default=30, ge=1, le=3650)
    multi_server_run_duration_days: int = Field(default=1, ge=1, le=365)
    hana_host: str = ""
    hana_port: int | None = Field(default=None, ge=1, le=65535)
    hana_user: str = ""
    hana_password: SecretStr = SecretStr("")
    po_db_schema: str = Field(
        default="",
        pattern=r"^$|^[A-Za-z][A-Za-z0-9_$#]{0,127}$",
    )
    host_id_table: str = Field(
        default="",
        pattern=r"^$|^[A-Za-z][A-Za-z0-9_$#]{0,127}$",
    )
    host_id_field: str = Field(
        default="",
        pattern=r"^$|^[A-Za-z][A-Za-z0-9_$#]{0,127}$",
    )

    @field_validator("collector_id", mode="before")
    @classmethod
    def normalize_collector_id(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("delivery_semantics", mode="before")
    @classmethod
    def normalize_delivery_semantics(cls, value: str) -> str:
        return value.strip().upper()

    @model_validator(mode="after")
    def validate_host_id_pair(self) -> "RtimsCollectorProfile":
        if bool(self.host_id_table) != bool(self.host_id_field):
            raise ValueError("host_id_table and host_id_field must be configured together")
        return self


class PoServer(BaseModel):
    sid: str = Field(pattern=r"^[A-Z][A-Z0-9]{1,7}$")
    display_name: str = Field(min_length=1, max_length=100)
    environment: Environment
    base_url: str
    port: int = Field(default=50000, ge=1, le=65535)
    username: str | None = None
    password: SecretStr | None = None
    endpoint_paths: dict[SapPoEndpointName, str] = Field(default_factory=dict)
    host_aliases: list[str] = Field(default_factory=list)
    collectors: list[RtimsCollectorProfile] = Field(default_factory=list)
    enabled: bool = True
    capabilities: list[Capability] = Field(default_factory=lambda: ["monitor"])

    @field_validator("sid", mode="before")
    @classmethod
    def normalize_sid(cls, value: str) -> str:
        return value.upper()

    @field_validator("endpoint_paths")
    @classmethod
    def validate_endpoint_paths(
        cls,
        value: dict[SapPoEndpointName, str],
    ) -> dict[SapPoEndpointName, str]:
        for name, path in value.items():
            if not path.startswith("/"):
                raise ValueError(f"{name} endpoint path must start with '/'")
        return value

    @field_validator("host_aliases")
    @classmethod
    def normalize_host_aliases(cls, value: list[str]) -> list[str]:
        aliases: list[str] = []
        for raw_alias in value:
            alias = raw_alias.strip().lower().rstrip(".")
            if (
                not alias
                or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789.-" for character in alias)
                or alias.startswith((".", "-"))
                or alias.endswith((".", "-"))
            ):
                raise ValueError("host aliases must be plain DNS hostnames")
            if alias not in aliases:
                aliases.append(alias)
        return aliases

    @field_validator("collectors")
    @classmethod
    def validate_collector_ids(
        cls,
        value: list[RtimsCollectorProfile],
    ) -> list[RtimsCollectorProfile]:
        ids = [profile.collector_id for profile in value]
        if len(ids) != len(set(ids)):
            raise ValueError("collector profile ids must be unique per server")
        return value

    def public_view(self) -> dict:
        return {
            "sid": self.sid,
            "display_name": self.display_name,
            "environment": self.environment,
            "enabled": self.enabled,
            "capabilities": self.capabilities,
        }

    def endpoint_path(self, name: SapPoEndpointName, fallback: str) -> str:
        return self.endpoint_paths.get(name, fallback)

    @property
    def origin(self) -> str:
        parsed = urlsplit(self.base_url.rstrip("/"))
        if not parsed.scheme or not parsed.hostname:
            raise ValueError(f"{self.sid} base_url must include scheme and hostname")
        host = parsed.hostname
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        netloc = f"{host}:{parsed.port or self.port}"
        return urlunsplit((parsed.scheme, netloc, parsed.path.rstrip("/"), "", ""))


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
    sap_po_live_mode: bool = False
    secret_key: str = "change-me-before-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 480
    cors_origins_raw: str = "http://localhost:3000"

    database_url: str = "postgresql+psycopg://po_monitor:change-me@localhost:5432/po_monitor"
    database_connect_on_startup: bool = False

    rtims_enabled: bool = False
    rtims_postgres_database_url: str = ""
    rtims_oracle_host: str = ""
    rtims_oracle_port: int = 1521
    rtims_oracle_service: str = ""
    rtims_oracle_schema: str = Field(
        default="",
        pattern=r"^$|^[A-Za-z][A-Za-z0-9_$#]{0,127}$",
    )
    rtims_oracle_user: str = ""
    rtims_oracle_password: SecretStr = SecretStr("")
    rtims_oracle_ddl_user: str = ""
    rtims_oracle_ddl_password: SecretStr = SecretStr("")
    rtims_pool_min: int = 1
    rtims_pool_max: int = 5
    rtims_collector_enabled: bool = False
    rtims_collector_startup_delay_seconds: int = Field(default=30, ge=0, le=3600)
    rtims_collector_interval_seconds: int = Field(default=300, ge=30, le=86400)
    rtims_collector_limit: int = Field(default=500, ge=100, le=5000)
    rtims_collector_oracle_user: str = ""
    rtims_collector_oracle_password: SecretStr = SecretStr("")

    po_servers_json: str = "[]"
    sap_po_user: str = ""
    sap_po_password: SecretStr = SecretStr("")
    sap_verify_tls: bool = True
    sap_connect_timeout_seconds: float = 10.0
    sap_read_timeout_seconds: float = 60.0
    sap_retry_count: int = 2
    sap_channel_wsdl_path: str = "/CommunicationChannelInService/CommunicationChannelInImplBean?wsdl"
    sap_channel_admin_wsdl_path: str = "/ChannelAdminService/ChannelAdmin?wsdl"
    sap_adapter_monitor_wsdl_path: str = "/AdapterMessageMonitoring/basic?wsdl"
    sap_aae_monitor_wsdl_path: str = "/AaeMessageMonitorService/AaeMessageMonitor?wsdl"
    sap_systatus_wsdl_path: str = "/SystatusService/Systatus?wsdl"
    sap_business_system_wsdl_path: str = "/BusinessSystemInService/BusinessSystemInImplBean?wsdl"
    sap_interface_monitor_wsdl_path: str = "/InterfaceMonitorService/InterfaceMonitor?wsdl"
    sap_directory_path: str = "/dir/read/ext"
    sap_hrd_channel_pattern: str = "JDBC4_Receiver_DIST_HRD*"
    sap_hrd_test_path: str = "/HttpAdapter/HttpMessageServlet"
    sap_keystore_help_path: str = "/KeystoreHelp/basic?style=document"
    sap_keystore_certificates_path: str = "/KeystoreService/KeystoreServiceApi"
    sap_keystore_max_response_bytes: int = Field(
        default=10_000_000,
        ge=100_000,
        le=100_000_000,
    )
    sap_hrd_test_interface: str = ""
    sap_hrd_sender_services_json: str = "{}"
    sap_hana_host: str = ""
    sap_hana_port: int = 30015
    sap_hana_user: str = ""
    sap_hana_password: SecretStr = SecretStr("")
    sap_aae_delivery_semantics: str = "BE"
    sap_aae_host_id_table: str = ""
    sap_aae_host_id_field: str = ""
    sap_message_lookback_minutes: int = 60
    sap_control_allowed_sids_raw: str = ""

    ifs_oracle_enabled: bool = False
    ifs_oracle_host: str = ""
    ifs_oracle_port: int = 1521
    ifs_oracle_service: str = ""
    ifs_oracle_user: str = ""
    ifs_oracle_password: SecretStr = SecretStr("")
    ifs_sync_scheduler_enabled: bool = False
    ifs_sync_interval_seconds: int = 3600

    llm_api_url: str = ""
    llm_api_timeout_seconds: float = Field(default=30.0, gt=0, le=300)

    demo_admin_username: str = "admin"
    demo_admin_password: str = "1234"

    @property
    def cors_origins(self) -> list[str]:
        return [value.strip() for value in self.cors_origins_raw.split(",") if value.strip()]

    @property
    def po_servers(self) -> list[PoServer]:
        raw = json.loads(self.po_servers_json or "[]")
        servers = [PoServer.model_validate(item) for item in raw]
        seen: set[str] = set()
        collector_instances: set[int] = set()
        for server in servers:
            if server.sid in seen:
                raise ValueError(f"PO_SERVERS_JSON duplicate sid: {server.sid}")
            seen.add(server.sid)
            for profile in server.collectors:
                if profile.oracle_instance_id in collector_instances:
                    raise ValueError(
                        "PO_SERVERS_JSON duplicate collector oracle_instance_id: "
                        f"{profile.oracle_instance_id}"
                    )
                collector_instances.add(profile.oracle_instance_id)
        return servers

    @property
    def sap_control_allowed_sids(self) -> set[str]:
        return {
            value.strip().upper()
            for value in self.sap_control_allowed_sids_raw.split(",")
            if value.strip()
        }

    @property
    def rtims_configured(self) -> bool:
        return bool(
            self.rtims_enabled
            and self.rtims_oracle_host
            and self.rtims_oracle_service
            and self.rtims_oracle_user
            and self.rtims_oracle_password.get_secret_value()
        )

    @property
    def rtims_postgres_setup_url(self) -> str:
        return self.rtims_postgres_database_url.strip() or self.database_url

    @property
    def rtims_oracle_ddl_configured(self) -> bool:
        return bool(
            self.rtims_oracle_host
            and self.rtims_oracle_service
            and self.rtims_oracle_ddl_user
            and self.rtims_oracle_ddl_password.get_secret_value()
        )

    @property
    def rtims_collector_oracle_username(self) -> str:
        return self.rtims_collector_oracle_user.strip() or self.rtims_oracle_user.strip()

    @property
    def rtims_collector_oracle_secret(self) -> str:
        collector_secret = self.rtims_collector_oracle_password.get_secret_value()
        return collector_secret or self.rtims_oracle_password.get_secret_value()

    @property
    def rtims_collector_oracle_configured(self) -> bool:
        return bool(
            self.rtims_oracle_host
            and self.rtims_oracle_service
            and self.rtims_collector_oracle_username
            and self.rtims_collector_oracle_secret
        )

    @property
    def sap_hana_configured(self) -> bool:
        return bool(
            self.sap_hana_host
            and self.sap_hana_user
            and self.sap_hana_password.get_secret_value()
        )

    @property
    def sap_hrd_sender_services(self) -> dict[str, str]:
        raw = json.loads(self.sap_hrd_sender_services_json or "{}")
        return {str(key).upper(): str(value) for key, value in raw.items()}

    @property
    def ifs_oracle_configured(self) -> bool:
        return bool(
            self.ifs_oracle_enabled
            and self.ifs_oracle_host
            and self.ifs_oracle_service
            and self.ifs_oracle_user
            and self.ifs_oracle_password.get_secret_value()
        )

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_url.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
