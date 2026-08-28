from contextlib import contextmanager
from time import perf_counter

import pytest

from app.core.config import PoServer, RtimsCollectorProfile, Settings
from app.domains.collectors.contracts import AaeMessage, CollectorCheckpoint
from app.domains.collectors.oracle_service import OracleRtimsCollectorService
from app.integrations.rtims import collector_repository as repository_module
from app.integrations.rtims.collector_repository import OracleCollectorRepository
from app.integrations.sap_po.hana_collector import (
    HANA_TIMESTAMP_FORMAT,
    build_message_query,
    build_status_query,
)


def profile(**overrides) -> RtimsCollectorProfile:
    values = {
        "collector_id": "aae-be",
        "oracle_instance_id": 101,
        "delivery_semantics": "BE",
        "po_db_schema": "SAPPO",
        "limit": 500,
    }
    values.update(overrides)
    return RtimsCollectorProfile.model_validate(values)


def message(**overrides) -> AaeMessage:
    values = {
        "msg_id": "12345678-1234-1234-1234-123456789abc",
        "direction": "OUTBOUND",
        "ref_msg_id": None,
        "status": "DLVD",
        "to_service_name": "TARGET",
        "to_service_type": None,
        "from_service_name": "SOURCE",
        "from_service_type": None,
        "action_name": "ACTION",
        "action_type": None,
        "delivery_semantics": "BE",
        "sent_recv_time": "20260828090000000",
        "tran_delv_time": "20260828090000000",
        "schedule_time": None,
        "persist_until": None,
        "transport": None,
        "node": None,
        "error_code": None,
        "error_category": None,
        "recv_action_name": None,
        "recv_action_type": None,
        "bytes_length": 123,
        "host_id": None,
        "checkpoint_time": "20260828090000000",
    }
    values.update(overrides)
    return AaeMessage(**values)


def test_hana_queries_use_binds_bounded_pages_and_stable_order() -> None:
    be_sql, be_binds = build_message_query(profile())
    eo_sql, eo_binds = build_message_query(
        profile(
            collector_id="aae-eo",
            delivery_semantics="EO",
            host_id_table="BC_MSG_HOST",
            host_id_field="HOST_ID",
        )
    )

    assert "SELECT TOP 500" in be_sql
    assert "ORDER BY a.log_time, a.msg_id" in be_sql
    assert f"TO_TIMESTAMP(?, '{HANA_TIMESTAMP_FORMAT}')" in be_sql
    assert be_binds == ("timestamp", "timestamp", "message_id")
    assert "IFNULL(a.tran_delv_time, a.sent_recv_time)" in eo_sql
    assert "LEFT OUTER JOIN SAPPO.BC_MSG_HOST" in eo_sql
    assert eo_binds == (
        "timestamp",
        "timestamp",
        "timestamp",
        "message_id",
    )

    with pytest.raises(ValueError):
        profile(po_db_schema="SAPPO; DROP TABLE X")


def test_hana_pending_status_query_is_id_bounded_and_uses_placeholders() -> None:
    sql = build_status_query(profile(), 2)

    assert "SELECT TOP 500" in sql
    assert "a.msg_id IN (?, ?)" in sql
    assert "NOT IN ('DLNG', 'TBDL', 'WAIT', 'HOLD')" in sql
    assert "ORDER BY a.log_time, a.msg_id" in sql


class FakeCursor:
    def __init__(self, fail_callproc: bool = False) -> None:
        self.fail_callproc = fail_callproc
        self.operations: list[tuple] = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, sql, params=None):
        self.operations.append(("execute", sql, params))

    def executemany(self, sql, params):
        self.operations.append(("executemany", sql, params))

    def callproc(self, name, params):
        self.operations.append(("callproc", name, params))
        if self.fail_callproc:
            raise RuntimeError("expected procedure failure")


class FakeConnection:
    def __init__(self, fail_callproc: bool = False) -> None:
        self.value = FakeCursor(fail_callproc)
        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return self.value

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class StatusCursor:
    def __init__(self) -> None:
        self.rows = []
        self.calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, sql, params=None):
        self.calls += 1
        if "mon_collector_params" in sql:
            self.rows = [(101, "20260828090000000", "message-key")]
        else:
            self.rows = [
                (
                    101,
                    "S",
                    "2026-08-28T18:00:00",
                    42,
                    "Success rows=7",
                    "2026-08-28T18:00:00",
                )
            ]

    def __iter__(self):
        return iter(self.rows)


class StatusConnection:
    def __init__(self) -> None:
        self.value = StatusCursor()

    def cursor(self):
        return self.value


def collector_settings() -> Settings:
    return Settings(
        _env_file=None,
        po_servers_json="[]",
        rtims_collector_enabled=True,
        rtims_oracle_host="oracle.internal",
        rtims_oracle_service="RTIMS",
        rtims_collector_oracle_user="collector",
        rtims_collector_oracle_password="secret",
    )


def test_oracle_batch_procedure_and_checkpoint_share_one_transaction(monkeypatch) -> None:
    connection = FakeConnection()

    @contextmanager
    def fake_connection(_):
        yield connection

    monkeypatch.setattr(repository_module, "collector_connection", fake_connection)
    repository = OracleCollectorRepository(collector_settings())
    repository.persist_success(
        "POP",
        profile(),
        [message()],
        CollectorCheckpoint("20260828090000000", "message-key"),
        perf_counter(),
    )

    names = [operation[0] for operation in connection.value.operations]
    assert names == ["executemany", "callproc", "execute", "execute", "execute"]
    assert connection.value.operations[1][1] == "process_msg_logs"
    assert connection.commits == 1
    assert connection.rollbacks == 0


def test_oracle_profile_status_uses_oracle_checkpoint_and_latest_log(monkeypatch) -> None:
    connection = StatusConnection()

    @contextmanager
    def fake_connection(_):
        yield connection

    monkeypatch.setattr(repository_module, "collector_connection", fake_connection)
    server = PoServer(
        sid="POP",
        display_name="Production",
        environment="production",
        base_url="https://pop.example.internal",
        capabilities=["monitor", "collector"],
        collectors=[profile()],
    )

    result = OracleCollectorRepository(collector_settings()).list_status([server])

    assert connection.value.calls == 2
    assert result[0]["status"] == "SUCCESS"
    assert result[0]["last_window_end"] == "20260828090000000"
    assert result[0]["checkpoint_message_id"] == "message-key"
    assert result[0]["item_count"] == 7


def test_oracle_procedure_failure_rolls_back_checkpoint(monkeypatch) -> None:
    connection = FakeConnection(fail_callproc=True)

    @contextmanager
    def fake_connection(_):
        yield connection

    monkeypatch.setattr(repository_module, "collector_connection", fake_connection)
    repository = OracleCollectorRepository(collector_settings())

    with pytest.raises(RuntimeError):
        repository.persist_success(
            "POP",
            profile(),
            [message()],
            CollectorCheckpoint("20260828090000000", "message-key"),
            perf_counter(),
        )

    assert connection.commits == 0
    assert connection.rollbacks == 1


class FakeSource:
    def fetch(self, server, collector_profile, checkpoint):
        return [
            message(status="WAIT"),
            message(status="DLVD", checkpoint_time="20260828090001000"),
        ]

    def fetch_status_updates(self, server, collector_profile, message_ids):
        return []


class FakeRepository:
    def __init__(self) -> None:
        self.saved = None
        self.pending_ids = []

    def load_checkpoint(self, instance_id):
        return CollectorCheckpoint("20260828085900000", "")

    def load_pending_message_ids(
        self,
        sid,
        delivery_semantics,
        search_minutes,
        limit,
    ):
        return self.pending_ids

    def persist_success(self, sid, collector_profile, messages, checkpoint, started):
        self.saved = (sid, collector_profile, messages, checkpoint)

    def persist_failure(self, instance_id, started, message="Collector execution failed"):
        raise AssertionError("failure log should not be called")


def test_oracle_service_marks_older_duplicate_and_advances_composite_checkpoint() -> None:
    repository = FakeRepository()
    service = OracleRtimsCollectorService(FakeSource(), repository)
    server = PoServer(
        sid="POP",
        display_name="Production",
        environment="production",
        base_url="https://pop.example.internal",
        capabilities=["monitor", "collector"],
    )

    result = service.run(server, profile(), "tester")

    saved_messages = repository.saved[2]
    saved_checkpoint = repository.saved[3]
    assert saved_messages[0].status == "DLNG"
    assert saved_messages[1].status == "DLVD"
    assert saved_checkpoint.timestamp == "20260828090001000"
    assert saved_checkpoint.message_id == message().msg_id.lower()
    assert result["target"] == "rtims-oracle"


class PendingStatusSource:
    def fetch(self, server, collector_profile, checkpoint):
        return [message(checkpoint_time="20260828090000000")]

    def fetch_status_updates(self, server, collector_profile, message_ids):
        assert message_ids == ["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"]
        return [
            message(
                msg_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                checkpoint_time="20260828093000000",
            )
        ]


def test_pending_status_rows_do_not_advance_new_message_checkpoint() -> None:
    repository = FakeRepository()
    repository.pending_ids = ["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"]
    service = OracleRtimsCollectorService(PendingStatusSource(), repository)
    server = PoServer(
        sid="POP",
        display_name="Production",
        environment="production",
        base_url="https://pop.example.internal",
        capabilities=["monitor", "collector"],
    )

    result = service.run(server, profile(), "tester")

    assert repository.saved[3].timestamp == "20260828090000000"
    assert result["new_rows"] == 1
    assert result["status_rows"] == 1
