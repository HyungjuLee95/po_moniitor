from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
from itertools import count
from threading import Lock
from typing import Any

from sqlalchemy import text

from app.core.config import settings
from app.database import session_scope


_demo_lock = Lock()
_demo_ids = count(1)
_demo_rows: dict[str, list[dict[str, Any]]] = {}


def _demo_seed(username: str) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    rows = [
        {
            "workspace_id": next(_demo_ids),
            "task_name": "채널 운영 화면 검증",
            "description": "POQ 채널 조회와 제어 흐름을 확인합니다.",
            "progress": 65,
            "status": "in_progress",
            "target_date": date.today(),
            "created_at": now,
            "updated_at": now,
        },
        {
            "workspace_id": next(_demo_ids),
            "task_name": "Message Audit 운영 절차",
            "description": "Message ID 기준 Audit 로그 확인 절차를 정리합니다.",
            "progress": 30,
            "status": "planned",
            "target_date": None,
            "created_at": now,
            "updated_at": now,
        },
    ]
    _demo_rows[username] = rows
    return rows


def _demo_user_rows(username: str) -> list[dict[str, Any]]:
    return _demo_rows[username] if username in _demo_rows else _demo_seed(username)


class WorkspaceRepository:
    def list(self, username: str) -> list[dict]:
        if settings.demo_mode:
            with _demo_lock:
                return deepcopy(_demo_user_rows(username))
        with session_scope() as session:
            rows = session.execute(
                text(
                    """
                    select w.workspace_id, w.task_name, w.description, w.progress,
                           w.status, w.target_date, w.created_at, w.updated_at
                    from workspace.project_workspace w
                    join iam.app_user u on u.user_id = w.owner_id
                    where u.username = :username
                    order by w.updated_at desc, w.workspace_id desc
                    """
                ),
                {"username": username},
            ).mappings().all()
        return [dict(row) for row in rows]

    def get(self, username: str, workspace_id: int) -> dict | None:
        if settings.demo_mode:
            with _demo_lock:
                rows = _demo_user_rows(username)
                return deepcopy(next(
                    (row for row in rows if row["workspace_id"] == workspace_id),
                    None,
                ))
        with session_scope() as session:
            row = session.execute(
                text(
                    """
                    select w.workspace_id, w.task_name, w.description, w.progress,
                           w.status, w.target_date, w.created_at, w.updated_at
                    from workspace.project_workspace w
                    join iam.app_user u on u.user_id = w.owner_id
                    where u.username = :username and w.workspace_id = :workspace_id
                    """
                ),
                {"username": username, "workspace_id": workspace_id},
            ).mappings().first()
        return dict(row) if row else None

    def create(self, username: str, values: dict) -> dict | None:
        if settings.demo_mode:
            now = datetime.now(timezone.utc)
            row = {
                "workspace_id": next(_demo_ids),
                "status": "planned",
                "created_at": now,
                "updated_at": now,
                **values,
            }
            with _demo_lock:
                _demo_user_rows(username).insert(0, row)
            return deepcopy(row)
        with session_scope() as session:
            row = session.execute(
                text(
                    """
                    insert into workspace.project_workspace (
                        owner_id, task_name, description, progress, target_date
                    )
                    select user_id, :task_name, :description, :progress, :target_date
                    from iam.app_user
                    where username = :username
                    returning workspace_id, task_name, description, progress,
                              status, target_date, created_at, updated_at
                    """
                ),
                {"username": username, **values},
            ).mappings().first()
        return dict(row) if row else None

    def update(self, username: str, workspace_id: int, values: dict) -> dict | None:
        if settings.demo_mode:
            with _demo_lock:
                rows = _demo_user_rows(username)
                row = next(
                    (item for item in rows if item["workspace_id"] == workspace_id),
                    None,
                )
                if row is None:
                    return None
                row.update(values)
                row["updated_at"] = datetime.now(timezone.utc)
                return deepcopy(row)
        with session_scope() as session:
            row = session.execute(
                text(
                    """
                    update workspace.project_workspace w
                    set task_name = :task_name,
                        description = :description,
                        progress = :progress,
                        target_date = :target_date,
                        updated_at = now()
                    from iam.app_user u
                    where w.owner_id = u.user_id
                      and u.username = :username
                      and w.workspace_id = :workspace_id
                    returning w.workspace_id, w.task_name, w.description, w.progress,
                              w.status, w.target_date, w.created_at, w.updated_at
                    """
                ),
                {"username": username, "workspace_id": workspace_id, **values},
            ).mappings().first()
        return dict(row) if row else None

    def advance(
        self,
        username: str,
        workspace_id: int,
        status: str,
        progress: int,
    ) -> dict | None:
        if settings.demo_mode:
            current = self.get(username, workspace_id)
            if current is None:
                return None
            with _demo_lock:
                row = next(
                    item for item in _demo_rows[username]
                    if item["workspace_id"] == workspace_id
                )
                row.update(
                    status=status,
                    progress=progress,
                    updated_at=datetime.now(timezone.utc),
                )
                return deepcopy(row)
        with session_scope() as session:
            row = session.execute(
                text(
                    """
                    update workspace.project_workspace w
                    set status = :status, progress = :progress, updated_at = now()
                    from iam.app_user u
                    where w.owner_id = u.user_id
                      and u.username = :username
                      and w.workspace_id = :workspace_id
                    returning w.workspace_id, w.task_name, w.description, w.progress,
                              w.status, w.target_date, w.created_at, w.updated_at
                    """
                ),
                {
                    "username": username,
                    "workspace_id": workspace_id,
                    "status": status,
                    "progress": progress,
                },
            ).mappings().first()
        return dict(row) if row else None

    def delete(self, username: str, workspace_id: int) -> bool:
        if settings.demo_mode:
            with _demo_lock:
                rows = _demo_user_rows(username)
                original = len(rows)
                _demo_rows[username] = [
                    row for row in rows if row["workspace_id"] != workspace_id
                ]
                return len(_demo_rows[username]) != original
        with session_scope() as session:
            result = session.execute(
                text(
                    """
                    delete from workspace.project_workspace w
                    using iam.app_user u
                    where w.owner_id = u.user_id
                      and u.username = :username
                      and w.workspace_id = :workspace_id
                    """
                ),
                {"username": username, "workspace_id": workspace_id},
            )
        return result.rowcount == 1
