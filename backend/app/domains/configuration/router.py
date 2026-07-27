from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.security import ROLE_PERMISSIONS, current_user, require_permissions
from app.domains.configuration.registry import ServerRegistry
from app.integrations.sap_po.client import soap_client
from app.integrations.rtims.repository import RtimsRepository


router = APIRouter(prefix="/configuration", tags=["Configuration"])


@router.get("/bootstrap")
def bootstrap(user: dict = Depends(current_user)) -> dict:
    return {
        "application": {
            "name": settings.app_name,
            "version": settings.app_version,
            "mode": "demo" if settings.demo_mode else "live",
        },
        "current_user": user,
        "servers": [
            server.public_view()
            for server in ServerRegistry().list_enabled()
        ],
        "roles": {
            role: sorted(permissions)
            for role, permissions in ROLE_PERMISSIONS.items()
        },
    }


@router.get("/rtims-check")
def rtims_check(
    _: dict = Depends(require_permissions("configuration:read")),
) -> dict:
    if not settings.rtims_enabled:
        return {"data": {"enabled": False, "ready": False}}
    RtimsRepository().check()
    return {"data": {"enabled": True, "ready": True}}


@router.get("/sap-po-check")
def sap_po_check(
    sid: str,
    _: dict = Depends(require_permissions("configuration:read")),
) -> dict:
    server = ServerRegistry().get(sid)
    service_names = ["systatus", "channels", "business_system"]
    if "channel-control" in server.capabilities:
        service_names.append("channel_admin")
    if "audit" in server.capabilities:
        service_names.extend(["aae_monitor", "adapter_monitor"])

    results = []
    for service_name in service_names:
        try:
            client = soap_client(server.sid, service_name)
            operations: list[str] = []
            for wsdl_service in client.wsdl.services.values():
                for port in wsdl_service.ports.values():
                    operations.extend(port.binding._operations.keys())
            results.append(
                {
                    "service": service_name,
                    "status": "ok",
                    "operations": sorted(set(operations)),
                }
            )
        except Exception as exc:
            results.append(
                {
                    "service": service_name,
                    "status": "error",
                    "detail": str(exc),
                }
            )
    return {
        "data": {
            "sid": server.sid,
            "live_mode": settings.sap_po_live_mode,
            "ready": all(item["status"] == "ok" for item in results),
            "services": results,
        }
    }
