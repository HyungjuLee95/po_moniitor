from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.security import ROLE_PERMISSIONS, current_user
from app.domains.configuration.registry import ServerRegistry


router = APIRouter(prefix="/configuration", tags=["Configuration"])


@router.get("/bootstrap")
def bootstrap(user: dict = Depends(current_user)) -> dict:
    return {
        "application": {
            "name": settings.app_name,
            "version": settings.app_version,
            "mode": "demo" if settings.demo_mode else "live",
        },
        "current_user": user,
        "servers": [
            server.public_view()
            for server in ServerRegistry().list_enabled()
        ],
        "roles": {
            role: sorted(permissions)
            for role, permissions in ROLE_PERMISSIONS.items()
        },
    }
