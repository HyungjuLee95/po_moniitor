from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings


ROLE_PERMISSIONS: dict[str, set[str]] = {
    "ADMIN": {"*"},
    "OPERATOR": {
        "monitoring:read", "channels:read", "channels:control", "messages:read",
        "incidents:read", "incidents:resolve", "collectors:read", "collectors:run",
        "interfaces:read", "dashboard:read", "dashboard:write", "alerts:read",
        "alerts:acknowledge", "llm-search:read",
        "workspaces:read", "workspaces:write",
        "hrd:read", "hrd:test", "posts:read", "posts:write",
        "oracle-ifs:read", "oracle-ifs:write",
    },
    "VIEWER": {
        "monitoring:read", "channels:read", "messages:read", "incidents:read",
        "collectors:read", "interfaces:read", "dashboard:read", "dashboard:write",
        "alerts:read", "llm-search:read",
        "workspaces:read",
        "hrd:read", "posts:read", "oracle-ifs:read",
    },
}

bearer = HTTPBearer(auto_error=False)


def permissions_for(role: str) -> list[str]:
    return sorted(ROLE_PERMISSIONS.get(role.upper(), set()))


def create_access_token(username: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": username,
            "role": role.upper(),
            "iat": now,
            "exp": now + timedelta(minutes=settings.access_token_minutes),
        },
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="authentication required")
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="invalid or expired token") from exc
    role = str(payload.get("role", "VIEWER")).upper()
    user = {
        "username": str(payload["sub"]),
        "role": role,
        "permissions": permissions_for(role),
    }
    from app.domains.auth.repository import UserRepository
    user["allowed_sids"] = UserRepository().allowed_sids(user["username"], role)
    return user


def require_server_access(
    sid: str,
    user: dict = Depends(current_user),
) -> dict:
    allowed_sids = user.get("allowed_sids")
    if allowed_sids is not None and sid.upper() not in allowed_sids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="server access denied",
        )
    return user


def require_permissions(*required: str):
    def dependency(user: dict = Depends(current_user)) -> dict:
        granted = set(user["permissions"])
        if "*" not in granted and not set(required).issubset(granted):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="permission denied",
            )
        return user

    return dependency
