import base64
from types import SimpleNamespace

from zeep import xsd

from app.core.config import PoServer
from app.domains.channels.service import ChannelService
from app.domains.interfaces.service import InterfaceService
from app.domains.messages.service import MessageService
from app.integrations.sap_po.directory import extract_and_decrypt_password
from app.integrations.sap_po.client import rewrite_host_alias
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


def test_wsdl_short_host_alias_reuses_configured_server_origin() -> None:
    server = PoServer(
        sid="POQ",
        display_name="Quality",
        environment="quality",
        base_url="http://poq.example.internal",
        port=50000,
        host_aliases=["poq-short"],
    )

    rewritten = rewrite_host_alias(
        "http://poq-short:50000/service/path?wsdl=binding",
        server,
    )

    assert rewritten == "http://poq.example.internal:50000/service/path?wsdl=binding"
    assert rewrite_host_alias("https://schemas.example.org/schema.xsd", server) == (
        "https://schemas.example.org/schema.xsd"
    )


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


def test_channel_inventory_uses_none_for_all_components(monkeypatch) -> None:
    monkeypatch.setattr("app.domains.channels.service.settings.sap_po_live_mode", True)
    captured = {}

    def query(**kwargs):
        captured.update(kwargs)
        return {"CommunicationChannelID": []}

    monkeypatch.setattr(
        "app.domains.channels.service.soap_client",
        lambda sid, name: SimpleNamespace(service=SimpleNamespace(Query=query)),
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

    assert ChannelService().inventory(server) == []
    assert captured["CommunicationChannelID"] == {
        "PartyID": "",
        "ComponentID": xsd.SkipValue,
        "ChannelID": "*",
    }


def test_business_system_list_calls_query_contract(monkeypatch) -> None:
    monkeypatch.setattr("app.domains.interfaces.service.settings.sap_po_live_mode", True)
    captured = {}

    def query(**kwargs):
        captured.update(kwargs)
        return {"BusinessSystemID": [{"ComponentID": "BS_POQ"}]}

    monkeypatch.setattr(
        "app.domains.interfaces.service.soap_client",
        lambda sid, name: SimpleNamespace(service=SimpleNamespace(Query=query)),
    )
    monkeypatch.setattr(
        "app.domains.interfaces.service.call",
        lambda operation, *args, **kwargs: operation(*args, **kwargs),
    )
    server = PoServer(
        sid="POQ",
        display_name="Quality",
        environment="quality",
        base_url="http://po.example.internal",
    )

    rows = InterfaceService().list_business_systems(server)

    assert captured == {
        "BusinessSystemID": None,
        "Description": None,
        "AdministrativeData": None,
    }
    assert rows[0]["business_system_id"] == "BS_POQ"


def test_namespace_inventory_prefers_get_all_interfaces(monkeypatch) -> None:
    monkeypatch.setattr("app.domains.interfaces.service.settings.sap_po_live_mode", True)
    operation = lambda: [
        {
            "fromAction": "IF_ORDER_OUT",
            "fromActionNamespace": "urn:company:order:out",
            "fromService": "ERP",
            "toAction": "IF_ORDER_IN",
            "toActionNamespace": "urn:company:order:in",
            "toService": "MES",
        }
    ]
    client = SimpleNamespace(
        service=SimpleNamespace(getAllInterfaces=operation),
        wsdl=SimpleNamespace(
            services={
                "service": SimpleNamespace(
                    ports={
                        "port": SimpleNamespace(
                            binding=SimpleNamespace(
                                _operations={"getAllInterfaces": object()}
                            )
                        )
                    }
                )
            }
        ),
    )
    monkeypatch.setattr(
        "app.domains.interfaces.service.soap_client",
        lambda sid, name: client,
    )
    monkeypatch.setattr(
        "app.domains.interfaces.service.call",
        lambda operation, *args, **kwargs: operation(*args, **kwargs),
    )
    server = PoServer(
        sid="POQ",
        display_name="Quality",
        environment="quality",
        base_url="http://po.example.internal",
    )

    rows = InterfaceService().namespace_inventory(server)

    assert rows[0]["interface_name"] == "IF_ORDER_OUT"
    assert rows[0]["namespace"] == "urn:company:order:out"
    assert rows[0]["direction"] == "OUTBOUND_TO_INBOUND"
    assert rows[0]["source_system"] == "ERP"
    assert rows[0]["target_system"] == "MES"
    assert rows[0]["operation"] == "IF_ORDER_IN"


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
    assert captured["args"][-1] == "20"


def test_message_audit_calls_full_adapter_contract(monkeypatch) -> None:
    monkeypatch.setattr("app.domains.messages.service.settings.sap_po_live_mode", True)
    captured = {}

    def get_messages_by_ids(**kwargs):
        captured["messages"] = kwargs
        return {"messageKey": "key-1"}

    def get_log_entries(**kwargs):
        captured["logs"] = kwargs
        return [
            {
                "status": "SUCCESS",
                "timeStamp": "2026-07-28T01:02:03Z",
                "localizedText": "Processed",
            }
        ]

    monkeypatch.setattr(
        "app.domains.messages.service.soap_client",
        lambda sid, name: SimpleNamespace(
            service=SimpleNamespace(
                getMessagesByIDs=get_messages_by_ids,
                getLogEntries=get_log_entries,
            )
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

    rows = MessageService().audit(server, "message-1")

    assert captured["messages"] == {
        "messageIds": ["message-1"],
        "referenceIds": ["0"],
        "correlationIds": ["0"],
        "archive": False,
    }
    assert captured["logs"]["messageKey"] == "key-1\\"
    assert captured["logs"]["archive"] is False
    assert captured["logs"]["maxResults"] == 100
    assert captured["logs"]["locale"] is None
    assert rows[0]["status"] == "SUCCESS"
