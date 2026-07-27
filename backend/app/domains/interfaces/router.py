from fastapi import APIRouter, Depends

from app.core.security import require_permissions
from app.domains.configuration.registry import ServerRegistry


router = APIRouter(prefix="/interfaces", tags=["Interfaces"])


@router.get("")
def list_interfaces(
    sid: str,
    _: dict = Depends(require_permissions("interfaces:read")),
) -> dict:
    server = ServerRegistry().require_capability(sid, "monitor")
    return {
        "data": [
            {
                "sid": server.sid,
                "interface_name": f"IF_{server.sid}_EMPLOYEE_SYNC",
                "namespace": f"http://company/interfaces/{server.sid}/EMPLOYEE",
                "source_system": server.sid,
                "target_system": "ERP",
                "module_name": "HR",
                "active": True,
            },
            {
                "sid": server.sid,
                "interface_name": f"IF_{server.sid}_ORDER_STATUS",
                "namespace": f"http://company/interfaces/{server.sid}/ORDER",
                "source_system": "ERP",
                "target_system": server.sid,
                "module_name": "SD",
                "active": True,
            },
        ]
    }
