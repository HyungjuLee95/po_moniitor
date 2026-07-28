from __future__ import annotations

from sqlalchemy import text

from app.core.config import settings
from app.database import session_scope


DEFAULT_POLICY = {
    "response_window_minutes": 15,
    "slow_threshold_ms": 3000,
    "critical_threshold_ms": 10000,
    "max_detail_rows": 100,
}
_demo_policies: dict[str, dict] = {}


class MonitoringPolicyRepository:
    def get(self, sid: str) -> dict:
        normalized = sid.upper()
        if settings.demo_mode:
            return {"sid": normalized, **_demo_policies.get(normalized, DEFAULT_POLICY)}

        with session_scope() as session:
            row = session.execute(
                text(
                    """
                    select sid, response_window_minutes, slow_threshold_ms,
                           critical_threshold_ms, max_detail_rows, updated_by, updated_at
                    from configuration.monitoring_policy
                    where sid = :sid
                    """
                ),
                {"sid": normalized},
            ).mappings().first()
        return dict(row) if row else {"sid": normalized, **DEFAULT_POLICY}

    def save(self, sid: str, values: dict, username: str) -> dict:
        normalized = sid.upper()
        payload = {**DEFAULT_POLICY, **values}
        if settings.demo_mode:
            _demo_policies[normalized] = payload
            return {"sid": normalized, **payload, "updated_by": username}

        with session_scope() as session:
            row = session.execute(
                text(
                    """
                    insert into configuration.monitoring_policy (
                        sid, response_window_minutes, slow_threshold_ms,
                        critical_threshold_ms, max_detail_rows, updated_by
                    ) values (
                        :sid, :response_window_minutes, :slow_threshold_ms,
                        :critical_threshold_ms, :max_detail_rows, :updated_by
                    )
                    on conflict (sid) do update set
                        response_window_minutes = excluded.response_window_minutes,
                        slow_threshold_ms = excluded.slow_threshold_ms,
                        critical_threshold_ms = excluded.critical_threshold_ms,
                        max_detail_rows = excluded.max_detail_rows,
                        updated_by = excluded.updated_by,
                        updated_at = now()
                    returning sid, response_window_minutes, slow_threshold_ms,
                              critical_threshold_ms, max_detail_rows, updated_by, updated_at
                    """
                ),
                {"sid": normalized, **payload, "updated_by": username},
            ).mappings().one()
        return dict(row)
