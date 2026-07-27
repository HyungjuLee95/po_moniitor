from fastapi import APIRouter, Depends

from app.core.security import require_permissions
from app.domains.monitoring.service import MonitoringService


router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/summary")
def summary(
    sid: str,
    _: dict = Depends(require_permissions("monitoring:read")),
) -> dict:
    return {"data": MonitoringService().summary(sid)}
