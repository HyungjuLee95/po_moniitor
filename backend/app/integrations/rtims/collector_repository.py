from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
import re
from time import perf_counter
from typing import Any, Iterator

from app.core.config import PoServer, RtimsCollectorProfile, Settings, settings
from app.domains.collectors.contracts import AaeMessage, CollectorCheckpoint
from app.integrations.rtims.repository import ORACLE_IDENTIFIER, RtimsError


INSERT_AAE_MESSAGE_SQL = """
    insert into mon_buf_aae_msg (
        seq_id, msgid, direction, ref_msg_id, msgstatus,
        to_service_name, to_service_type,
        from_service_name, from_service_type,
        action_name, action_type, delivery_semantics,
        sent_recv_time, tran_delv_time, schedule_time,
        transport, server_id, node, error_code, error_category,
        persist_until, recv_action_name, recv_action_type,
        bytes_length, host_id
    ) values (
        mon_aae_seq_id.nextval,
        replace(upper(:msg_id), '-', ''),
        substr(upper(:direction), 1, 1),
        replace(upper(:ref_msg_id), '-', ''),
        :status,
        :to_service_name,
        :to_service_type,
        :from_service_name,
        :from_service_type,
        :action_name,
        :action_type,
        :delivery_semantics,
        from_tz(to_timestamp(:sent_recv_time, 'YYYYMMDDHH24MISSFF3'), 'GMT')
            at time zone 'Asia/Seoul',
        from_tz(to_timestamp(:tran_delv_time, 'YYYYMMDDHH24MISSFF3'), 'GMT')
            at time zone 'Asia/Seoul',
        from_tz(to_timestamp(:schedule_time, 'YYYYMMDDHH24MISSFF3'), 'GMT')
            at time zone 'Asia/Seoul',
        :transport,
        :server_id,
        :node,
        :error_code,
        :error_category,
        to_char(
            from_tz(to_timestamp(:persist_until, 'YYYYMMDDHH24MISSFF3'), 'GMT')
            at time zone 'Asia/Seoul',
            'YYYYMMDDHH24MISSFF3'
        ),
        :recv_action_name,
        :recv_action_type,
        :bytes_length,
        :host_id
    )
"""

MERGE_CHECKPOINT_SQL = """
    merge into mon_collector_params target
    using (
        select :instance_id as instance_id,
               'R' as type,
               :key as key,
               :value as value
        from dual
    ) source
    on (
        target.instance_id = source.instance_id
        and target.type = source.type
        and target.key = source.key
    )
    when matched then update set target.value = source.value
    when not matched then insert (instance_id, type, key, value)
        values (source.instance_id, source.type, source.key, source.value)
"""

INSERT_COLLECTOR_LOG_SQL = """
    insert into mon_collector_log (
        col_log_id, instance_id, status, run_time,
        elapsed_msec, message, persist_until_ts
    ) values (
        mon_col_log_id.nextval, :instance_id, :status, sysdate,
        :elapsed_msec, :message, sysdate + 1
    )
"""


@lru_cache(maxsize=4)
def _collector_pool(
    user: str,
    password: str,
    host: str,
    port: int,
    service: str,
    pool_min: int,
    pool_max: int,
):
    try:
        import oracledb

        return oracledb.create_pool(
            user=user,
            password=password,
            dsn=oracledb.makedsn(
                host,
                port,
                service_name=service,
            ),
            min=pool_min,
            max=pool_max,
            increment=1,
        )
    except Exception as exc:
        raise RtimsError("failed to initialize RTIMS Collector Oracle pool") from exc


@contextmanager
def collector_connection(config: Settings | None = None) -> Iterator[Any]:
    active = config or settings
    if not active.rtims_collector_oracle_configured:
        raise RtimsError("RTIMS Collector Oracle connection is not fully configured")
    try:
        pool = _collector_pool(
            active.rtims_collector_oracle_username,
            active.rtims_collector_oracle_secret,
            active.rtims_oracle_host,
            active.rtims_oracle_port,
            active.rtims_oracle_service,
            active.rtims_pool_min,
            active.rtims_pool_max,
        )
        with pool.acquire() as value:
            schema = active.rtims_oracle_schema.strip().upper()
            if schema:
                if not ORACLE_IDENTIFIER.fullmatch(schema):
                    raise RtimsError("RTIMS Oracle schema name is invalid")
                with value.cursor() as cursor:
                    cursor.execute(f"alter session set current_schema = {schema}")
            yield value
    except RtimsError:
        raise
    except Exception as exc:
        raise RtimsError("RTIMS Collector Oracle operation failed") from exc


class OracleCollectorRepository:
    def __init__(self, config: Settings | None = None) -> None:
        self.config = config or settings

    def load_checkpoint(self, instance_id: int) -> CollectorCheckpoint | None:
        sql = """
            select key, value
            from mon_collector_params
            where instance_id = :instance_id
              and type = 'R'
              and key in ('TIMESTAMP', 'MESSAGE_ID')
        """
        with collector_connection(self.config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, {"instance_id": instance_id})
                values = {str(key).upper(): str(value or "") for key, value in cursor}
        timestamp = values.get("TIMESTAMP", "")
        if not timestamp:
            return None
        return CollectorCheckpoint(timestamp, values.get("MESSAGE_ID", ""))

    def load_pending_message_ids(
        self,
        sid: str,
        delivery_semantics: str,
        search_minutes: int,
        limit: int,
    ) -> list[str]:
        message_type = "S" if delivery_semantics == "BE" else "A"
        sql = """
            select msg_id
            from (
                select distinct msg_id
                from (
                    select mml.msg_id as msg_id
                    from mon_msg_log mml
                    where mml.server_id = :sid
                      and mml.msg_status = 'P'
                      and mml.type = :message_type
                      and mml.req_start_dtm >= sysdate - (:search_minutes / 1440)
                      and mml.req_start_dtm <= sysdate - (1 / 1440)
                      and mml.msg_id is not null
                      and not exists (
                          select 1
                          from mon_buf_aae_msg buffer
                          where buffer.server_id = :sid
                            and buffer.msgid = mml.msg_id
                      )
                    union all
                    select mml.res_msg_id as msg_id
                    from mon_msg_log mml
                    where mml.server_id = :sid
                      and mml.msg_status = 'P'
                      and mml.type = :message_type
                      and mml.req_start_dtm >= sysdate - (:search_minutes / 1440)
                      and mml.req_start_dtm <= sysdate - (1 / 1440)
                      and mml.res_msg_id is not null
                      and not exists (
                          select 1
                          from mon_buf_aae_msg buffer
                          where buffer.server_id = :sid
                            and buffer.msgid = mml.res_msg_id
                      )
                )
            )
            where rownum <= :limit
        """
        with collector_connection(self.config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    {
                        "sid": sid,
                        "message_type": message_type,
                        "search_minutes": search_minutes,
                        "limit": limit,
                    },
                )
                return [str(row[0]) for row in cursor if row[0]]

    def list_status(self, servers: list[PoServer]) -> list[dict[str, object]]:
        targets = [
            (server, profile)
            for server in servers
            for profile in server.collectors
            if profile.enabled
        ]
        if not targets:
            return []
        instance_ids = sorted({profile.oracle_instance_id for _, profile in targets})
        placeholders = ", ".join(
            f":instance_{index}" for index in range(len(instance_ids))
        )
        binds = {
            f"instance_{index}": instance_id
            for index, instance_id in enumerate(instance_ids)
        }
        checkpoint_sql = f"""
            select instance_id,
                   max(case when key = 'TIMESTAMP' then value end) as checkpoint_time,
                   max(case when key = 'MESSAGE_ID' then value end) as checkpoint_message_id
            from mon_collector_params
            where type = 'R'
              and instance_id in ({placeholders})
            group by instance_id
        """
        log_sql = f"""
            select instance_id,
                   max(status) keep (dense_rank last order by col_log_id) as status,
                   max(run_time) keep (dense_rank last order by col_log_id) as run_time,
                   max(elapsed_msec) keep (dense_rank last order by col_log_id) as elapsed_msec,
                   max(message) keep (dense_rank last order by col_log_id) as message,
                   max(case when status = 'S' then run_time end) as last_success_at
            from mon_collector_log
            where instance_id in ({placeholders})
            group by instance_id
        """
        with collector_connection(self.config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(checkpoint_sql, binds)
                checkpoints = {
                    int(instance_id): {
                        "timestamp": str(timestamp or ""),
                        "message_id": str(message_id or ""),
                    }
                    for instance_id, timestamp, message_id in cursor
                }
                cursor.execute(log_sql, binds)
                logs = {
                    int(instance_id): {
                        "status": str(status or ""),
                        "run_time": run_time,
                        "elapsed_ms": int(elapsed_msec or 0),
                        "message": str(message or ""),
                        "last_success_at": last_success_at,
                    }
                    for (
                        instance_id,
                        status,
                        run_time,
                        elapsed_msec,
                        message,
                        last_success_at,
                    ) in cursor
                }

        status_map = {"S": "SUCCESS", "E": "FAILED"}
        result: list[dict[str, object]] = []
        for server, profile in targets:
            checkpoint = checkpoints.get(profile.oracle_instance_id, {})
            log = logs.get(profile.oracle_instance_id, {})
            message = str(log.get("message") or "")
            count_match = re.search(r"\brows=(\d+)\b", message)
            result.append(
                {
                    "sid": server.sid,
                    "server_name": server.display_name,
                    "collector_id": profile.collector_id,
                    "oracle_instance_id": profile.oracle_instance_id,
                    "delivery_semantics": profile.delivery_semantics,
                    "status": status_map.get(str(log.get("status") or ""), "READY"),
                    "last_run_at": log.get("run_time"),
                    "last_success_at": log.get("last_success_at"),
                    "last_window_end": checkpoint.get("timestamp"),
                    "checkpoint_message_id": checkpoint.get("message_id"),
                    "item_count": int(count_match.group(1)) if count_match else 0,
                    "elapsed_ms": int(log.get("elapsed_ms") or 0),
                    "detail": message or None,
                }
            )
        return result

    def persist_success(
        self,
        sid: str,
        profile: RtimsCollectorProfile,
        messages: list[AaeMessage],
        checkpoint: CollectorCheckpoint,
        started: float,
    ) -> None:
        params = [_message_params(sid, message) for message in messages]
        with collector_connection(self.config) as connection:
            try:
                with connection.cursor() as cursor:
                    if params:
                        cursor.executemany(INSERT_AAE_MESSAGE_SQL, params)
                        cursor.callproc(
                            "process_msg_logs",
                            [
                                profile.persist_duration_days,
                                profile.multi_server_run_duration_days,
                            ],
                        )
                    self._merge_checkpoint(cursor, profile.oracle_instance_id, checkpoint)
                    self._insert_log(
                        cursor,
                        profile.oracle_instance_id,
                        "S",
                        round((perf_counter() - started) * 1000),
                        f"Success rows={len(messages)}",
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def persist_failure(
        self,
        instance_id: int,
        started: float,
        message: str = "Collector execution failed",
    ) -> None:
        with collector_connection(self.config) as connection:
            try:
                with connection.cursor() as cursor:
                    self._insert_log(
                        cursor,
                        instance_id,
                        "E",
                        round((perf_counter() - started) * 1000),
                        message,
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def _merge_checkpoint(
        cursor,
        instance_id: int,
        checkpoint: CollectorCheckpoint,
    ) -> None:
        for key, value in (
            ("TIMESTAMP", checkpoint.timestamp),
            ("MESSAGE_ID", checkpoint.message_id),
        ):
            cursor.execute(
                MERGE_CHECKPOINT_SQL,
                {
                    "instance_id": instance_id,
                    "key": key,
                    "value": value,
                },
            )

    @staticmethod
    def _insert_log(
        cursor,
        instance_id: int,
        status: str,
        elapsed_msec: int,
        message: str,
    ) -> None:
        cursor.execute(
            INSERT_COLLECTOR_LOG_SQL,
            {
                "instance_id": instance_id,
                "status": status,
                "elapsed_msec": elapsed_msec,
                "message": message[:2000],
            },
        )


def _message_params(sid: str, message: AaeMessage) -> dict[str, object]:
    status = message.status
    if message.delivery_semantics == "BE" and not status:
        status = "DLNG"
    return {
        "msg_id": message.msg_id,
        "direction": message.direction,
        "ref_msg_id": message.ref_msg_id,
        "status": status,
        "to_service_name": _dash(message.to_service_name),
        "to_service_type": message.to_service_type,
        "from_service_name": message.from_service_name,
        "from_service_type": message.from_service_type,
        "action_name": message.action_name,
        "action_type": message.action_type,
        "delivery_semantics": message.delivery_semantics,
        "sent_recv_time": message.sent_recv_time,
        "tran_delv_time": message.tran_delv_time,
        "schedule_time": message.schedule_time,
        "transport": message.transport,
        "server_id": sid,
        "node": message.node,
        "error_code": message.error_code,
        "error_category": message.error_category,
        "persist_until": message.persist_until,
        "recv_action_name": _dash(message.recv_action_name),
        "recv_action_type": _dash(message.recv_action_type),
        "bytes_length": message.bytes_length,
        "host_id": message.host_id,
    }


def _dash(value: str | None) -> str:
    return value if value and value.strip() else "-"
