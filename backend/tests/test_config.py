import json

from pydantic import SecretStr

from app.core.config import Settings
from app.integrations.sap_po.client import credentials, service_path


def test_server_registry_is_dynamic() -> None:
    settings = Settings(
        po_servers_json=json.dumps(
            [
                {
                    "sid": "PEQ",
                    "display_name": "Planning Quality",
                    "environment": "quality",
                    "base_url": "https://example.internal",
                    "capabilities": ["monitor", "collector"],
                }
            ]
        )
    )
    assert settings.po_servers[0].sid == "PEQ"
    assert settings.po_servers[0].origin == "https://example.internal:50000"
    assert settings.po_servers[0].public_view()["display_name"] == "Planning Quality"
    assert "base_url" not in settings.po_servers[0].public_view()


def test_server_specific_credentials_are_never_public() -> None:
    settings = Settings(
        po_servers_json=json.dumps(
            [
                {
                    "sid": "POQ",
                    "display_name": "Quality",
                    "environment": "quality",
                    "base_url": "http://po.example.internal",
                    "username": "technical-user",
                    "password": "not-public",
                }
            ]
        )
    )
    public = settings.po_servers[0].public_view()
    assert "username" not in public
    assert "password" not in public


def test_server_specific_connection_settings_override_common_values() -> None:
    configured = Settings(
        sap_po_user="common-user",
        sap_po_password="common-password",
        po_servers_json=json.dumps(
            [
                {
                    "sid": "PMP",
                    "display_name": "Production",
                    "environment": "production",
                    "base_url": "https://pmp.example.internal",
                    "port": 60000,
                    "username": "pmp-user",
                    "password": "pmp-password",
                    "endpoint_paths": {
                        "channels": "/custom/CommunicationChannel?wsdl",
                        "directory": "/custom/dir/read/ext",
                    },
                }
            ]
        ),
    )
    server = configured.po_servers[0]

    assert server.origin == "https://pmp.example.internal:60000"
    assert credentials(server) == ("pmp-user", "pmp-password")
    assert service_path("channels", server) == "/custom/CommunicationChannel?wsdl"
    assert server.endpoint_path("directory", "/dir/read/ext") == "/custom/dir/read/ext"
    assert "endpoint_paths" not in server.public_view()


def test_empty_server_password_falls_back_to_common_password(monkeypatch) -> None:
    configured = Settings(
        po_servers_json=json.dumps(
            [
                {
                    "sid": "POQ",
                    "display_name": "Quality",
                    "environment": "quality",
                    "base_url": "https://poq.example.internal",
                    "username": "poq-user",
                    "password": "",
                }
            ]
        )
    )
    monkeypatch.setattr(
        "app.integrations.sap_po.client.settings.sap_po_password",
        SecretStr("common-password"),
    )

    assert credentials(configured.po_servers[0]) == ("poq-user", "common-password")


def test_rtims_ddl_credentials_are_separate_from_runtime_credentials() -> None:
    configured = Settings(
        rtims_enabled=True,
        rtims_oracle_host="db.internal",
        rtims_oracle_service="RTIMS",
        rtims_oracle_user="runtime_reader",
        rtims_oracle_password="runtime-secret",
        rtims_oracle_ddl_user="schema_owner",
        rtims_oracle_ddl_password="ddl-secret",
    )

    assert configured.rtims_configured is True
    assert configured.rtims_oracle_ddl_configured is True
    assert configured.rtims_oracle_password.get_secret_value() != (
        configured.rtims_oracle_ddl_password.get_secret_value()
    )


def test_rtims_postgresql_setup_can_use_a_separate_database() -> None:
    configured = Settings(
        database_url="postgresql+psycopg://app:secret@app-db/po_monitor",
        rtims_postgres_database_url="postgresql+psycopg://rtims:secret@rtims-db/rtims",
    )

    assert "rtims-db/rtims" in configured.rtims_postgres_setup_url
