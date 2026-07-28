from __future__ import annotations

from app.core.config import PoServer, settings
from app.integrations.sap_po.client import call, soap_client
from app.integrations.sap_po.normalize import pick, records
from app.integrations.rtims.repository import RtimsRepository


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
            soap_client(server.sid, "business_system").service.getBusinessSystemList
        )
        result = []
        for row in records(
            response,
            ("businessSystemId", "businessSystemName", "name", "id"),
        ):
            identifier = pick(row, "businessSystemId", "id", "name")
            if identifier is None:
                continue
            result.append(
                {
                    "sid": server.sid,
                    "business_system_id": str(identifier),
                    "name": str(pick(row, "businessSystemName", "name", default=identifier)),
                    "active": True,
                }
            )
        return result

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
