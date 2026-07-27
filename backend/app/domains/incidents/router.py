from fastapi import APIRouter, Depends

from app.core.security import require_permissions
from app.domains.configuration.registry import ServerRegistry


router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("")
def list_incidents(
    sid: str,
    _: dict = Depends(require_permissions("incidents:read")),
) -> dict:
    server = ServerRegistry().require_capability(sid, "monitor")
    return {
        "data": [
            {
                "incident_key": f"{server.sid}:message-timeout",
                "sid": server.sid,
                "incident_type": "ERROR",
                "interface_name": f"IF_{server.sid}_ORDER",
                "status": "OPEN",
                "detail": "Adapter response timeout",
            }
        ]
    }


@router.patch("/{incident_key:path}/resolve")
def resolve_incident(
    incident_key: str,
    user: dict = Depends(require_permissions("incidents:resolve")),
) -> dict:
    return {
        "data": {
            "incident_key": incident_key,
            "resolved": True,
            "resolved_by": user["username"],
        }
    }
