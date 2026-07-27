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
    assert settings.po_servers[0].public_view()["display_name"] == "Planning Quality"
    assert "base_url" not in settings.po_servers[0].public_view()
