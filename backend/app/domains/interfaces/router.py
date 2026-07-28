from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.security import require_permissions, require_server_access
from app.domains.configuration.registry import ServerRegistry
from app.domains.interfaces.service import InterfaceService


router = APIRouter(prefix="/interfaces", tags=["Interfaces"])


@router.get("")
def list_interfaces(
    sid: str,
    _: dict = Depends(require_permissions("interfaces:read")),
    __: dict = Depends(require_server_access),
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


@router.get("/topology")
def interface_topology(
    sid: str,
    _: dict = Depends(require_permissions("interfaces:read")),
    __: dict = Depends(require_server_access),
) -> dict:
    server = ServerRegistry().require_capability(sid, "monitor")
    rows = InterfaceService().topology(server)
    return {
        "data": rows,
        "meta": {
            "count": len(rows),
            "sid": server.sid,
            "source": "rtims-oracle" if settings.rtims_configured else "demo",
        },
    }
