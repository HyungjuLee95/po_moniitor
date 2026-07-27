from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.security import require_permissions
from app.domains.configuration.registry import ServerRegistry
from app.domains.messages.service import MessageService


router = APIRouter(prefix="/collectors", tags=["Collectors"])


class CollectorRunRequest(BaseModel):
    sids: list[str] = Field(default_factory=list, max_length=20)


@router.get("")
def collector_status(
    _: dict = Depends(require_permissions("collectors:read")),
) -> dict:
    servers = [
        server for server in ServerRegistry().list_enabled()
        if "collector" in server.capabilities
    ]
    return {
        "data": [
            {
                "sid": server.sid,
                "server_name": server.display_name,
                "status": "READY",
                "last_success_at": None,
                "item_count": 0,
            }
            for server in servers
        ]
    }


@router.post("/run")
def run_collectors(
    payload: CollectorRunRequest,
    user: dict = Depends(require_permissions("collectors:run")),
) -> dict:
    requested = payload.sids or [
        server.sid for server in ServerRegistry().list_enabled()
        if "collector" in server.capabilities
    ]
    servers = [
        ServerRegistry().require_capability(sid, "collector")
        for sid in dict.fromkeys(requested)
    ]
    results = []
    for server in servers:
        rows = MessageService().list_recent(server, 1000)
        results.append(
            {
                "sid": server.sid,
                "status": "SUCCESS",
                "fetched": len(rows),
                "requested_by": user["username"],
                "source": "demo" if not settings.sap_po_live_mode else "sap-po-aae-monitor",
            }
        )
    return {
        "data": results,
        "meta": {"execution": "sequential"},
    }
