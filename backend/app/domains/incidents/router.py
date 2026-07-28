from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.security import require_permissions, require_server_access
from app.domains.configuration.registry import ServerRegistry
from app.integrations.rtims.repository import RtimsRepository


router = APIRouter(prefix="/incidents", tags=["Incidents"])


class ResolveIncidentRequest(BaseModel):
    message: str | None = Field(default=None, max_length=2000)


@router.get("")
def list_incidents(
    sid: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    hours: int = Query(default=24, ge=1, le=168),
    _: dict = Depends(require_permissions("incidents:read")),
    __: dict = Depends(require_server_access),
) -> dict:
    server = ServerRegistry().require_capability(sid, "monitor")
    if settings.rtims_configured:
        rows = RtimsRepository().incidents(server.sid, limit, offset, hours)
        return {"data": rows, "meta": {"source": "rtims-oracle", "count": len(rows)}}
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
        ],
        "meta": {"source": "demo"},
    }


@router.patch("/{error_log_id}/resolve")
def resolve_incident(
    error_log_id: int,
    payload: ResolveIncidentRequest,
    user: dict = Depends(require_permissions("incidents:resolve")),
) -> dict:
    if not settings.rtims_configured:
        raise HTTPException(status_code=409, detail="RTIMS Oracle is not configured")
    RtimsRepository().resolve_incident(
        error_log_id,
        user["username"],
        payload.message,
    )
    return {
        "data": {
            "error_log_id": error_log_id,
            "resolved": True,
            "resolved_by": user["username"],
        }
    }
