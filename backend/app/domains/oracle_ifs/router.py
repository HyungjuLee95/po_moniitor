from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import require_permissions
from app.domains.oracle_ifs.service import OracleIfsService


router = APIRouter(prefix="/oracle-ifs", tags=["Oracle IFS"])


class TargetDateUpdate(BaseModel):
    target_date: date | None = None


@router.get("/interfaces")
def list_interfaces(
    user: dict = Depends(require_permissions("oracle-ifs:read")),
) -> dict:
    rows = OracleIfsService().list_rows(
        user["username"],
        user["role"] == "ADMIN",
    )
    return {"data": rows, "meta": {"count": len(rows)}}


@router.post("/sync")
def sync(
    _: dict = Depends(require_permissions("oracle-ifs:sync")),
) -> dict:
    return {"data": OracleIfsService().sync()}


@router.put("/target-date/{req_seq}")
def update_target_date(
    req_seq: str,
    payload: TargetDateUpdate,
    _: dict = Depends(require_permissions("oracle-ifs:write")),
) -> dict:
    try:
        return {"data": OracleIfsService().update_target_date(req_seq, payload.target_date)}
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
