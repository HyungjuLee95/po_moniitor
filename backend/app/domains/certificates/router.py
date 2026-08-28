from fastapi import APIRouter, Depends, Query

from app.core.security import require_permissions, require_server_access
from app.domains.certificates.service import CertificateService
from app.domains.configuration.registry import ServerRegistry


router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.get("")
def list_certificates(
    sid: str,
    warning_days: int = Query(default=30, ge=1, le=3650),
    _: dict = Depends(require_permissions("certificates:read")),
    __: dict = Depends(require_server_access),
) -> dict:
    server = ServerRegistry().require_capability(sid, "monitor")
    rows, meta = CertificateService().list(server, warning_days)
    return {"data": rows, "meta": meta}
