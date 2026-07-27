from __future__ import annotations

from app.core.config import PoServer, settings
from app.integrations.sap_po.client import call, soap_client
from app.integrations.sap_po.normalize import pick, records


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
