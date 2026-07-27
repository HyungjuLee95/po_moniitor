from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from typing import Any, Iterator

from app.core.config import settings


class RtimsError(RuntimeError):
    """Sanitized RTIMS Oracle error."""


@lru_cache(maxsize=1)
def pool():
    if not settings.rtims_configured:
        raise RtimsError("RTIMS Oracle connection is not fully configured")
    try:
        import oracledb

        return oracledb.create_pool(
            user=settings.rtims_oracle_user,
            password=settings.rtims_oracle_password.get_secret_value(),
            dsn=oracledb.makedsn(
                settings.rtims_oracle_host,
                settings.rtims_oracle_port,
                service_name=settings.rtims_oracle_service,
            ),
            min=settings.rtims_pool_min,
            max=settings.rtims_pool_max,
            increment=1,
        )
    except Exception as exc:
        raise RtimsError("failed to initialize RTIMS Oracle pool") from exc


@contextmanager
def connection() -> Iterator[Any]:
    try:
        with pool().acquire() as value:
            yield value
    except RtimsError:
        raise
    except Exception as exc:
        raise RtimsError("RTIMS Oracle operation failed") from exc


def _rows(cursor) -> list[dict]:
    columns = [item[0].lower() for item in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


class RtimsRepository:
    def check(self) -> None:
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("select 1 from dual")
                cursor.fetchone()

    def dashboard_summary(self, sid: str, hours: int = 24) -> dict:
        sql = """
            select
                nvl(sum(s.count), 0) as total_count,
                nvl(sum(case when s.msg_status = 'S' then s.count else 0 end), 0) as success_count,
                nvl(sum(case when s.msg_status = 'F' then s.count else 0 end), 0) as fail_count,
                nvl(sum(case when s.msg_status = 'P' then s.count else 0 end), 0) as pending_count,
                nvl(
                    sum(s.latency) / nullif(sum(s.count), 0),
                    0
                ) as average_latency_ms
            from mon_daily_statistics s
            join mon_intf_map m on m.intf_map_id = s.intf_map_id
            where upper(m.server_id) = upper(:sid)
              and to_date(s.ymdd || lpad(s.hour, 2, '0'), 'YYYYMMDDHH24')
                  >= sysdate - (:hours / 24)
        """
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, {"sid": sid, "hours": hours})
                row = _rows(cursor)[0]
        total = int(row["total_count"] or 0)
        success = int(row["success_count"] or 0)
        fail = int(row["fail_count"] or 0)
        pending = int(row["pending_count"] or 0)
        return {
            "total": total,
            "success": success,
            "fail": fail,
            "pending": pending,
            "success_rate": round(success / total * 100, 2) if total else 0.0,
            "average_latency_ms": round(float(row["average_latency_ms"] or 0)),
        }

    def channel_summary(self, sid: str) -> dict[str, int]:
        sql = """
            select upper(trim(state)) as state, count(*) as count
            from mon_channinfo
            where upper(server_id) = upper(:sid)
            group by upper(trim(state))
        """
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, {"sid": sid})
                rows = _rows(cursor)
        return {str(row["state"] or "UNKNOWN"): int(row["count"]) for row in rows}

    def recent_messages(
        self,
        sid: str,
        limit: int,
        offset: int = 0,
        hours: int = 24,
    ) -> list[dict]:
        sql = """
            select
                msgid,
                msgstatus,
                server_id,
                from_service_name,
                to_service_name,
                sent_recv_time,
                tran_delv_time,
                error_code,
                error_category,
                bytes_length
            from mon_buf_aae_msg
            where upper(server_id) = upper(:sid)
              and sent_recv_time >= systimestamp - numtodsinterval(:hours, 'HOUR')
            order by sent_recv_time desc
            offset :offset rows fetch next :limit rows only
        """
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    sql,
                    {"sid": sid, "hours": hours, "offset": offset, "limit": limit},
                )
                rows = _rows(cursor)
        return [
            {
                "message_id": row["msgid"],
                "sid": row["server_id"],
                "interface_name": (
                    row["to_service_name"] or row["from_service_name"] or ""
                ),
                "status": row["msgstatus"],
                "start_time": (
                    row["sent_recv_time"].isoformat()
                    if row["sent_recv_time"] else None
                ),
                "end_time": (
                    row["tran_delv_time"].isoformat()
                    if row["tran_delv_time"] else None
                ),
                "duration_ms": None,
                "source_system": row["from_service_name"],
                "target_system": row["to_service_name"],
                "error_text": row["error_category"] or row["error_code"],
                "size_bytes": row["bytes_length"],
            }
            for row in rows
        ]

    def incidents(
        self,
        sid: str,
        limit: int = 100,
        offset: int = 0,
        hours: int = 24,
    ) -> list[dict]:
        sql = """
            select *
            from (
                select
                    error_log_id,
                    msgguid,
                    server_id,
                    ob_intf_nm,
                    category_nm,
                    error_text,
                    error_state,
                    first_seen_at,
                    last_seen_at
                from mon_inci_log
                where upper(server_id) = upper(:sid)
                  and last_seen_at >= systimestamp - numtodsinterval(:hours, 'HOUR')
                order by last_seen_at desc
            )
            offset :offset rows fetch next :limit rows only
        """
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    sql,
                    {"sid": sid, "hours": hours, "offset": offset, "limit": limit},
                )
                return _rows(cursor)

    def resolve_incident(
        self,
        error_log_id: int,
        username: str,
        message: str | None,
    ) -> None:
        sql = """
            update mon_inci_log
            set error_state = 'C',
                proc_message = :message,
                user_id = :username
            where error_log_id = :error_log_id
        """
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    sql,
                    {
                        "message": message,
                        "username": username,
                        "error_log_id": error_log_id,
                    },
                )
                if cursor.rowcount != 1:
                    raise RtimsError("RTIMS incident was not found")
            conn.commit()
