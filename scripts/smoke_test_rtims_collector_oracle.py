from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import PoServer, RtimsCollectorProfile, Settings  # noqa: E402
from app.domains.collectors.contracts import AaeMessage, CollectorCheckpoint  # noqa: E402
from app.integrations.rtims.collector_repository import OracleCollectorRepository  # noqa: E402


LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
SERVER_ID = "TST"
SUCCESS_INSTANCE_ID = 900001
ROLLBACK_INSTANCE_ID = 900002
SUCCESS_MESSAGE_ID = "11111111-1111-1111-1111-111111111111"
ROLLBACK_MESSAGE_ID = "22222222-2222-2222-2222-222222222222"


def main() -> int:
    host = os.getenv("RTIMS_TEST_ORACLE_HOST", "127.0.0.1").strip().lower()
    if host not in LOCAL_HOSTS:
        raise RuntimeError("RTIMS Collector smoke test only accepts a loopback Oracle host")
    password = os.getenv("RTIMS_TEST_ORACLE_PASSWORD", "")
    if not password:
        raise RuntimeError("RTIMS_TEST_ORACLE_PASSWORD is required")
    port = int(os.getenv("RTIMS_TEST_ORACLE_PORT", "15211"))
    service = os.getenv("RTIMS_TEST_ORACLE_SERVICE", "FREEPDB1")
    user = os.getenv("RTIMS_TEST_ORACLE_USER", "RTIMS_TEST")

    config = Settings(
        _env_file=None,
        po_servers_json="[]",
        rtims_oracle_host=host,
        rtims_oracle_port=port,
        rtims_oracle_service=service,
        rtims_collector_oracle_user=user,
        rtims_collector_oracle_password=password,
        rtims_pool_min=1,
        rtims_pool_max=2,
    )

    import oracledb

    connection = oracledb.connect(
        user=user,
        password=password,
        dsn=oracledb.makedsn(host, port, service_name=service),
    )
    try:
        _reset_and_seed(connection)
    finally:
        connection.close()

    repository = OracleCollectorRepository(config)
    profile = RtimsCollectorProfile(
        collector_id="smoke-be",
        oracle_instance_id=SUCCESS_INSTANCE_ID,
        delivery_semantics="BE",
        po_db_schema="LOCAL_TEST",
        limit=100,
    )
    repository.persist_success(
        SERVER_ID,
        profile,
        [_message(SUCCESS_MESSAGE_ID, "OUTBOUND")],
        CollectorCheckpoint("20260828090000250", SUCCESS_MESSAGE_ID),
        perf_counter(),
    )

    success = _read_success(config)
    status_rows = repository.list_status(
        [
            PoServer(
                sid=SERVER_ID,
                display_name="Local RTIMS Test",
                environment="sandbox",
                base_url="https://localhost",
                capabilities=["monitor", "collector"],
                collectors=[profile],
            )
        ]
    )
    if len(status_rows) != 1 or status_rows[0]["status"] != "SUCCESS":
        raise AssertionError("Oracle Collector status projection did not return SUCCESS")
    success["status_projection"] = {
        "status": status_rows[0]["status"],
        "item_count": status_rows[0]["item_count"],
        "last_window_end": status_rows[0]["last_window_end"],
    }
    rollback = _verify_rollback(config, profile)
    print(json.dumps({"success": success, "rollback": rollback}, ensure_ascii=False))
    return 0


def _reset_and_seed(connection) -> None:
    with connection.cursor() as cursor:
        for statement, binds in (
            (
                "delete from mon_collector_params where instance_id in (:a, :b)",
                {"a": SUCCESS_INSTANCE_ID, "b": ROLLBACK_INSTANCE_ID},
            ),
            (
                "delete from mon_collector_log where instance_id in (:a, :b)",
                {"a": SUCCESS_INSTANCE_ID, "b": ROLLBACK_INSTANCE_ID},
            ),
            ("delete from mon_buf_aae_msg where server_id = :sid", {"sid": SERVER_ID}),
            (
                """
                delete from mon_daily_statistics_hist
                where intf_map_id in (
                    select intf_map_id from mon_intf_map where server_id = :sid
                )
                """,
                {"sid": SERVER_ID},
            ),
            (
                """
                delete from mon_daily_statistics
                where intf_map_id in (
                    select intf_map_id from mon_intf_map where server_id = :sid
                )
                """,
                {"sid": SERVER_ID},
            ),
            ("delete from mon_msg_log where server_id = :sid", {"sid": SERVER_ID}),
            ("delete from mon_intf_map where server_id = :sid", {"sid": SERVER_ID}),
            ("delete from pm_intf_map_pattern where pattern_id = 900001", {}),
            ("delete from pm_interface where intf_id = 900001", {}),
            ("delete from pm_intf_group where group_id = 900001", {}),
        ):
            cursor.execute(statement, binds)

        cursor.execute(
            """
            insert into pm_intf_group (group_id, group_nm, use_yn, description)
            values (900001, 'PO Monitor Local Test', 'Y', 'Disposable local smoke data')
            """
        )
        cursor.execute(
            """
            insert into pm_interface (
                intf_id, intf_nm, status, intf_level,
                ob_base_mapping, payload_yn, group_id
            ) values (900001, 'Collector Local Test', 'O', 'L', 'N', 'N', 900001)
            """
        )
        cursor.execute(
            """
            insert into pm_intf_map_pattern (
                pattern_id, ob_ns, ob_intf_nm, ob_system,
                ib_ns, ib_intf_nm, ib_system, server_id, intf_id
            ) values (
                900001, 'urn:po-monitor:test', 'SI_TEST_OUT', 'SENDER_BS',
                'urn:po-monitor:target', 'SI_TEST_IN', 'RECEIVER_BS',
                :sid, 900001
            )
            """,
            {"sid": SERVER_ID},
        )
    connection.commit()


def _message(message_id: str, direction: str) -> AaeMessage:
    return AaeMessage(
        msg_id=message_id,
        direction=direction,
        ref_msg_id=None,
        status="DLVD",
        to_service_name="RECEIVER_BS",
        to_service_type=None,
        from_service_name="SENDER_BS",
        from_service_type=None,
        action_name="SI_TEST_OUT",
        action_type="urn:po-monitor:test",
        delivery_semantics="BE",
        sent_recv_time="20260828090000000",
        tran_delv_time="20260828090000250",
        schedule_time=None,
        persist_until=None,
        transport=None,
        node="node-test",
        error_code=None,
        error_category=None,
        recv_action_name="SI_TEST_IN",
        recv_action_type="urn:po-monitor:target",
        bytes_length=1024,
        host_id="local-test",
        checkpoint_time="20260828090000250",
    )


def _connect(config: Settings):
    import oracledb

    return oracledb.connect(
        user=config.rtims_collector_oracle_username,
        password=config.rtims_collector_oracle_secret,
        dsn=oracledb.makedsn(
            config.rtims_oracle_host,
            config.rtims_oracle_port,
            service_name=config.rtims_oracle_service,
        ),
    )


def _read_success(config: Settings) -> dict[str, object]:
    normalized_id = SUCCESS_MESSAGE_ID.replace("-", "").upper()
    connection = _connect(config)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select msg_status, type, req_msg_size, req_elapsed_sec, intf_map_id
                from mon_msg_log
                where server_id = :sid and msg_id = :msg_id
                """,
                {"sid": SERVER_ID, "msg_id": normalized_id},
            )
            row = cursor.fetchone()
            if row is None:
                raise AssertionError("processed MON_MSG_LOG row was not created")
            status, message_type, size, elapsed, intf_map_id = row
            cursor.execute(
                "select count(*) from mon_buf_aae_msg where server_id = :sid",
                {"sid": SERVER_ID},
            )
            buffer_count = int(cursor.fetchone()[0])
            cursor.execute(
                """
                select key, value
                from mon_collector_params
                where instance_id = :instance_id and type = 'R'
                """,
                {"instance_id": SUCCESS_INSTANCE_ID},
            )
            checkpoint = {str(key): str(value) for key, value in cursor}
            cursor.execute(
                """
                select status, message
                from mon_collector_log
                where instance_id = :instance_id
                order by col_log_id desc fetch first 1 row only
                """,
                {"instance_id": SUCCESS_INSTANCE_ID},
            )
            log_status, log_message = cursor.fetchone()
    finally:
        connection.close()

    assert status == "S"
    assert message_type == "S"
    assert int(size) == 1024
    assert abs(float(elapsed) - 0.25) < 0.001
    assert int(intf_map_id) > 0
    assert buffer_count == 0
    assert checkpoint == {
        "MESSAGE_ID": SUCCESS_MESSAGE_ID,
        "TIMESTAMP": "20260828090000250",
    }
    assert log_status == "S"
    assert str(log_message) == "Success rows=1"
    return {
        "mon_msg_log": "created",
        "status": status,
        "type": message_type,
        "bytes": int(size),
        "elapsed_seconds": float(elapsed),
        "buffer_rows": buffer_count,
        "checkpoint_keys": sorted(checkpoint),
        "collector_log": str(log_message),
    }


def _verify_rollback(
    config: Settings,
    profile: RtimsCollectorProfile,
) -> dict[str, object]:
    failing_profile = profile.model_copy(
        update={"oracle_instance_id": ROLLBACK_INSTANCE_ID}
    )
    repository = OracleCollectorRepository(config)
    failed = False
    try:
        repository.persist_success(
            SERVER_ID,
            failing_profile,
            [_message(ROLLBACK_MESSAGE_ID, "")],
            CollectorCheckpoint("20260828090000250", ROLLBACK_MESSAGE_ID),
            perf_counter(),
        )
    except Exception:
        failed = True
    if not failed:
        raise AssertionError("invalid buffer row unexpectedly committed")

    normalized_id = ROLLBACK_MESSAGE_ID.replace("-", "").upper()
    connection = _connect(config)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select count(*)
                from mon_buf_aae_msg
                where server_id = :sid and msgid = :msg_id
                """,
                {"sid": SERVER_ID, "msg_id": normalized_id},
            )
            buffer_count = int(cursor.fetchone()[0])
            cursor.execute(
                """
                select count(*)
                from mon_collector_params
                where instance_id = :instance_id
                """,
                {"instance_id": ROLLBACK_INSTANCE_ID},
            )
            checkpoint_count = int(cursor.fetchone()[0])
            cursor.execute(
                """
                select count(*)
                from mon_collector_log
                where instance_id = :instance_id and status = 'S'
                """,
                {"instance_id": ROLLBACK_INSTANCE_ID},
            )
            success_log_count = int(cursor.fetchone()[0])
    finally:
        connection.close()

    assert buffer_count == 0
    assert checkpoint_count == 0
    assert success_log_count == 0
    return {
        "invalid_insert_failed": True,
        "buffer_rows": buffer_count,
        "checkpoint_rows": checkpoint_count,
        "success_log_rows": success_log_count,
    }


if __name__ == "__main__":
    raise SystemExit(main())
