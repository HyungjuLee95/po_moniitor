from __future__ import annotations

import json
from datetime import datetime, timezone
from threading import Lock

from sqlalchemy import text

from app.core.config import PoServer, settings
from app.database import session_scope


_demo_lock = Lock()
_demo_checkpoints: dict[str, dict] = {}


class CollectorRepository:
    def list(self, servers: list[PoServer]) -> list[dict]:
        if settings.demo_mode:
            with _demo_lock:
                return [
                    {
                        "sid": server.sid,
                        "server_name": server.display_name,
                        "status": _demo_checkpoints.get(server.sid, {}).get("status", "READY"),
                        "last_success_at": _demo_checkpoints.get(server.sid, {}).get("last_success_at"),
                        "last_window_end": _demo_checkpoints.get(server.sid, {}).get("last_window_end"),
                        "item_count": _demo_checkpoints.get(server.sid, {}).get("item_count", 0),
                        "elapsed_ms": _demo_checkpoints.get(server.sid, {}).get("elapsed_ms", 0),
                        "detail": _demo_checkpoints.get(server.sid, {}).get("detail"),
                    }
                    for server in servers
                ]

        sids = [server.sid for server in servers]
        with session_scope() as session:
            rows = session.execute(
                text(
                    """
                    select sid, last_window_end, last_success_at, status,
                           item_count, elapsed_ms, detail
                    from monitoring.collector_checkpoint
                    where sid = any(:sids)
                    """
                ),
                {"sids": sids},
            ).mappings().all()
        checkpoints = {row["sid"]: dict(row) for row in rows}
        return [
            {
                "sid": server.sid,
                "server_name": server.display_name,
                "status": checkpoints.get(server.sid, {}).get("status", "READY"),
                "last_success_at": checkpoints.get(server.sid, {}).get("last_success_at"),
                "last_window_end": checkpoints.get(server.sid, {}).get("last_window_end"),
                "item_count": checkpoints.get(server.sid, {}).get("item_count", 0),
                "elapsed_ms": checkpoints.get(server.sid, {}).get("elapsed_ms", 0),
                "detail": checkpoints.get(server.sid, {}).get("detail"),
            }
            for server in servers
        ]

    def save(
        self,
        server: PoServer,
        status: str,
        item_count: int,
        elapsed_ms: int,
        detail: str | None = None,
    ) -> None:
        now = datetime.now(timezone.utc)
        if settings.demo_mode:
            with _demo_lock:
                _demo_checkpoints[server.sid] = {
                    "status": status,
                    "last_window_end": now,
                    "last_success_at": now if status == "SUCCESS" else None,
                    "item_count": item_count,
                    "elapsed_ms": elapsed_ms,
                    "detail": detail,
                }
            return
        with session_scope() as session:
            session.execute(
                text(
                    """
                    insert into configuration.po_server (
                        sid, display_name, environment, base_url, port,
                        capabilities, enabled
                    ) values (
                        :sid, :display_name, :environment, :base_url, :port,
                        cast(:capabilities as jsonb), true
                    )
                    on conflict (sid) do update
                    set display_name = excluded.display_name,
                        environment = excluded.environment,
                        base_url = excluded.base_url,
                        port = excluded.port,
                        capabilities = excluded.capabilities,
                        enabled = true,
                        updated_at = now()
                    """
                ),
                {
                    "sid": server.sid,
                    "display_name": server.display_name,
                    "environment": server.environment,
                    "base_url": server.origin,
                    "port": server.port,
                    "capabilities": json.dumps(server.capabilities),
                },
            )
            session.execute(
                text(
                    """
                    insert into monitoring.collector_checkpoint (
                        sid, last_window_end, last_success_at, status,
                        item_count, elapsed_ms, detail
                    ) values (
                        :sid, :now, case when :status = 'SUCCESS' then :now else null end,
                        :status, :item_count, :elapsed_ms, :detail
                    )
                    on conflict (sid) do update
                    set last_window_end = excluded.last_window_end,
                        last_success_at = case
                            when excluded.status = 'SUCCESS' then excluded.last_success_at
                            else monitoring.collector_checkpoint.last_success_at
                        end,
                        status = excluded.status,
                        item_count = excluded.item_count,
                        elapsed_ms = excluded.elapsed_ms,
                        detail = excluded.detail
                    """
                ),
                {
                    "sid": server.sid,
                    "now": now,
                    "status": status,
                    "item_count": item_count,
                    "elapsed_ms": elapsed_ms,
                    "detail": detail,
                },
            )
