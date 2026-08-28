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


class RegistrationRequest(BaseModel):
    username: str
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)
    role: str
    active: bool
    server_sids: list[str] = Field(default_factory=list)


class PasswordReset(BaseModel):
    temporary_password: str = Field(min_length=8, max_length=128)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPassword(BaseModel):
    username: str = Field(min_length=3, max_length=64)


class TokenPasswordReset(BaseModel):
    token: str = Field(min_length=20, max_length=256)
    new_password: str = Field(min_length=8, max_length=128)


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


@router.post("/register", status_code=202)
def register(payload: RegistrationRequest) -> dict:
    username = payload.username.strip().lower()
    display_name = payload.display_name.strip()
    if not USERNAME_PATTERN.fullmatch(username):
        raise HTTPException(status_code=422, detail="invalid username")
    if not display_name:
        raise HTTPException(status_code=422, detail="invalid display name")
    try:
        UserRepository().register_user(
            username,
            display_name,
            payload.password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "data": {
            "accepted": True,
            "status": "pending",
            "role": "VIEWER",
            "message": "Administrator approval is required before login.",
        }
    }


@router.get("/me")
def me(user: dict = Depends(current_user)) -> dict:
    profile = UserRepository().get_user(user["username"])
    return {
        **user,
        "display_name": profile["display_name"],
    }


@router.post("/change-password", status_code=204)
def change_password(
    payload: PasswordChange,
    user: dict = Depends(current_user),
) -> None:
    try:
        UserRepository().change_password(
            user["username"],
            payload.current_password,
            payload.new_password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/forgot-password", status_code=202)
def forgot_password(payload: ForgotPassword) -> dict:
    UserRepository().request_password_reset(payload.username.strip().lower())
    return {
        "data": {
            "accepted": True,
            "message": "계정이 존재하면 관리자 승인 목록에 등록됩니다.",
        }
    }


@router.post("/reset-password", status_code=204)
def reset_password_with_token(payload: TokenPasswordReset) -> None:
    try:
        UserRepository().consume_password_reset(payload.token, payload.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
    if role == "ADMIN":
        raise HTTPException(
            status_code=409,
            detail="additional administrator accounts are not allowed",
        )
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
    role, server_sids = validate_role_and_servers(payload.role, payload.server_sids)
    administrator = settings.demo_admin_username.strip().lower()
    if normalized == administrator and (role != "ADMIN" or not payload.active):
        raise HTTPException(
            status_code=409,
            detail="the Administrator account must remain active with the ADMIN role",
        )
    if normalized != administrator and role == "ADMIN":
        raise HTTPException(
            status_code=409,
            detail="additional administrator accounts are not allowed",
        )
    if normalized == actor["username"] and not payload.active:
        raise HTTPException(status_code=409, detail="cannot deactivate the current user")
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


@router.get("/password-reset-requests")
def password_reset_requests(
    _: dict = Depends(require_permissions("users:manage")),
) -> dict:
    rows = UserRepository().list_password_reset_requests()
    return {"data": rows, "meta": {"count": len(rows)}}


@router.post("/password-reset-requests/{request_id}/issue-token")
def issue_password_reset_token(
    request_id: int,
    _: dict = Depends(require_permissions("users:manage")),
) -> dict:
    try:
        token = UserRepository().issue_password_reset_token(request_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "data": {
            "request_id": request_id,
            "token": token,
            "expires_in_minutes": 30,
        }
    }
