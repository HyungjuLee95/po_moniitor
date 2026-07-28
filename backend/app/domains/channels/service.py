from __future__ import annotations

from typing import Any

from app.core.config import PoServer, settings
from app.integrations.sap_po.client import call, soap_client
from app.integrations.sap_po.directory import (
    extract_and_decrypt_password,
    read_channel_xml,
)
from app.integrations.sap_po.normalize import pick, records, serialize


def _demo_rows(server: PoServer) -> list[dict]:
    values = [
        ("REST_Receiver_EMPLOYEE_SYNC", "Receiver", "Running", 61),
        ("JDBC_Sender_MASTER_DATA", "Sender", "Running", 42),
        ("SOAP_Sender_ORDER_STATUS", "Sender", "Error", None),
        ("FILE_Receiver_BATCH", "Receiver", "Stopped", None),
    ]
    return [
        {
            "id": index,
            "sid": server.sid,
            "component_id": f"BS_{server.sid}",
            "channel_id": name,
            "direction": direction,
            "status": status,
            "latency_ms": latency,
        }
        for index, (name, direction, status, latency) in enumerate(values, 1)
    ]


def _status(raw: Any) -> str:
    value = str(raw or "").upper()
    if "ERROR" in value or "FAIL" in value:
        return "Error"
    if "STOP" in value or "INACTIVE" in value:
        return "Stopped"
    return "Running"


def _channel_id(value: dict) -> tuple[str, str, str]:
    identifier = pick(value, "CommunicationChannelID", "ChannelID", default={})
    if not isinstance(identifier, dict):
        identifier = {}
    component = pick(
        identifier, "ComponentID", default=pick(value, "service", "componentId", default="")
    )
    channel = pick(
        identifier, "ChannelID", default=pick(value, "channelName", "objectId", default="")
    )
    party = pick(identifier, "PartyID", default=pick(value, "party", default=""))
    return str(component or ""), str(channel or ""), str(party or "")


class ChannelService:
    def list_status(self, server: PoServer) -> list[dict]:
        if not settings.sap_po_live_mode:
            return _demo_rows(server)
        response = call(soap_client(server.sid, "systatus").service.getChannInfo)
        raw_rows = records(
            response,
            (
                "objectId",
                "channelName",
                "adapterType",
                "automation",
                "direction",
                "service",
                "status",
            ),
        )
        result = []
        for index, row in enumerate(raw_rows, 1):
            component, channel, _ = _channel_id(row)
            result.append(
                {
                    "id": index,
                    "sid": server.sid,
                    "component_id": component or str(pick(row, "service", default="")),
                    "channel_id": channel or str(pick(row, "channelName", "objectId", default="")),
                    "direction": str(pick(row, "direction", default="Unknown")),
                    "adapter_type": str(pick(row, "adapterType", default="")),
                    "automation": str(pick(row, "automation", default="")),
                    "status": _status(pick(row, "status")),
                    "raw_status": str(pick(row, "status", default="")),
                    "last_error_since": pick(row, "lastErrorSince"),
                    "short_text": pick(row, "shortText"),
                    "latency_ms": None,
                }
            )
        return result

    def inventory(
        self,
        server: PoServer,
        component_id: str = "*",
        channel_pattern: str = "*",
    ) -> list[dict]:
        if not settings.sap_po_live_mode:
            return [
                row for row in _demo_rows(server)
                if component_id == "*" or row["component_id"] == component_id
            ]
        client = soap_client(server.sid, "channels")
        response = call(
            client.service.Query,
            CommunicationChannelID={
                "PartyID": "",
                "ComponentID": component_id,
                "ChannelID": channel_pattern,
            },
            Description=None,
            AdministrativeData=None,
        )
        rows = records(response, ("CommunicationChannelID", "ChannelID", "ComponentID"))
        result = []
        for index, row in enumerate(rows, 1):
            component, channel, party = _channel_id(row)
            if not channel:
                continue
            result.append(
                {
                    "id": index,
                    "sid": server.sid,
                    "component_id": component,
                    "channel_id": channel,
                    "party_id": party,
                }
            )
        return result

    def detail(
        self,
        server: PoServer,
        component_id: str,
        channel_id: str,
        include_password: bool = False,
    ) -> dict:
        if not settings.sap_po_live_mode:
            return {
                "sid": server.sid,
                "component_id": component_id,
                "channel_id": channel_id,
                "attributes": {},
                "password": None,
                "source": "demo",
            }
        client = soap_client(server.sid, "channels")
        response = call(
            client.service.Read,
            ReadContext="User",
            CommunicationChannelID=[
                {
                    "PartyID": "",
                    "ComponentID": component_id,
                    "ChannelID": channel_id,
                }
            ],
        )
        data = serialize(response)
        attributes: dict[str, Any] = {}
        for attribute in records(data, ("Name", "Value")):
            name = pick(attribute, "Name", "AttributeName")
            value = pick(attribute, "Value", "AttributeValue")
            if name is not None:
                attributes[str(name)] = value
        result = {
            "sid": server.sid,
            "component_id": component_id,
            "channel_id": channel_id,
            "attributes": attributes,
            "source": "sap-po",
        }
        if include_password:
            raw_xml = read_channel_xml(server, component_id, channel_id)
            result["password"] = extract_and_decrypt_password(raw_xml)
        return result

    def control(self, server: PoServer, action: str, targets: list[Any]) -> dict:
        if not settings.sap_po_live_mode:
            return {
                "requested": len(targets),
                "succeeded": len(targets),
                "failed": 0,
                "results": [
                    {
                        "component_id": target.component_id,
                        "channel_id": target.channel_id,
                        "success": True,
                    }
                    for target in targets
                ],
                "source": "demo",
            }
        client = soap_client(server.sid, "channel_admin")
        factory = client.type_factory("ns0")
        automation_states = {
            "AUTOMATIC": "SCHEDULER",
            "MANUAL": "MANUAL",
            "EXTERNAL": "WEBSERVICE",
        }
        results = []
        for target in targets:
            descriptor = factory.channelAdminDescriptor(
                service=target.component_id,
                name=target.channel_id,
                party="",
            )
            try:
                if action == "START":
                    call(
                        client.service.setChannelAutomationStatus,
                        channels=[descriptor],
                        automationState="WEBSERVICE",
                    )
                    call(
                        client.service.startChannels,
                        channel=[descriptor],
                        language="EN",
                    )
                elif action == "STOP":
                    call(
                        client.service.stopChannels,
                        channel=[descriptor],
                        language="EN",
                    )
                elif action in automation_states:
                    call(
                        client.service.setChannelAutomationStatus,
                        channels=[descriptor],
                        automationState=automation_states[action],
                    )
                verification = call(
                    client.service.getChannelAutomationStatus,
                    channels=[descriptor],
                )
                results.append(
                    {
                        "component_id": target.component_id,
                        "channel_id": target.channel_id,
                        "success": True,
                        "verification": serialize(verification),
                    }
                )
            except Exception as exc:
                results.append(
                    {
                        "component_id": target.component_id,
                        "channel_id": target.channel_id,
                        "success": False,
                        "error": str(exc),
                    }
                )
        succeeded = sum(1 for result in results if result["success"])
        return {
            "requested": len(results),
            "succeeded": succeeded,
            "failed": len(results) - succeeded,
            "results": results,
            "source": "sap-po",
        }
