from io import BytesIO

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.security import require_permissions, require_server_access
from app.domains.configuration.registry import ServerRegistry
from app.domains.hrd.service import HrdService, generate_excel


router = APIRouter(prefix="/hrd", tags=["HRD"])


class TestMessageRequest(BaseModel):
    sid: str
    if_id: str = Field(min_length=1, max_length=128)


@router.get("/interfaces")
def list_interfaces(
    sid: str,
    company_codes: list[str] = Query(default=[]),
    table_names: list[str] = Query(default=[]),
    search_ifid: str | None = Query(default=None, max_length=128),
    _: dict = Depends(require_permissions("hrd:read")),
    __: dict = Depends(require_server_access),
) -> dict:
    server = ServerRegistry().require_capability(sid, "hrd")
    rows = HrdService().list_interfaces(
        server, company_codes, table_names, search_ifid
    )
    return {"data": rows, "meta": {"sid": server.sid, "count": len(rows)}}


@router.get("/interfaces/excel")
def export_interfaces(
    sid: str,
    company_codes: list[str] = Query(default=[]),
    table_names: list[str] = Query(default=[]),
    search_ifid: str | None = Query(default=None, max_length=128),
    _: dict = Depends(require_permissions("hrd:read")),
    __: dict = Depends(require_server_access),
):
    server = ServerRegistry().require_capability(sid, "hrd")
    rows = HrdService().list_interfaces(
        server, company_codes, table_names, search_ifid
    )
    return StreamingResponse(
        BytesIO(generate_excel(rows)),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="HRD_Interfaces_{server.sid}.xlsx"'
        },
    )


@router.post("/test-message")
def test_message(
    payload: TestMessageRequest,
    user: dict = Depends(require_permissions("hrd:test")),
) -> dict:
    allowed_sids = user.get("allowed_sids")
    if allowed_sids is not None and payload.sid.upper() not in allowed_sids:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="server access denied")
    server = ServerRegistry().require_capability(payload.sid, "hrd")
    return {"data": HrdService().send_test_message(server, payload.if_id)}
