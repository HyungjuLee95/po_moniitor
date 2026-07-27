from fastapi import APIRouter, Depends

from app.core.security import require_permissions
from app.domains.configuration.registry import ServerRegistry


router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("")
def list_alerts(
    sid: str,
    _: dict = Depends(require_permissions("alerts:read")),
) -> dict:
    server = ServerRegistry().require_capability(sid, "monitor")
    return {
        "data": [
            {
                "id": f"{server.sid}-CHANNEL-001",
                "sid": server.sid,
                "title": "Receiver Channel response delay",
                "domain": "channels",
                "detail": "Response time exceeded the configured threshold.",
                "severity": "critical",
                "status": "open",
                "occurred_at": "now",
            }
        ]
    }


@router.patch("/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: str,
    user: dict = Depends(require_permissions("alerts:acknowledge")),
) -> dict:
    return {
        "data": {
            "id": alert_id,
            "status": "acknowledged",
            "acknowledged_by": user["username"],
        }
    }
