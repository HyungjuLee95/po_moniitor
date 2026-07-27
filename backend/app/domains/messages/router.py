from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query

from app.core.security import require_permissions
from app.domains.configuration.registry import ServerRegistry


router = APIRouter(prefix="/messages", tags=["Messages"])


@router.get("")
def list_messages(
    sid: str,
    limit: int = Query(default=20, ge=1, le=200),
    _: dict = Depends(require_permissions("messages:read")),
) -> dict:
    server = ServerRegistry().require_capability(sid, "monitor")
    now = datetime.now(timezone.utc)
    rows = [
        {
            "message_id": f"{server.sid}-{index:06d}",
            "sid": server.sid,
            "interface_name": f"IF_{server.sid}_ORDER_{index % 4 + 1}",
            "status": "ERROR" if index % 11 == 0 else "SUCCESS",
            "start_time": (now - timedelta(minutes=index * 3)).isoformat(),
            "duration_ms": 420 + index * 37,
        }
        for index in range(1, limit + 1)
    ]
    return {"data": rows, "meta": {"count": len(rows), "source": "demo"}}
