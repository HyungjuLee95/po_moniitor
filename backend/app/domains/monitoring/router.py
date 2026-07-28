from fastapi import APIRouter, Depends, Query

from app.core.security import require_permissions, require_server_access
from app.domains.monitoring.service import MonitoringService


router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/summary")
def summary(
    sid: str,
    _: dict = Depends(require_permissions("monitoring:read")),
    __: dict = Depends(require_server_access),
) -> dict:
    return {"data": MonitoringService().summary(sid)}


@router.get("/performance")
def performance(
    sid: str,
    hours: int = Query(default=24, ge=1, le=168),
    _: dict = Depends(require_permissions("monitoring:read")),
    __: dict = Depends(require_server_access),
) -> dict:
    rows = MonitoringService().performance(sid, hours)
    return {"data": rows, "meta": {"sid": sid.upper(), "hours": hours, "count": len(rows)}}


@router.get("/slow-messages")
def slow_messages(
    sid: str,
    _: dict = Depends(require_permissions("monitoring:read")),
    __: dict = Depends(require_server_access),
) -> dict:
    result = MonitoringService().slow_messages(sid)
    return {
        "data": result["items"],
        "meta": {"sid": sid.upper(), **result["policy"], "count": len(result["items"])},
    }


@router.get("/resources")
def resources(
    sid: str,
    _: dict = Depends(require_permissions("monitoring:read")),
    __: dict = Depends(require_server_access),
) -> dict:
    rows = MonitoringService().resources(sid)
    return {"data": rows, "meta": {"sid": sid.upper(), "count": len(rows)}}


@router.get("/queues")
def queues(
    sid: str,
    _: dict = Depends(require_permissions("monitoring:read")),
    __: dict = Depends(require_server_access),
) -> dict:
    return {"data": MonitoringService().queues(sid), "meta": {"sid": sid.upper()}}
