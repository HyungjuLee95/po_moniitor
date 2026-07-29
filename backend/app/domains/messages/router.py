from fastapi import APIRouter, Depends, Query

from app.core.config import settings
from app.core.security import require_permissions, require_server_access
from app.domains.configuration.registry import ServerRegistry
from app.domains.messages.service import MessageService
from app.integrations.rtims.repository import RtimsRepository


router = APIRouter(prefix="/messages", tags=["Messages"])


@router.get("")
def list_messages(
    sid: str,
    limit: int = Query(default=20, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    hours: int = Query(default=24, ge=1, le=168),
    status: str | None = Query(default=None, max_length=32),
    keyword: str | None = Query(default=None, max_length=128),
    _: dict = Depends(require_permissions("messages:read")),
    __: dict = Depends(require_server_access),
) -> dict:
    server = ServerRegistry().require_capability(sid, "monitor")
    rows = (
        RtimsRepository().recent_messages(
            server.sid,
            limit,
            offset=offset,
            hours=hours,
            status=status,
            keyword=keyword,
        )
        if settings.rtims_configured
        else MessageService().list_recent(
            server,
            limit,
            hours=hours,
            status=status,
            keyword=keyword,
        )
    )
    return {
        "data": rows,
        "meta": {
            "count": len(rows),
            "sid": server.sid,
            "hours": hours,
            "offset": offset,
            "status": status,
            "keyword": keyword,
            "source": (
                "rtims-oracle"
                if settings.rtims_configured
                else ("demo" if not settings.sap_po_live_mode else "sap-po-aae-monitor")
            ),
        },
    }


@router.get("/{message_id}/audit")
def message_audit(
    message_id: str,
    sid: str,
    _: dict = Depends(require_permissions("messages:read")),
    __: dict = Depends(require_server_access),
) -> dict:
    server = ServerRegistry().require_capability(sid, "audit")
    rows = MessageService().audit(server, message_id)
    return {"data": rows, "meta": {"count": len(rows), "sid": server.sid}}
