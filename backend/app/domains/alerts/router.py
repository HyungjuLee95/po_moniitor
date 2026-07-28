from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.security import require_permissions, require_server_access
from app.domains.configuration.registry import ServerRegistry
from app.integrations.rtims.repository import RtimsRepository


router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("")
def list_alerts(
    sid: str,
    _: dict = Depends(require_permissions("alerts:read")),
    __: dict = Depends(require_server_access),
) -> dict:
    server = ServerRegistry().require_capability(sid, "monitor")
    if settings.rtims_configured:
        rows = RtimsRepository().incidents(server.sid, limit=50, offset=0, hours=24)
        return {
            "data": [
                {
                    "id": str(row["error_log_id"]),
                    "sid": row["server_id"],
                    "title": row.get("ob_intf_nm") or row.get("msgguid") or "RTIMS 오류",
                    "domain": row.get("category_nm") or "messages",
                    "detail": row.get("error_text") or "상세 오류 내용이 없습니다.",
                    "severity": "warning" if str(row.get("category_nm", "")).upper() == "WARNING" else "critical",
                    "status": "resolved" if row.get("error_state") == "C" else "open",
                    "occurred_at": (
                        row["last_seen_at"].isoformat()
                        if row.get("last_seen_at") else None
                    ),
                }
                for row in rows
            ]
        }
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
