import re

from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.security import (
    create_access_token,
    current_user,
    permissions_for,
    require_permissions,
)
from app.domains.auth.repository import UserRepository
from app.domains.configuration.registry import ServerRegistry


router = APIRouter(prefix="/auth", tags=["Auth"])
USERNAME_PATTERN = re.compile(r"^[a-z0-9._-]{3,64}$")


class UserCreate(BaseModel):
    username: str
    display_name: str = Field(min_length=1, max_length=100)
    temporary_password: str = Field(min_length=8, max_length=128)
    role: str
    server_sids: list[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)
    role: str
    active: bool
    server_sids: list[str] = Field(default_factory=list)


class PasswordReset(BaseModel):
    temporary_password: str = Field(min_length=8, max_length=128)


def validate_role_and_servers(role: str, server_sids: list[str]) -> tuple[str, list[str]]:
    normalized_role = role.upper()
    if normalized_role not in {"ADMIN", "OPERATOR", "VIEWER"}:
        raise HTTPException(status_code=422, detail="invalid role")
    normalized_sids = sorted({sid.upper() for sid in server_sids})
    available = {server.sid for server in ServerRegistry().list_enabled()}
    if not set(normalized_sids).issubset(available):
        raise HTTPException(status_code=422, detail="unknown server SID")
    return normalized_role, normalized_sids


@router.post("/login")
def login(username: str = Form(...), password: str = Form(...)) -> dict:
    user = UserRepository().authenticate(username.strip(), password)
    if user is None:
        raise HTTPException(status_code=401, detail="invalid username or password")
    role = user["role"]
    return {
        "access_token": create_access_token(user["username"], role),
        "token_type": "bearer",
        "user": {
            "username": user["username"],
            "display_name": user["display_name"],
            "role": role,
            "permissions": permissions_for(role),
        },
    }


@router.get("/me")
def me(user: dict = Depends(current_user)) -> dict:
    return {
        **user,
        "display_name": (
            "Demo Administrator"
            if settings.demo_mode and user["username"] == settings.demo_admin_username
            else user["username"]
        ),
    }


@router.get("/users")
def list_users(
    _: dict = Depends(require_permissions("users:manage")),
) -> dict:
    return {"data": UserRepository().list_users()}


@router.post("/users", status_code=201)
def create_user(
    payload: UserCreate,
    actor: dict = Depends(require_permissions("users:manage")),
) -> dict:
    username = payload.username.strip().lower()
    if not USERNAME_PATTERN.fullmatch(username):
        raise HTTPException(status_code=422, detail="invalid username")
    role, server_sids = validate_role_and_servers(payload.role, payload.server_sids)
    try:
        row = UserRepository().create_user(
            username,
            payload.display_name.strip(),
            payload.temporary_password,
            role,
            server_sids,
            actor["username"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"data": row}


@router.put("/users/{username}")
def update_user(
    username: str,
    payload: UserUpdate,
    actor: dict = Depends(require_permissions("users:manage")),
) -> dict:
    normalized = username.strip().lower()
    if normalized == actor["username"] and not payload.active:
        raise HTTPException(status_code=409, detail="cannot deactivate the current user")
    role, server_sids = validate_role_and_servers(payload.role, payload.server_sids)
    try:
        row = UserRepository().update_user(
            normalized,
            payload.display_name.strip(),
            role,
            payload.active,
            server_sids,
            actor["username"],
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"data": row}


@router.post("/users/{username}/reset-password", status_code=204)
def reset_password(
    username: str,
    payload: PasswordReset,
    actor: dict = Depends(require_permissions("users:manage")),
) -> None:
    try:
        UserRepository().reset_password(
            username.strip().lower(),
            payload.temporary_password,
            actor["username"],
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
