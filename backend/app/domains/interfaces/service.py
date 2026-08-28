from __future__ import annotations

from app.core.config import PoServer, settings
from app.integrations.sap_po.client import call, soap_client
from app.integrations.sap_po.normalize import pick, records, recursive_values, serialize
from app.integrations.rtims.repository import RtimsRepository
from app.integrations.sap_po.errors import SapPoConnectionError


class InterfaceService:
    def list_business_systems(self, server: PoServer) -> list[dict]:
        if not settings.sap_po_live_mode:
            return [
                {
                    "sid": server.sid,
                    "business_system_id": f"BS_{server.sid}",
                    "name": server.display_name,
                    "active": True,
                }
            ]
        response = call(
            soap_client(server.sid, "business_system").service.Query,
            BusinessSystemID=None,
            Description=None,
            AdministrativeData=None,
        )
        identifiers = sorted({
            str(value)
            for value in recursive_values(response, "ComponentID")
            if value
        })
        return [
            {
                "sid": server.sid,
                "business_system_id": str(identifier),
                "name": str(identifier),
                "active": True,
            }
            for identifier in identifiers
        ]

    def topology(self, server: PoServer) -> list[dict]:
        if settings.rtims_configured:
            return RtimsRepository().topology(server.sid)
        return [
            {
                "source_system": "ERP",
                "target_system": "SAP PO",
                "interface_name": f"IF_{server.sid}_ORDER_IN",
                "source_namespace": "urn:company:erp",
                "target_namespace": "urn:company:po",
            },
            {
                "source_system": "SAP PO",
                "target_system": "MES",
                "interface_name": f"IF_{server.sid}_ORDER_OUT",
                "source_namespace": "urn:company:po",
                "target_namespace": "urn:company:mes",
            },
        ]

    def namespace_inventory(self, server: PoServer) -> list[dict]:
        if not settings.sap_po_live_mode:
            return [
                {
                    "sid": server.sid,
                    "interface_name": f"IF_{server.sid}_ORDER",
                    "namespace": "urn:company:order",
                    "direction": "OUTBOUND",
                    "source_system": "ERP",
                    "target_system": "MES",
                    "operation": "CreateOrder",
                }
            ]
        client = soap_client(server.sid, "interface_monitor")
        available = {
            name
            for wsdl_service in client.wsdl.services.values()
            for port in wsdl_service.ports.values()
            for name in port.binding._operations
        }
        candidates = (
            "getAllInterfaces",
            "getInterfaceInfo",
            "getInterfaces",
            "getInterfaceList",
            "getIntfInfo",
        )
        operation_name = next((name for name in candidates if name in available), None)
        if operation_name is None:
            raise SapPoConnectionError(
                "InterfaceMonitor WSDL does not expose a supported inventory operation"
            )
        response = call(getattr(client.service, operation_name))
        result = []
        for row in records(
            serialize(response),
            (
                "interfaceName",
                "interfaceNamespace",
                "namespace",
                "operation",
                "senderService",
                "receiverService",
                "fromAction",
                "fromActionNamespace",
                "fromService",
                "toAction",
                "toActionNamespace",
                "toService",
            ),
        ):
            from_action = pick(row, "fromAction")
            to_action = pick(row, "toAction")
            name = pick(
                row,
                "interfaceName",
                "name",
                "interface",
                "fromAction",
                "toAction",
            )
            namespace = pick(
                row,
                "interfaceNamespace",
                "namespace",
                "outboundNamespace",
                "inboundNamespace",
                "fromActionNamespace",
                "toActionNamespace",
            )
            if not name and not namespace:
                continue
            result.append(
                {
                    "sid": server.sid,
                    "interface_name": str(name or ""),
                    "namespace": str(namespace or ""),
                    "direction": str(
                        pick(
                            row,
                            "direction",
                            default=(
                                "OUTBOUND_TO_INBOUND"
                                if from_action and to_action
                                else ""
                            ),
                        )
                    ),
                    "source_system": pick(
                        row, "senderService", "sourceSystem", "fromService"
                    ),
                    "target_system": pick(
                        row, "receiverService", "targetSystem", "toService"
                    ),
                    "operation": pick(
                        row, "operation", "operationName", "toAction", "objectId"
                    ),
                }
            )
        return result
