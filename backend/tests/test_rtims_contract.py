from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Any

from app.integrations.rtims import repository as rtims_module
from app.integrations.rtims.repository import RtimsRepository


class FakeCursor:
    def __init__(self, responses: list[tuple[list[str], list[tuple[Any, ...]]]]) -> None:
        self.responses = responses
        self.description: list[tuple[str]] = []
        self.rows: list[tuple[Any, ...]] = []
        self.executions: list[tuple[str, dict[str, object]]] = []
        self.rowcount = 1
        self.arraysize = 1

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, sql: str, params: dict[str, object]) -> None:
        self.executions.append((sql, params))
        columns, self.rows = self.responses.pop(0)
        self.description = [(column,) for column in columns]

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self.rows

    def fetchone(self) -> tuple[Any, ...] | None:
        return self.rows[0] if self.rows else None


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self.value = cursor
        self.committed = False
        self.rolled_back = False

    def cursor(self) -> FakeCursor:
        return self.value

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def install_connection(monkeypatch, fake: FakeConnection) -> None:
    @contextmanager
    def connection_override():
        yield fake

    monkeypatch.setattr(rtims_module, "connection", connection_override)


def test_recent_messages_uses_live_mon_msg_log_contract(monkeypatch) -> None:
    now = datetime(2026, 8, 23, 12, 0, 0)
    columns = [
        "LOG_ID", "MSG_ID", "MSG_STATUS", "SERVER_ID", "HOST_ID",
        "REQ_START_DTM", "REQ_END_DTM", "RES_START_DTM", "RES_END_DTM",
        "REQ_ELAPSED_SEC", "PROV_ELAPSED_SEC", "RES_ELAPSED_SEC",
        "REQ_MSG_SIZE", "RES_MSG_SIZE", "INTF_ID", "OB_NS",
        "OB_INTF_NM", "OB_SYSTEM", "IB_NS", "IB_INTF_NM", "IB_SYSTEM",
    ]
    cursor = FakeCursor(
        [
            (
                columns,
                [
                    (
                        1, "MSG-1", "S", "POP", "host", now, now, now, now,
                        0.1, 0.2, 0.3, 100, 200, 7, "urn:ob", "HRD_OUT",
                        "ERP", "urn:ib", "HRD_IN", "MES",
                    )
                ],
            )
        ]
    )
    fake = FakeConnection(cursor)
    install_connection(monkeypatch, fake)

    rows = RtimsRepository().recent_messages(
        "POP", 20, hours=24, status="SUCCESS", keyword="HRD"
    )

    sql, params = cursor.executions[0]
    assert "from mon_msg_log a" in sql.lower()
    assert "mon_buf_aae_msg" not in sql.lower()
    assert params["sid"] == "POP"
    assert params["keyword"] == "%HRD%"
    assert rows[0]["message_id"] == "MSG-1"
    assert rows[0]["duration_ms"] == 600
    assert rows[0]["size_bytes"] == 300


def test_resource_history_uses_collector_usage_table(monkeypatch) -> None:
    columns = [
        "SERVER_ID", "RESOURCE_ID", "RESOURCE_TYPE", "RESOURCE_NAME",
        "NODE", "MINUTE_DAY", "USAGE_PERCENT",
    ]
    cursor = FakeCursor(
        [
            (columns, [("POP", 1, "CPU", "CPU", "node-1", 600, 72)]),
            (columns, [("POP", 2, "MEMORY", "Heap", "node-1", 600, 91)]),
        ]
    )
    fake = FakeConnection(cursor)
    install_connection(monkeypatch, fake)

    rows = RtimsRepository().resource_summary("POP", ("CPU", "MEMORY"), 1)

    assert len(cursor.executions) == 2
    assert all("from mon_res_usage" in sql.lower() for sql, _ in cursor.executions)
    assert rows[0]["status"] == "Yellow"
    assert rows[1]["status"] == "Red"
    assert rows[1]["timeseries"][0]["usage_percent"] == 91


def test_incidents_use_mon_err_hist_and_live_joins(monkeypatch) -> None:
    now = datetime(2026, 8, 23, 12, 0, 0)
    columns = [
        "ERROR_LOG_ID", "MESSAGE_ID", "MSGGUID", "SERVER_ID", "CLIENT_ID",
        "ERROR_TEXT", "ERROR_LEVEL", "FIRST_SEEN_AT", "LAST_SEEN_AT",
        "ERROR_STATE", "PROCESS_MESSAGE", "USER_ID", "INTF_ID", "MNG_INTF_ID",
        "INTERFACE_NAME", "OB_INTF_NM", "GROUP_ID", "GROUP_NM", "OB_SYSTEM",
        "IB_SYSTEM", "ERR_CODE", "CATEGORY_ID", "CATEGORY_NM", "RN",
    ]
    cursor = FakeCursor(
        [
            (
                columns,
                [
                    (
                        9, "MSG-9", "MSG-9", "POP", "100", "failure", "E",
                        now, now, "O", None, None, 3, "IFS-3", "HRD Interface",
                        "HRD Interface", 2, "HRD", "ERP", "MES", "E001", 1,
                        "Adapter", 1,
                    )
                ],
            )
        ]
    )
    fake = FakeConnection(cursor)
    install_connection(monkeypatch, fake)

    rows = RtimsRepository().incidents("POP", 100, 0, 24)

    sql, params = cursor.executions[0]
    assert "from mon_err_hist h" in sql.lower()
    assert "mon_inci_log" not in sql.lower()
    assert "inner join mon_intf_map" in sql.lower()
    assert params["end_row"] == 100
    assert rows[0]["error_log_id"] == 9
    assert rows[0]["first_seen_at"] == now.isoformat()
    assert "rn" not in rows[0]


def test_resolve_incident_updates_mon_err_hist(monkeypatch) -> None:
    cursor = FakeCursor([([], [])])
    fake = FakeConnection(cursor)
    install_connection(monkeypatch, fake)

    RtimsRepository().resolve_incident(9, "operator", "checked")

    sql, params = cursor.executions[0]
    assert "update mon_err_hist" in sql.lower()
    assert "err_state = 'c'" in sql.lower()
    assert params["error_log_id"] == 9
    assert fake.committed is True
    assert fake.rolled_back is False
