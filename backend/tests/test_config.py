import json

from app.core.config import Settings


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
