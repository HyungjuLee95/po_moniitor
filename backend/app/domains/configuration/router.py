from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, model_validator

from app.core.config import settings
from app.core.security import (
    ROLE_PERMISSIONS,
    current_user,
    require_permissions,
    require_server_access,
)
from app.domains.configuration.registry import ServerRegistry
from app.domains.configuration.policy_repository import MonitoringPolicyRepository
from app.integrations.sap_po.client import soap_client
from app.integrations.rtims.repository import RtimsRepository


router = APIRouter(prefix="/configuration", tags=["Configuration"])


class MonitoringPolicyUpdate(BaseModel):
    response_window_minutes: int = Field(ge=5, le=1440)
    slow_threshold_ms: int = Field(ge=100, le=3_600_000)
    critical_threshold_ms: int = Field(ge=100, le=3_600_000)
    max_detail_rows: int = Field(ge=10, le=500)

    @model_validator(mode="after")
    def validate_thresholds(self):
        if self.critical_threshold_ms < self.slow_threshold_ms:
            raise ValueError("critical threshold must be greater than or equal to slow threshold")
        return self


@router.get("/monitoring-policy")
def monitoring_policy(
    sid: str,
    _: dict = Depends(require_permissions("monitoring:read")),
    __: dict = Depends(require_server_access),
) -> dict:
    server = ServerRegistry().require_capability(sid, "monitor")
    return {"data": MonitoringPolicyRepository().get(server.sid)}


@router.put("/monitoring-policy")
def update_monitoring_policy(
    sid: str,
    payload: MonitoringPolicyUpdate,
    user: dict = Depends(require_permissions("configuration:write")),
    _: dict = Depends(require_server_access),
) -> dict:
    server = ServerRegistry().require_capability(sid, "monitor")
    return {
        "data": MonitoringPolicyRepository().save(
            server.sid,
            payload.model_dump(),
            user["username"],
        )
    }


@router.get("/bootstrap")
def bootstrap(user: dict = Depends(current_user)) -> dict:
    allowed_sids = user.get("allowed_sids")
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
            if allowed_sids is None or server.sid in allowed_sids
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
    __: dict = Depends(require_server_access),
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
