from fastapi import APIRouter, Depends, Form, HTTPException

from app.core.config import settings
from app.core.security import (
    create_access_token,
    current_user,
    permissions_for,
)
from app.domains.auth.repository import UserRepository


router = APIRouter(prefix="/auth", tags=["Auth"])


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
