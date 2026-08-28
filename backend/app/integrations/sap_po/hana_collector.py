from __future__ import annotations

import re
from uuid import UUID

from app.core.config import PoServer, RtimsCollectorProfile, Settings, settings
from app.domains.collectors.contracts import AaeMessage, CollectorCheckpoint


HANA_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_$#]{0,127}$")
HANA_TIMESTAMP_FORMAT = "YYYYMMDDHH24MISSFF3"


class HanaCollectorError(RuntimeError):
    """Sanitized HANA Collector source error."""


def _identifier(value: str, field: str) -> str:
    normalized = value.strip().upper()
    if not normalized or not HANA_IDENTIFIER.fullmatch(normalized):
        raise HanaCollectorError(f"Collector {field} is invalid")
    return normalized


def build_message_query(
    profile: RtimsCollectorProfile,
) -> tuple[str, tuple[str, ...]]:
    schema = _identifier(profile.po_db_schema, "PO database schema")
    limit = int(profile.limit)
    if profile.host_id_table:
        host_table = _identifier(profile.host_id_table, "host ID table")
        host_field = _identifier(profile.host_id_field, "host ID field")
        host_select = f", h.{host_field} AS host_id"
        host_join = (
            f"LEFT OUTER JOIN {schema}.{host_table} h ON a.msg_id = h.msg_id"
        )
    else:
        host_select = ", NULL AS host_id"
        host_join = ""

    common_columns = f"""
        a.msg_id,
        a.direction,
        a.ref_to_msg_id,
        a.status,
        a.to_service_name,
        a.from_service_name,
        a.action_name,
        a.action_type,
        a.delivery_semantics,
        a.error_code,
        a.bytes_length
        {host_select}
    """
    if profile.delivery_semantics == "BE":
        sql = f"""
            SELECT TOP {limit}
                {common_columns},
                NULL AS to_service_type,
                NULL AS from_service_type,
                TO_CHAR(a.log_time, '{HANA_TIMESTAMP_FORMAT}') AS sent_recv_time,
                TO_CHAR(a.log_time, '{HANA_TIMESTAMP_FORMAT}') AS tran_delv_time,
                NULL AS schedule_time,
                NULL AS persist_until,
                NULL AS transport,
                NULL AS node,
                a.error_code AS error_category,
                NULL AS recv_action_name,
                NULL AS recv_action_type,
                TO_CHAR(a.log_time, '{HANA_TIMESTAMP_FORMAT}') AS checkpoint_time
            FROM {schema}.bc_msg_log a
            {host_join}
            WHERE a.delivery_semantics = 'BE'
              AND (
                    a.log_time > TO_TIMESTAMP(?, '{HANA_TIMESTAMP_FORMAT}')
                    OR (
                        a.log_time = TO_TIMESTAMP(?, '{HANA_TIMESTAMP_FORMAT}')
                        AND a.msg_id > ?
                    )
                  )
            ORDER BY a.log_time, a.msg_id
        """
        return sql, ("timestamp", "timestamp", "message_id")

    time_expression = "IFNULL(a.tran_delv_time, a.sent_recv_time)"
    sql = f"""
        SELECT TOP {limit}
            {common_columns},
            a.to_service_type,
            a.from_service_type,
            TO_CHAR(a.sent_recv_time, '{HANA_TIMESTAMP_FORMAT}') AS sent_recv_time,
            TO_CHAR({time_expression}, '{HANA_TIMESTAMP_FORMAT}') AS tran_delv_time,
            TO_CHAR(a.schedule_time, '{HANA_TIMESTAMP_FORMAT}') AS schedule_time,
            TO_CHAR(a.persist_until, '{HANA_TIMESTAMP_FORMAT}') AS persist_until,
            a.transport,
            a.node,
            a.error_category,
            a.recv_action_name,
            a.recv_action_type,
            TO_CHAR({time_expression}, '{HANA_TIMESTAMP_FORMAT}') AS checkpoint_time
        FROM {schema}.bc_msg a
        {host_join}
        WHERE a.sent_recv_time >= ADD_DAYS(
                  TO_TIMESTAMP(?, '{HANA_TIMESTAMP_FORMAT}'), -1
              )
          AND a.transport <> 'HTTP'
          AND (
                {time_expression} > TO_TIMESTAMP(?, '{HANA_TIMESTAMP_FORMAT}')
                OR (
                    {time_expression} = TO_TIMESTAMP(?, '{HANA_TIMESTAMP_FORMAT}')
                    AND a.msg_id > ?
                )
              )
        ORDER BY {time_expression}, a.msg_id
    """
    return sql, ("timestamp", "timestamp", "timestamp", "message_id")


def build_status_query(
    profile: RtimsCollectorProfile,
    message_count: int,
) -> str:
    if message_count < 1 or message_count > profile.limit:
        raise HanaCollectorError("Collector status message count is invalid")
    schema = _identifier(profile.po_db_schema, "PO database schema")
    placeholders = ", ".join("?" for _ in range(message_count))
    if profile.host_id_table:
        host_table = _identifier(profile.host_id_table, "host ID table")
        host_field = _identifier(profile.host_id_field, "host ID field")
        host_select = f", h.{host_field} AS host_id"
        host_join = f"LEFT OUTER JOIN {schema}.{host_table} h ON a.msg_id = h.msg_id"
    else:
        host_select = ", NULL AS host_id"
        host_join = ""

    if profile.delivery_semantics == "BE":
        return f"""
            SELECT TOP {profile.limit}
                a.msg_id, a.direction, a.ref_to_msg_id,
                MAP(a.status, NULL, 'DLNG', a.status) AS status,
                a.to_service_name, NULL AS to_service_type,
                a.from_service_name, NULL AS from_service_type,
                a.action_name, a.action_type, a.delivery_semantics,
                TO_CHAR(a.log_time, '{HANA_TIMESTAMP_FORMAT}') AS sent_recv_time,
                TO_CHAR(a.log_time, '{HANA_TIMESTAMP_FORMAT}') AS tran_delv_time,
                NULL AS schedule_time, NULL AS persist_until,
                NULL AS transport, NULL AS node,
                a.error_code, a.error_code AS error_category,
                NULL AS recv_action_name, NULL AS recv_action_type,
                a.bytes_length {host_select},
                TO_CHAR(a.log_time, '{HANA_TIMESTAMP_FORMAT}') AS checkpoint_time
            FROM {schema}.bc_msg_log a
            {host_join}
            WHERE a.delivery_semantics = 'BE'
              AND a.msg_id IN ({placeholders})
              AND a.status NOT IN ('DLNG', 'TBDL', 'WAIT', 'HOLD')
            ORDER BY a.log_time, a.msg_id
        """

    time_expression = "IFNULL(a.tran_delv_time, a.sent_recv_time)"
    return f"""
        SELECT TOP {profile.limit}
            a.msg_id, a.direction, a.ref_to_msg_id, a.status,
            a.to_service_name, a.to_service_type,
            a.from_service_name, a.from_service_type,
            a.action_name, a.action_type, a.delivery_semantics,
            TO_CHAR(a.sent_recv_time, '{HANA_TIMESTAMP_FORMAT}') AS sent_recv_time,
            TO_CHAR({time_expression}, '{HANA_TIMESTAMP_FORMAT}') AS tran_delv_time,
            TO_CHAR(a.schedule_time, '{HANA_TIMESTAMP_FORMAT}') AS schedule_time,
            TO_CHAR(a.persist_until, '{HANA_TIMESTAMP_FORMAT}') AS persist_until,
            a.transport, a.node, a.error_code, a.error_category,
            a.recv_action_name, a.recv_action_type, a.bytes_length {host_select},
            TO_CHAR({time_expression}, '{HANA_TIMESTAMP_FORMAT}') AS checkpoint_time
        FROM {schema}.bc_msg a
        {host_join}
        WHERE a.transport <> 'HTTP'
          AND a.msg_id IN ({placeholders})
          AND a.status NOT IN ('DLNG', 'TBDL', 'WAIT', 'HOLD')
        ORDER BY {time_expression}, a.msg_id
    """


class HanaAaeMessageSource:
    def __init__(self, config: Settings | None = None) -> None:
        self.config = config or settings

    def fetch(
        self,
        server: PoServer,
        profile: RtimsCollectorProfile,
        checkpoint: CollectorCheckpoint,
    ) -> list[AaeMessage]:
        sql, bind_order = build_message_query(profile)
        values = {
            "timestamp": checkpoint.timestamp,
            "message_id": checkpoint.message_id,
        }
        binds = tuple(values[name] for name in bind_order)
        return self._execute(server, profile, sql, binds)

    def fetch_status_updates(
        self,
        server: PoServer,
        profile: RtimsCollectorProfile,
        message_ids: list[str],
    ) -> list[AaeMessage]:
        if not message_ids:
            return []
        normalized = [_hana_message_id(value) for value in message_ids[: profile.limit]]
        sql = build_status_query(profile, len(normalized))
        return self._execute(server, profile, sql, tuple(normalized))

    def _execute(
        self,
        server: PoServer,
        profile: RtimsCollectorProfile,
        sql: str,
        binds: tuple[str, ...],
    ) -> list[AaeMessage]:
        host = profile.hana_host.strip() or self.config.sap_hana_host.strip()
        port = profile.hana_port or self.config.sap_hana_port
        user = profile.hana_user.strip() or self.config.sap_hana_user.strip()
        password = (
            profile.hana_password.get_secret_value()
            or self.config.sap_hana_password.get_secret_value()
        )
        if not host or not user or not password:
            raise HanaCollectorError(
                f"HANA Collector connection is not configured for SID {server.sid}"
            )
        try:
            from hdbcli import dbapi

            connection = dbapi.connect(
                address=host,
                port=port,
                user=user,
                password=password,
            )
            try:
                cursor = connection.cursor()
                try:
                    cursor.execute(sql, binds)
                    columns = [item[0].lower() for item in cursor.description]
                    rows = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
                finally:
                    cursor.close()
            finally:
                connection.close()
        except HanaCollectorError:
            raise
        except Exception as exc:
            raise HanaCollectorError(
                f"HANA Collector query failed for SID {server.sid}"
            ) from exc
        messages = [AaeMessage.from_mapping(row) for row in rows]
        for message in messages:
            if (
                not message.msg_id
                or not message.direction
                or not _valid_timestamp(message.sent_recv_time)
                or not _valid_timestamp(message.tran_delv_time)
                or not _valid_timestamp(message.checkpoint_time)
                or message.delivery_semantics != profile.delivery_semantics
            ):
                raise HanaCollectorError(
                    f"HANA Collector returned an invalid message row for SID {server.sid}"
                )
        return messages


def _hana_message_id(value: str) -> str:
    try:
        return str(UUID(value.strip()))
    except (ValueError, AttributeError) as exc:
        raise HanaCollectorError("RTIMS pending message ID is invalid") from exc


def _valid_timestamp(value: str) -> bool:
    return len(value) == 17 and value.isdigit()
