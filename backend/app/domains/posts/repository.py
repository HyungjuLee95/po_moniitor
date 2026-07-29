from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from itertools import count

from sqlalchemy import text

from app.core.config import settings
from app.database import session_scope


_ids = count(1)
_demo_posts: list[dict] = []


class PostRepository:
    def list(self) -> list[dict]:
        if settings.demo_mode:
            return deepcopy(_demo_posts)
        with session_scope() as session:
            rows = session.execute(
                text(
                    """
                    select post_id, author_username, title, content, category,
                           created_at, updated_at
                    from knowledge.post
                    order by updated_at desc, post_id desc
                    """
                )
            ).mappings().all()
        return [dict(row) for row in rows]

    def create(self, username: str, title: str, content: str, category: str) -> dict:
        if settings.demo_mode:
            now = datetime.now(timezone.utc).isoformat()
            row = {
                "post_id": next(_ids),
                "author_username": username,
                "title": title,
                "content": content,
                "category": category,
                "created_at": now,
                "updated_at": now,
            }
            _demo_posts.insert(0, row)
            return deepcopy(row)
        with session_scope() as session:
            row = session.execute(
                text(
                    """
                    insert into knowledge.post (
                        author_username, title, content, category
                    ) values (:username, :title, :content, :category)
                    returning post_id, author_username, title, content, category,
                              created_at, updated_at
                    """
                ),
                {
                    "username": username,
                    "title": title,
                    "content": content,
                    "category": category,
                },
            ).mappings().one()
        return dict(row)

    def update(
        self,
        post_id: int,
        username: str,
        is_admin: bool,
        title: str,
        content: str,
        category: str,
    ) -> dict:
        if settings.demo_mode:
            for row in _demo_posts:
                if row["post_id"] == post_id:
                    if not is_admin and row["author_username"] != username:
                        raise PermissionError
                    row.update(
                        title=title,
                        content=content,
                        category=category,
                        updated_at=datetime.now(timezone.utc).isoformat(),
                    )
                    return deepcopy(row)
            raise LookupError
        with session_scope() as session:
            existing = session.execute(
                text("select author_username from knowledge.post where post_id = :post_id"),
                {"post_id": post_id},
            ).scalar_one_or_none()
            if existing is None:
                raise LookupError
            if not is_admin and existing != username:
                raise PermissionError
            row = session.execute(
                text(
                    """
                    update knowledge.post
                    set title = :title, content = :content, category = :category,
                        updated_at = now()
                    where post_id = :post_id
                    returning post_id, author_username, title, content, category,
                              created_at, updated_at
                    """
                ),
                {
                    "post_id": post_id,
                    "title": title,
                    "content": content,
                    "category": category,
                },
            ).mappings().one()
        return dict(row)

    def delete(self, post_id: int, username: str, is_admin: bool) -> None:
        if settings.demo_mode:
            for index, row in enumerate(_demo_posts):
                if row["post_id"] == post_id:
                    if not is_admin and row["author_username"] != username:
                        raise PermissionError
                    _demo_posts.pop(index)
                    return
            raise LookupError
        with session_scope() as session:
            existing = session.execute(
                text("select author_username from knowledge.post where post_id = :post_id"),
                {"post_id": post_id},
            ).scalar_one_or_none()
            if existing is None:
                raise LookupError
            if not is_admin and existing != username:
                raise PermissionError
            session.execute(
                text("delete from knowledge.post where post_id = :post_id"),
                {"post_id": post_id},
            )
