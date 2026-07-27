import base64
from types import SimpleNamespace

from app.core.config import PoServer
from app.domains.channels.service import ChannelService
from app.domains.messages.service import MessageService
from app.integrations.sap_po.directory import extract_and_decrypt_password
from app.integrations.sap_po.normalize import pick, records, recursive_values


def encode_legacy_password(value: str) -> str:
    encrypted = bytes([0]) + bytes(
        character ^ 0x74 for character in reversed(value.encode("utf-8"))
    )
    return base64.b64encode(encrypted).decode("ascii")


def test_directory_password_algorithm_matches_legacy_java_flow() -> None:
    encoded = encode_legacy_password("safe-test-value")
    xml = f"<Channel><dbpassword>{encoded}</dbpassword></Channel>"
    assert extract_and_decrypt_password(xml) == "safe-test-value"


def test_soap_normalizer_handles_nested_wrappers() -> None:
    payload = {
        "return": {
            "items": [
                {"MessageID": "one", "Status": "SUCCESS"},
                {"MessageID": "two", "Status": "ERROR"},
            ]
        }
    }
    rows = records(payload, ("messageId", "status"))
    assert [pick(row, "message_id") for row in rows] == ["one", "two"]


def test_recursive_message_key_extraction() -> None:
    payload = {"messages": [{"messageKey": "key-1"}, {"nested": {"messageKey": "key-2"}}]}
    assert recursive_values(payload, "messageKey") == ["key-1", "key-2"]


def test_channel_status_calls_systatus_operation(monkeypatch) -> None:
    monkeypatch.setattr("app.domains.channels.service.settings.sap_po_live_mode", True)
    service = SimpleNamespace(
        getChannInfo=lambda: [
            {
                "objectId": "JDBC_Receiver",
                "channelName": "JDBC_Receiver",
                "service": "BS_POQ",
                "direction": "Receiver",
                "status": "ERROR",
            }
        ]
    )
    monkeypatch.setattr(
        "app.domains.channels.service.soap_client",
        lambda sid, name: SimpleNamespace(service=service),
    )
    monkeypatch.setattr(
        "app.domains.channels.service.call",
        lambda operation, *args, **kwargs: operation(*args, **kwargs),
    )
    server = PoServer(
        sid="POQ",
        display_name="Quality",
        environment="quality",
        base_url="http://po.example.internal",
    )
    rows = ChannelService().list_status(server)
    assert rows[0]["component_id"] == "BS_POQ"
    assert rows[0]["status"] == "Error"


def test_message_list_calls_aae_monitor_contract(monkeypatch) -> None:
    monkeypatch.setattr("app.domains.messages.service.settings.sap_po_live_mode", True)
    captured = {}

    def get_message_logs(*args):
        captured["args"] = args
        return [
            {
                "messageId": "message-1",
                "msgStatus": "SUCCESS",
                "interfaceName": "IF_ORDER",
                "sentRecvTime": "2026-07-28T01:02:03Z",
            }
        ]

    monkeypatch.setattr(
        "app.domains.messages.service.soap_client",
        lambda sid, name: SimpleNamespace(
            service=SimpleNamespace(getMessageLogs=get_message_logs)
        ),
    )
    monkeypatch.setattr(
        "app.domains.messages.service.call",
        lambda operation, *args, **kwargs: operation(*args, **kwargs),
    )
    server = PoServer(
        sid="POQ",
        display_name="Quality",
        environment="quality",
        base_url="http://po.example.internal",
    )
    rows = MessageService().list_recent(server, 20)
    assert rows[0]["message_id"] == "message-1"
    assert captured["args"][-1] == 20
