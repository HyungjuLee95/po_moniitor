from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import settings


_engine: Engine | None = None


def engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            future=True,
        )
    return _engine


@contextmanager
def session_scope() -> Iterator[Session]:
    with Session(engine()) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


def check_database() -> None:
    with engine().connect() as connection:
        connection.execute(text("select 1"))
