from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text

from app.core.config import settings
from app.core.security import require_permissions
from app.database import session_scope


WidgetId = Literal[
    "health",
    "throughput",
    "channel_status",
    "incidents",
    "server_profile",
]
ALL_WIDGETS = [
    "health",
    "throughput",
    "channel_status",
    "incidents",
    "server_profile",
]


class DashboardLayout(BaseModel):
    order: list[WidgetId] = Field(default_factory=lambda: list(ALL_WIDGETS))
    hidden: list[WidgetId] = Field(default_factory=list)
    density: Literal["comfortable", "compact"] = "comfortable"

    @model_validator(mode="after")
    def validate_widgets(self) -> "DashboardLayout":
        if len(self.order) != len(set(self.order)):
            raise ValueError("widget order contains duplicates")
        if set(self.order) != set(ALL_WIDGETS):
            raise ValueError("widget order must contain every registered widget")
        if not set(self.hidden).issubset(set(self.order)):
            raise ValueError("hidden widget is not registered")
        return self


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
_demo_preferences: dict[str, DashboardLayout] = {}


@router.get("/preferences")
def get_preferences(
    user: dict = Depends(require_permissions("dashboard:read")),
) -> dict:
    if settings.demo_mode:
        return {"data": _demo_preferences.get(user["username"], DashboardLayout())}

    with session_scope() as session:
        layout = session.execute(
            text(
                """
                select p.layout
                from iam.dashboard_preference p
                join iam.app_user u on u.user_id = p.user_id
                where u.username = :username
                """
            ),
            {"username": user["username"]},
        ).scalar_one_or_none()
    return {"data": DashboardLayout.model_validate(layout or {})}


@router.put("/preferences")
def save_preferences(
    layout: DashboardLayout,
    user: dict = Depends(require_permissions("dashboard:write")),
) -> dict:
    if settings.demo_mode:
        _demo_preferences[user["username"]] = layout
        return {"data": layout, "storage": "demo-memory"}

    with session_scope() as session:
        result = session.execute(
            text(
                """
                insert into iam.dashboard_preference (user_id, layout)
                select user_id, cast(:layout as jsonb)
                from iam.app_user
                where username = :username
                on conflict (user_id)
                do update set layout = excluded.layout, updated_at = now()
                """
            ),
            {"username": user["username"], "layout": json.dumps(layout.model_dump())},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="user not found")
    return {"data": layout, "storage": "postgresql"}
