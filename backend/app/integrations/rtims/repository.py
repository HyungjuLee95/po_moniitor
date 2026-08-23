from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta
from functools import lru_cache
import re
from typing import Any, Iterator

from app.core.config import settings
from app.integrations.rtims.contract import REQUIRED_COLUMNS, REQUIRED_OBJECTS


class RtimsError(RuntimeError):
    """Sanitized RTIMS Oracle error."""


ORACLE_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_$#]{0,127}$")


def _configured_schema() -> str:
    schema = settings.rtims_oracle_schema.strip()
    if schema and not ORACLE_IDENTIFIER.fullmatch(schema):
        raise RtimsError("RTIMS Oracle schema name is invalid")
    return schema.upper()


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
            schema = _configured_schema()
            if schema:
                with value.cursor() as cursor:
                    cursor.execute(f"alter session set current_schema = {schema}")
            yield value
    except RtimsError:
        raise
    except Exception as exc:
        raise RtimsError("RTIMS Oracle operation failed") from exc


def _rows(cursor) -> list[dict]:
    columns = [item[0].lower() for item in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


class RtimsRepository:
    REQUIRED_OBJECTS = REQUIRED_OBJECTS

    def check(self) -> None:
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("select 1 from dual")
                cursor.fetchone()

    def check_contract(self) -> list[dict]:
        results: list[dict] = []
        with connection() as conn:
            with conn.cursor() as cursor:
                for object_name in self.REQUIRED_OBJECTS:
                    try:
                        columns = ", ".join(
                            f"t.{column}" for column in sorted(REQUIRED_COLUMNS[object_name])
                        )
                        cursor.execute(
                            f"select {columns} from {object_name} t where 1 = 0"
                        )
                        results.append({"object": object_name, "ready": True})
                    except Exception:
                        results.append({"object": object_name, "ready": False})
        return results

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

    def message_throughput(
        self,
        sid: str,
        granularity: str = "hour",
        days: int = 1,
    ) -> list[dict]:
        if granularity == "day":
            bucket_key = "to_char(l.req_start_dtm, 'YYYYMMDD')"
            bucket_label = "to_char(l.req_start_dtm, 'MM-DD')"
            window_clause = (
                "l.req_start_dtm >= trunc(sysdate) - (:days - 1) "
                "and l.req_start_dtm < trunc(sysdate) + 1"
            )
        else:
            bucket_key = "to_char(l.req_start_dtm, 'YYYYMMDDHH24')"
            bucket_label = "to_char(l.req_start_dtm, 'HH24:00')"
            window_clause = (
                "l.req_start_dtm >= trunc(sysdate) "
                "and l.req_start_dtm < trunc(sysdate) + 1"
            )

        sql = f"""
            select
                {bucket_key} as bucket,
                {bucket_label} as label,
                count(*) as total_count,
                sum(case when l.msg_status = 'S' then 1 else 0 end) as success_count,
                sum(case when l.msg_status = 'F' then 1 else 0 end) as fail_count,
                sum(case when l.msg_status = 'P' then 1 else 0 end) as pending_count,
                sum(nvl(l.req_msg_size, 0) + nvl(l.res_msg_size, 0))
                    as total_size_bytes
            from mon_msg_log l
            where upper(l.server_id) = upper(:sid)
              and {window_clause}
            group by {bucket_key}, {bucket_label}
            order by bucket
        """
        with connection() as conn:
            with conn.cursor() as cursor:
                params: dict[str, object] = {"sid": sid}
                if granularity == "day":
                    params["days"] = days
                cursor.execute(sql, params)
                rows = _rows(cursor)
        return [
            {
                "bucket": str(row["bucket"]),
                "label": str(row["label"]),
                "hour": (
                    int(str(row["bucket"])[-2:])
                    if granularity == "hour"
                    else None
                ),
                "total_count": int(row.get("total_count") or 0),
                "success_count": int(row.get("success_count") or 0),
                "fail_count": int(row.get("fail_count") or 0),
                "pending_count": int(row.get("pending_count") or 0),
                "total_size_bytes": int(row.get("total_size_bytes") or 0),
            }
            for row in rows
        ]

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
        status: str | None = None,
        keyword: str | None = None,
    ) -> list[dict]:
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(hours=hours)
        clauses = [
            "upper(a.server_id) = upper(:sid)",
            "a.req_start_dtm >= :start_dt",
            "a.req_start_dtm <= :end_dt",
        ]
        params: dict[str, object] = {
            "sid": sid,
            "start_dt": start_dt,
            "end_dt": end_dt,
            "offset": offset,
            "limit": limit,
        }
        normalized_status = (status or "").strip().upper()
        status_groups = {
            "SUCCESS": ("S", "SUCCESS", "DELIVERED", "DLVD"),
            "FAILED": ("F", "FAIL", "FAILED", "ERROR"),
            "DELIVERING": ("P", "I", "DELIVERING", "PENDING"),
        }
        if normalized_status:
            values = status_groups.get(normalized_status, (normalized_status,))
            placeholders = []
            for index, value in enumerate(values):
                key = f"status_{index}"
                placeholders.append(f":{key}")
                params[key] = value
            clauses.append(f"upper(a.msg_status) in ({', '.join(placeholders)})")
        normalized_keyword = (keyword or "").strip().upper()
        if normalized_keyword:
            clauses.append(
                "upper(nvl(b.ob_intf_nm, '') || ' ' || nvl(b.ib_intf_nm, '') || ' ' || "
                "nvl(b.ob_system, '') || ' ' || nvl(b.ib_system, '')) like :keyword"
            )
            params["keyword"] = f"%{normalized_keyword}%"
        sql = f"""
            select
                a.log_id,
                a.msg_id,
                a.msg_status,
                a.server_id,
                a.host_id,
                a.req_start_dtm,
                a.req_end_dtm,
                a.res_start_dtm,
                a.res_end_dtm,
                a.req_elapsed_sec,
                a.prov_elapsed_sec,
                a.res_elapsed_sec,
                a.req_msg_size,
                a.res_msg_size,
                b.intf_id,
                b.ob_ns,
                b.ob_intf_nm,
                b.ob_system,
                b.ib_ns,
                b.ib_intf_nm,
                b.ib_system
            from mon_msg_log a
            left join mon_intf_map b on b.intf_map_id = a.intf_map_id
            where {" and ".join(clauses)}
            order by a.req_start_dtm desc, a.log_id desc
            offset :offset rows fetch next :limit rows only
        """
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                rows = _rows(cursor)
        return [
            {
                "message_id": row["msg_id"],
                "sid": row["server_id"],
                "interface_name": row["ob_intf_nm"] or row["ib_intf_nm"] or "",
                "status": row["msg_status"],
                "start_time": (
                    row["req_start_dtm"].isoformat()
                    if row["req_start_dtm"] else None
                ),
                "end_time": (
                    (row["res_end_dtm"] or row["req_end_dtm"]).isoformat()
                    if row["res_end_dtm"] or row["req_end_dtm"] else None
                ),
                "duration_ms": round(
                    (
                        float(row["req_elapsed_sec"] or 0)
                        + float(row["prov_elapsed_sec"] or 0)
                        + float(row["res_elapsed_sec"] or 0)
                    )
                    * 1000
                ),
                "source_system": row["ob_system"],
                "target_system": row["ib_system"],
                "namespace": row["ob_ns"] or row["ib_ns"] or "",
                "error_text": None,
                "size_bytes": int(row["req_msg_size"] or 0)
                + int(row["res_msg_size"] or 0),
            }
            for row in rows
        ]

    def message_count(
        self,
        sid: str,
        hours: int = 24,
        status: str | None = None,
        keyword: str | None = None,
    ) -> int:
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(hours=hours)
        clauses = [
            "upper(a.server_id) = upper(:sid)",
            "a.req_start_dtm >= :start_dt",
            "a.req_start_dtm <= :end_dt",
        ]
        params: dict[str, object] = {
            "sid": sid,
            "start_dt": start_dt,
            "end_dt": end_dt,
        }
        normalized_status = (status or "").strip().upper()
        status_groups = {
            "SUCCESS": ("S", "SUCCESS", "DELIVERED", "DLVD"),
            "FAILED": ("F", "FAIL", "FAILED", "ERROR"),
            "DELIVERING": ("P", "I", "DELIVERING", "PENDING"),
        }
        if normalized_status:
            values = status_groups.get(normalized_status, (normalized_status,))
            placeholders = []
            for index, value in enumerate(values):
                key = f"status_{index}"
                placeholders.append(f":{key}")
                params[key] = value
            clauses.append(f"upper(a.msg_status) in ({', '.join(placeholders)})")
        normalized_keyword = (keyword or "").strip().upper()
        if normalized_keyword:
            clauses.append(
                "upper(nvl(b.ob_intf_nm, '') || ' ' || nvl(b.ib_intf_nm, '') || ' ' || "
                "nvl(b.ob_system, '') || ' ' || nvl(b.ib_system, '')) like :keyword"
            )
            params["keyword"] = f"%{normalized_keyword}%"
        sql = f"""
            select count(*) as cnt
            from mon_msg_log a
            left join mon_intf_map b on b.intf_map_id = a.intf_map_id
            where {" and ".join(clauses)}
        """
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                row = cursor.fetchone()
        return int(row[0] or 0) if row else 0

    def channel_statistics(
        self,
        sid: str,
        channel_name: str,
        hours: int = 24,
    ) -> dict:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        sql = """
            select
                count(*) as total_count,
                sum(case when l.msg_status = 'S' then 1 else 0 end) as success_count,
                sum(case when l.msg_status = 'F' then 1 else 0 end) as fail_count,
                sum(case when l.msg_status = 'P' then 1 else 0 end) as pending_count,
                avg(l.req_elapsed_sec) as avg_elapsed_sec,
                sum(nvl(l.req_msg_size, 0) + nvl(l.res_msg_size, 0)) as total_msg_size,
                avg(nvl(l.req_msg_size, 0) + nvl(l.res_msg_size, 0)) as avg_msg_size
            from mon_msg_log l
            where upper(l.server_id) = upper(:sid)
              and l.req_start_dtm >= :start_time
              and l.req_start_dtm < :end_time
              and l.intf_map_id in (
                  select m.intf_map_id
                  from mon_intf_map m
                  where upper(m.server_id) = upper(:sid)
                    and (
                        upper(m.ob_intf_nm) like upper(:channel_name)
                        or upper(m.ib_intf_nm) like upper(:channel_name)
                    )
              )
        """
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    sql,
                    {
                        "sid": sid,
                        "channel_name": f"%{channel_name}%",
                        "start_time": start_time,
                        "end_time": end_time,
                    },
                )
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
        hours: int = 24,
    ) -> list[dict]:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        sql = """
            select
                l.log_id,
                l.msg_id as message_id,
                l.msg_status as status,
                l.server_id,
                to_char(l.req_start_dtm, 'YYYY-MM-DD HH24:MI:SS') as start_time,
                l.req_elapsed_sec as elapsed_sec,
                (nvl(l.req_msg_size, 0) + nvl(l.res_msg_size, 0)) as msg_size
            from mon_msg_log l
            where upper(l.server_id) = upper(:sid)
              and l.req_start_dtm >= :start_time
              and l.req_start_dtm < :end_time
              and l.intf_map_id in (
                  select m.intf_map_id
                  from mon_intf_map m
                  where upper(m.server_id) = upper(:sid)
                    and (
                        upper(m.ob_intf_nm) like upper(:channel_name)
                        or upper(m.ib_intf_nm) like upper(:channel_name)
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
                        "channel_name": f"%{channel_name}%",
                        "limit": limit,
                        "offset": offset,
                        "start_time": start_time,
                        "end_time": end_time,
                    },
                )
                rows = _rows(cursor)
        for row in rows:
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

    def resource_summary(
        self,
        sid: str,
        resource_types: tuple[str, ...] = ("CPU", "MEMORY"),
        hours: int = 1,
    ) -> list[dict]:
        now = datetime.now()
        end_minute = now.hour * 60 + now.minute
        start_minute = max(0, end_minute - hours * 60)
        sql = """
            select
                u.server_id,
                u.resource_id,
                r.type as resource_type,
                r.resourcenm as resource_name,
                u.node,
                u.minute_day,
                decode(
                    u.max_limit,
                    0,
                    0,
                    round(u.recent_usage / u.max_limit * 100, 0)
                ) as usage_percent
            from mon_res_usage u
            join mon_resource r on r.resource_id = u.resource_id
            where upper(u.server_id) = upper(:sid)
              and upper(r.type) = upper(:resource_type)
              and u.ymdd = :ymdd
              and u.minute_day between :start_min and :end_min
            order by u.server_id, u.node, u.resource_id, u.minute_day
        """
        rows: list[dict] = []
        with connection() as conn:
            with conn.cursor() as cursor:
                for resource_type in resource_types:
                    cursor.execute(
                        sql,
                        {
                            "sid": sid,
                            "resource_type": resource_type,
                            "ymdd": now.strftime("%Y%m%d"),
                            "start_min": start_minute,
                            "end_min": end_minute,
                        },
                    )
                    rows.extend(_rows(cursor))
        grouped: dict[tuple[object, object], dict] = {}
        for row in rows:
            key = (row["resource_id"], row["node"])
            value = grouped.setdefault(
                key,
                {
                    "server_id": row["server_id"],
                    "resource_id": row["resource_id"],
                    "resource_type": row["resource_type"],
                    "resource_name": row["resource_name"],
                    "node": row["node"],
                    "recent_usage": 0.0,
                    "max_usage": 0.0,
                    "max_limit": 100.0,
                    "status": "Green",
                    "timeseries": [],
                },
            )
            usage = float(row.get("usage_percent") or 0)
            value["recent_usage"] = usage
            value["max_usage"] = max(float(value["max_usage"]), usage)
            value["status"] = "Red" if usage > 90 else ("Yellow" if usage > 70 else "Green")
            value["timeseries"].append(
                {"minute_day": int(row["minute_day"]), "usage_percent": usage}
            )
        return list(grouped.values())

    def queue_summary(self, sid: str) -> dict:
        ae_sql = """
            select server_id, servernode, queuename, conname, started, num_entries,
                   threads_assigned, threads_working, max_thread,
                   case
                       when nvl(max_thread, 0) > 0
                       then round(nvl(threads_working, 0) / max_thread * 100, 2)
                       else 0
                   end as load_factor
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

    def system_statistics(self, sid: str, hours: int = 24) -> list[dict]:
        sql = """
            with status_data as (
                select s.intf_map_id, s.msg_status, s.count as msg_count
                from mon_daily_statistics s
                where to_date(s.ymdd || lpad(s.hour, 2, '0'), 'YYYYMMDDHH24')
                      >= sysdate - (:hours / 24)
                union all
                select c.intf_map_id, 'C' as msg_status, c.count as msg_count
                from mon_daily_close_stat c
                where to_date(c.ymdd || lpad(c.hour, 2, '0'), 'YYYYMMDDHH24')
                      >= sysdate - (:hours / 24)
            ), group_data as (
                select
                    g.group_id,
                    g.group_nm,
                    d.msg_status,
                    nvl(d.msg_count, 0) as msg_count
                from pm_intf_group g
                left join pm_interface i on i.group_id = g.group_id
                left join mon_intf_map m
                  on m.intf_id = i.intf_id
                 and upper(m.server_id) = upper(:sid)
                left join status_data d on d.intf_map_id = m.intf_map_id
            )
            select
                group_id,
                nvl(group_nm, 'Unknown') as system_name,
                sum(case when msg_status = 'S' then msg_count else 0 end) as success_count,
                sum(case when msg_status = 'F' then msg_count else 0 end) as fail_count,
                sum(case when msg_status = 'P' then msg_count else 0 end) as pending_count,
                sum(case when msg_status = 'C' then msg_count else 0 end) as closed_count,
                sum(msg_count) as total_count
            from group_data
            group by group_id, group_nm
            order by fail_count desc,
                     pending_count desc,
                     case when nvl(group_nm, 'Unknown') = 'Unknown' then 1 else 0 end,
                     system_name asc
        """
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.arraysize = 100
                cursor.execute(sql, {"sid": sid, "hours": hours})
                rows = _rows(cursor)
        for row in rows:
            total = int(row.get("total_count") or 0)
            success = int(row.get("success_count") or 0)
            fail = int(row.get("fail_count") or 0)
            row.update(
                success_count=success,
                fail_count=fail,
                pending_count=int(row.get("pending_count") or 0),
                closed_count=int(row.get("closed_count") or 0),
                total_count=total,
                success_rate=round(success / total * 100, 2) if total else 0.0,
                fail_rate=round(fail / total * 100, 2) if total else 0.0,
            )
        return rows

    def system_queue_status(self, sid: str) -> list[dict]:
        sql = """
            select server_id, client_id,
                   sum(case when severity = 'N' then msg_count else 0 end) as normal,
                   sum(case when severity = 'W' then msg_count else 0 end) as warning,
                   sum(case when severity = 'F' then msg_count else 0 end) as fail
            from mon_q_status
            where upper(server_id) = upper(:sid)
            group by server_id, client_id
            order by fail desc, warning desc, client_id
        """
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, {"sid": sid})
                return _rows(cursor)

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
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        sql = """
            select
                error_log_id, message_id, msgguid, server_id, client_id,
                error_text, error_level, first_seen_at, last_seen_at,
                error_state, process_message, user_id, intf_id, mng_intf_id,
                interface_name, ob_intf_nm, group_id, group_nm, ob_system,
                ib_system, err_code, category_id, category_nm
            from (
                select
                    h.err_log_id as error_log_id,
                    h.ref_msg_id as message_id,
                    h.ref_msg_id as msgguid,
                    nvl(m.server_id, h.ref_server_id) as server_id,
                    h.ref_client_id as client_id,
                    h.err_msg as error_text,
                    h.error_level,
                    h.err_dtm as first_seen_at,
                    h.err_dtm as last_seen_at,
                    h.err_state as error_state,
                    h.err_proc_msg as process_message,
                    h.user_id,
                    i.intf_id,
                    i.mng_intf_id,
                    i.intf_nm as interface_name,
                    i.intf_nm as ob_intf_nm,
                    g.group_id,
                    g.group_nm,
                    m.ob_system,
                    m.ib_system,
                    e.err_code,
                    c.err_cate_id as category_id,
                    c.err_cate_nm as category_nm,
                    row_number() over (order by h.err_dtm desc, h.err_log_id desc) as rn
                from mon_err_hist h
                inner join mon_intf_map m on m.intf_map_id = h.ref_intf_map_id
                inner join pm_interface i on i.intf_id = m.intf_id
                inner join pm_intf_group g on g.group_id = i.group_id
                left join sys_err_code e on e.err_code_id = h.err_code_id
                left join sys_err_cate c on c.err_cate_id = e.err_cate_id
                where h.err_dtm >= :start_time
                  and h.err_dtm <= :end_time
                  and upper(m.server_id) = upper(:sid)
            )
            where rn > :offset
              and rn <= :end_row
            order by rn
        """
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    sql,
                    {
                        "sid": sid,
                        "start_time": start_time,
                        "end_time": end_time,
                        "offset": offset,
                        "end_row": offset + limit,
                    },
                )
                rows = _rows(cursor)
        for row in rows:
            row.pop("rn", None)
            for field in ("first_seen_at", "last_seen_at"):
                if row.get(field) is not None:
                    row[field] = row[field].isoformat()
        return rows

    def resolve_incident(
        self,
        error_log_id: int,
        username: str,
        message: str | None,
    ) -> None:
        sql = """
            update mon_err_hist
            set err_state = 'C',
                err_proc_msg = :message,
                user_id = :username
            where err_log_id = :error_log_id
        """
        with connection() as conn:
            try:
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
            except Exception:
                conn.rollback()
                raise
