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

    def dashboard_summary(self, sid: str, response_window_minutes: int = 15) -> dict:
        sql = """
            select
                nvl(sum(s.count), 0) as total_count,
                nvl(sum(case when s.msg_status = 'S' then s.count else 0 end), 0) as success_count,
                nvl(sum(case when s.msg_status = 'F' then s.count else 0 end), 0) as fail_count,
                nvl(sum(case when s.msg_status = 'P' then s.count else 0 end), 0) as pending_count
            from mon_daily_statistics s
            join mon_intf_map m on m.intf_map_id = s.intf_map_id
            where upper(m.server_id) = upper(:sid)
              and s.ymdd = to_char(sysdate, 'YYYYMMDD')
        """
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, {"sid": sid})
                row = _rows(cursor)[0]
                cursor.execute(
                    """
                    select nvl(
                        avg(
                            nvl(req_elapsed_sec, 0)
                            + nvl(prov_elapsed_sec, 0)
                            + nvl(res_elapsed_sec, 0)
                        ) * 1000,
                        0
                    ) as average_latency_ms
                    from mon_msg_log
                    where upper(server_id) = upper(:sid)
                      and req_start_dtm >= systimestamp
                          - numtodsinterval(:window_minutes, 'MINUTE')
                    """,
                    {"sid": sid, "window_minutes": response_window_minutes},
                )
                latency_row = _rows(cursor)[0]
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
            "average_latency_ms": round(float(latency_row["average_latency_ms"] or 0)),
        }

    def slow_messages(
        self,
        sid: str,
        window_minutes: int,
        threshold_ms: int,
        limit: int,
    ) -> list[dict]:
        sql = """
            select
                l.log_id,
                l.msg_id as message_id,
                l.msg_status as status,
                l.req_start_dtm as start_time,
                (
                    nvl(l.req_elapsed_sec, 0)
                    + nvl(l.prov_elapsed_sec, 0)
                    + nvl(l.res_elapsed_sec, 0)
                ) as elapsed_sec,
                m.ob_intf_nm as interface_name,
                m.ob_system as source_system,
                m.ib_system as target_system
            from mon_msg_log l
            left join mon_intf_map m on m.intf_map_id = l.intf_map_id
            where upper(l.server_id) = upper(:sid)
              and l.req_start_dtm >= systimestamp
                  - numtodsinterval(:window_minutes, 'MINUTE')
              and (
                    nvl(l.req_elapsed_sec, 0)
                    + nvl(l.prov_elapsed_sec, 0)
                    + nvl(l.res_elapsed_sec, 0)
                  ) * 1000 >= :threshold_ms
            order by elapsed_sec desc, l.req_start_dtm desc
            fetch first :limit rows only
        """
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    sql,
                    {
                        "sid": sid,
                        "window_minutes": window_minutes,
                        "threshold_ms": threshold_ms,
                        "limit": limit,
                    },
                )
                rows = _rows(cursor)
        for row in rows:
            if row.get("start_time") is not None:
                row["start_time"] = row["start_time"].isoformat()
            row["elapsed_sec"] = round(float(row.get("elapsed_sec") or 0), 3)
        return rows

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

    def channel_statistics(self, sid: str, channel_name: str) -> dict:
        sql = """
            select
                count(*) as total_count,
                sum(case when l.msg_status = 'S' then 1 else 0 end) as success_count,
                sum(case when l.msg_status = 'F' then 1 else 0 end) as fail_count,
                sum(case when l.msg_status = 'P' then 1 else 0 end) as pending_count,
                avg(
                    nvl(l.req_elapsed_sec, 0)
                    + nvl(l.prov_elapsed_sec, 0)
                    + nvl(l.res_elapsed_sec, 0)
                ) as avg_elapsed_sec,
                sum(nvl(l.req_msg_size, 0) + nvl(l.res_msg_size, 0)) as total_msg_size,
                avg(nvl(l.req_msg_size, 0) + nvl(l.res_msg_size, 0)) as avg_msg_size
            from mon_msg_log l
            where upper(l.server_id) = upper(:sid)
              and l.req_start_dtm >= trunc(sysdate)
              and l.intf_map_id in (
                  select m.intf_map_id
                  from mon_intf_map m
                  where upper(m.server_id) = upper(:sid)
                    and (
                        upper(m.ob_intf_nm) = upper(:channel_name)
                        or upper(m.ib_intf_nm) = upper(:channel_name)
                    )
              )
        """
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, {"sid": sid, "channel_name": channel_name})
                row = _rows(cursor)[0]
        return {
            "total_count": int(row["total_count"] or 0),
            "success_count": int(row["success_count"] or 0),
            "fail_count": int(row["fail_count"] or 0),
            "pending_count": int(row["pending_count"] or 0),
            "avg_elapsed_sec": round(float(row["avg_elapsed_sec"] or 0), 3),
            "total_msg_size": int(row["total_msg_size"] or 0),
            "avg_msg_size": round(float(row["avg_msg_size"] or 0), 1),
        }

    def channel_messages(
        self,
        sid: str,
        channel_name: str,
        limit: int,
        offset: int,
    ) -> list[dict]:
        sql = """
            select
                l.log_id,
                l.msg_id as message_id,
                l.msg_status as status,
                l.server_id,
                l.req_start_dtm as start_time,
                (
                    nvl(l.req_elapsed_sec, 0)
                    + nvl(l.prov_elapsed_sec, 0)
                    + nvl(l.res_elapsed_sec, 0)
                ) as elapsed_sec,
                (nvl(l.req_msg_size, 0) + nvl(l.res_msg_size, 0)) as msg_size
            from mon_msg_log l
            where upper(l.server_id) = upper(:sid)
              and l.req_start_dtm >= trunc(sysdate)
              and l.intf_map_id in (
                  select m.intf_map_id
                  from mon_intf_map m
                  where upper(m.server_id) = upper(:sid)
                    and (
                        upper(m.ob_intf_nm) = upper(:channel_name)
                        or upper(m.ib_intf_nm) = upper(:channel_name)
                    )
              )
            order by l.req_start_dtm desc, l.log_id desc
            offset :offset rows fetch next :limit rows only
        """
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    sql,
                    {
                        "sid": sid,
                        "channel_name": channel_name,
                        "limit": limit,
                        "offset": offset,
                    },
                )
                rows = _rows(cursor)
        for row in rows:
            if row.get("start_time") is not None:
                row["start_time"] = row["start_time"].isoformat()
            row["elapsed_sec"] = round(float(row.get("elapsed_sec") or 0), 3)
        return rows

    def interface_performance(self, sid: str, hours: int = 24) -> list[dict]:
        sql = """
            select
                m.ob_intf_nm as interface_name,
                m.ob_system as source_system,
                m.ib_system as target_system,
                sum(s.count) as total_count,
                sum(case when s.msg_status = 'S' then s.count else 0 end) as success_count,
                sum(case when s.msg_status = 'F' then s.count else 0 end) as fail_count,
                sum(case when s.msg_status = 'P' then s.count else 0 end) as pending_count,
                sum(s.latency) / nullif(sum(s.count), 0) as avg_latency_ms,
                max(s.max_latency) as max_latency_ms
            from mon_daily_statistics s
            join mon_intf_map m on m.intf_map_id = s.intf_map_id
            where upper(m.server_id) = upper(:sid)
              and to_date(s.ymdd || lpad(s.hour, 2, '0'), 'YYYYMMDDHH24')
                  >= sysdate - (:hours / 24)
            group by m.ob_intf_nm, m.ob_system, m.ib_system
            order by fail_count desc, total_count desc
            fetch first 100 rows only
        """
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, {"sid": sid, "hours": hours})
                rows = _rows(cursor)
        for row in rows:
            total = int(row.get("total_count") or 0)
            success = int(row.get("success_count") or 0)
            row["total_count"] = total
            row["success_count"] = success
            row["fail_count"] = int(row.get("fail_count") or 0)
            row["pending_count"] = int(row.get("pending_count") or 0)
            row["success_rate"] = round(success / total * 100, 2) if total else 0.0
            row["avg_latency_ms"] = round(float(row.get("avg_latency_ms") or 0), 1)
            row["max_latency_ms"] = round(float(row.get("max_latency_ms") or 0), 1)
        return rows

    def resource_summary(self, sid: str) -> list[dict]:
        sql = """
            select server_id, resource_id, resource_type, resource_name, node,
                   recent_usage, max_usage, max_limit
            from (
                select u.server_id, u.resource_id, r.type as resource_type,
                       r.resourcenm as resource_name, u.node, u.recent_usage,
                       u.max_usage, u.max_limit,
                       row_number() over (
                           partition by u.server_id, u.resource_id, u.node
                           order by u.ymdd desc, u.minute_day desc
                       ) as rn
                from mon_res_usage u
                join mon_resource r on r.resource_id = u.resource_id
                where upper(u.server_id) = upper(:sid)
            )
            where rn = 1
            order by resource_type, resource_name, node
        """
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, {"sid": sid})
                return _rows(cursor)

    def queue_summary(self, sid: str) -> dict:
        ae_sql = """
            select servernode, queuename, conname, started, num_entries,
                   threads_assigned, threads_working, max_thread
            from mon_ae_queue
            where upper(server_id) = upper(:sid)
            order by num_entries desc, servernode, queuename
        """
        status_sql = """
            select client_id, direction,
                   sum(case when severity = 'N' then msg_count else 0 end) as normal,
                   sum(case when severity = 'W' then msg_count else 0 end) as warning,
                   sum(case when severity = 'F' then msg_count else 0 end) as fail
            from mon_q_status
            where upper(server_id) = upper(:sid)
            group by client_id, direction
            order by client_id, direction
        """
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(ae_sql, {"sid": sid})
                ae_rows = _rows(cursor)
                cursor.execute(status_sql, {"sid": sid})
                status_rows = _rows(cursor)
        return {"adapter_engine": ae_rows, "integration_engine": status_rows}

    def topology(self, sid: str) -> list[dict]:
        sql = """
            select distinct
                ob_system as source_system,
                ib_system as target_system,
                ob_intf_nm as interface_name,
                ob_ns as source_namespace,
                ib_ns as target_namespace
            from mon_intf_map
            where upper(server_id) = upper(:sid)
            order by source_system, target_system, interface_name
        """
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, {"sid": sid})
                return _rows(cursor)

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
