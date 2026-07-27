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
        "interfaces:read",
    },
    "VIEWER": {
        "monitoring:read", "channels:read", "messages:read", "incidents:read",
        "collectors:read", "interfaces:read",
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
    return {
        "username": str(payload["sub"]),
        "role": role,
        "permissions": permissions_for(role),
    }


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
