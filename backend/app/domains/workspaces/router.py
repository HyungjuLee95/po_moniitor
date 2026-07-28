from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from app.core.security import require_permissions
from app.domains.workspaces.repository import WorkspaceRepository
from app.domains.workspaces.service import WorkspaceService


router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


class WorkspaceWrite(BaseModel):
    task_name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    progress: int = Field(default=0, ge=0, le=100)
    target_date: date | None = None


@router.get("")
def list_workspaces(
    user: dict = Depends(require_permissions("workspaces:read")),
) -> dict:
    rows = WorkspaceRepository().list(user["username"])
    return {"data": rows, "meta": {"count": len(rows)}}


@router.post("", status_code=201)
def create_workspace(
    payload: WorkspaceWrite,
    user: dict = Depends(require_permissions("workspaces:write")),
) -> dict:
    row = WorkspaceRepository().create(user["username"], payload.model_dump())
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")
    return {"data": row}


@router.get("/{workspace_id}")
def get_workspace(
    workspace_id: int,
    user: dict = Depends(require_permissions("workspaces:read")),
) -> dict:
    row = WorkspaceRepository().get(user["username"], workspace_id)
    if row is None:
        raise HTTPException(status_code=404, detail="workspace not found")
    return {"data": row}


@router.put("/{workspace_id}")
def update_workspace(
    workspace_id: int,
    payload: WorkspaceWrite,
    user: dict = Depends(require_permissions("workspaces:write")),
) -> dict:
    row = WorkspaceRepository().update(
        user["username"], workspace_id, payload.model_dump()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="workspace not found")
    return {"data": row}


@router.delete("/{workspace_id}", status_code=204)
def delete_workspace(
    workspace_id: int,
    user: dict = Depends(require_permissions("workspaces:write")),
) -> Response:
    if not WorkspaceRepository().delete(user["username"], workspace_id):
        raise HTTPException(status_code=404, detail="workspace not found")
    return Response(status_code=204)


@router.post("/{workspace_id}/move-to-next-step")
def move_to_next_step(
    workspace_id: int,
    user: dict = Depends(require_permissions("workspaces:write")),
) -> dict:
    row = WorkspaceService().advance(user["username"], workspace_id)
    if row is None:
        raise HTTPException(status_code=404, detail="workspace not found")
    return {"data": row}
