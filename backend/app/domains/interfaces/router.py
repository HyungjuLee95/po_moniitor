from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.security import require_permissions
from app.domains.configuration.registry import ServerRegistry
from app.domains.interfaces.service import InterfaceService


router = APIRouter(prefix="/interfaces", tags=["Interfaces"])


@router.get("")
def list_interfaces(
    sid: str,
    _: dict = Depends(require_permissions("interfaces:read")),
) -> dict:
    server = ServerRegistry().require_capability(sid, "monitor")
    rows = InterfaceService().list_business_systems(server)
    return {
        "data": rows,
        "meta": {
            "count": len(rows),
            "sid": server.sid,
            "source": "demo" if not settings.sap_po_live_mode else "sap-po-business-system",
        },
    }
