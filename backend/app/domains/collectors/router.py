from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.security import require_permissions
from app.domains.collectors.repository import CollectorRepository
from app.domains.collectors.service import CollectorService
from app.domains.configuration.registry import ServerRegistry


router = APIRouter(prefix="/collectors", tags=["Collectors"])


class CollectorRunRequest(BaseModel):
    sids: list[str] = Field(default_factory=list, max_length=20)


@router.get("")
def collector_status(
    user: dict = Depends(require_permissions("collectors:read")),
) -> dict:
    allowed_sids = user.get("allowed_sids")
    servers = [
        server for server in ServerRegistry().list_enabled()
        if "collector" in server.capabilities
        and (allowed_sids is None or server.sid in allowed_sids)
    ]
    return {"data": CollectorRepository().list(servers)}


@router.post("/run")
def run_collectors(
    payload: CollectorRunRequest,
    user: dict = Depends(require_permissions("collectors:run")),
) -> dict:
    requested = payload.sids or [
        server.sid for server in ServerRegistry().list_enabled()
        if "collector" in server.capabilities
    ]
    allowed_sids = user.get("allowed_sids")
    if allowed_sids is not None and not set(requested).issubset(allowed_sids):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="server access denied")
    servers = [
        ServerRegistry().require_capability(sid, "collector")
        for sid in dict.fromkeys(requested)
    ]
    results = []
    for server in servers:
        results.append(CollectorService().run(server, user["username"]))
    return {
        "data": results,
        "meta": {"execution": "sequential"},
    }
