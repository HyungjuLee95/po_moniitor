import pytest

from app.core.config import PoServer, Settings
from app.domains.collectors.scheduler import CollectorScheduler


def server(
    sid: str,
    *,
    collector: bool = True,
    enabled: bool = True,
    profiles: list[dict] | None = None,
) -> PoServer:
    return PoServer(
        sid=sid,
        display_name=sid,
        environment="quality",
        base_url="https://example.invalid",
        enabled=enabled,
        capabilities=["monitor", "collector"] if collector else ["monitor"],
        collectors=profiles or [],
    )


class FakeRegistry:
    def __init__(self, servers: list[PoServer]) -> None:
        self.servers = servers

    def list_enabled(self) -> list[PoServer]:
        return self.servers


class FakeCollectorService:
    def __init__(self, failing_sid: str | None = None) -> None:
        self.failing_sid = failing_sid
        self.calls: list[tuple[str, str, int]] = []

    def run(self, value: PoServer, username: str, limit: int = 1000) -> dict:
        self.calls.append((value.sid, username, limit))
        if value.sid == self.failing_sid:
            raise RuntimeError("expected collector failure")
        return {"sid": value.sid, "status": "SUCCESS", "fetched": 1}


class FakeOracleCollectorService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def run(self, value, profile, requested_by: str) -> dict:
        self.calls.append((value.sid, profile.collector_id, requested_by))
        return {
            "sid": value.sid,
            "collector_id": profile.collector_id,
            "status": "SUCCESS",
            "fetched": 1,
        }


class FakeClock:
    def __init__(self, value: float = 100.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value


class StopAfterOneCycle:
    def __init__(self) -> None:
        self.waits: list[float | None] = []

    def is_set(self) -> bool:
        return False

    def wait(self, timeout: float | None = None) -> bool:
        self.waits.append(timeout)
        return len(self.waits) == 2


def collector_settings() -> Settings:
    return Settings(
        _env_file=None,
        po_servers_json="[]",
        rtims_collector_enabled=True,
        rtims_collector_startup_delay_seconds=7,
        rtims_collector_interval_seconds=60,
        rtims_collector_limit=250,
    )


def test_run_once_filters_servers_and_isolates_failures() -> None:
    service = FakeCollectorService(failing_sid="P02")
    scheduler = CollectorScheduler(
        registry=FakeRegistry(
            [
                server("P01"),
                server("P02"),
                server("P03", collector=False),
                server("P04", enabled=False),
            ]
        ),
        service=service,
        config=collector_settings(),
    )

    results = scheduler.run_once()

    assert [call[0] for call in service.calls] == ["P01", "P02"]
    assert all(call[1] == "system:rtims-collector" for call in service.calls)
    assert all(call[2] == 250 for call in service.calls)
    assert [result["status"] for result in results] == ["SUCCESS", "FAILED"]


def test_scheduler_uses_interruptible_startup_and_fixed_delay() -> None:
    service = FakeCollectorService()
    clock = FakeClock()
    stop_event = StopAfterOneCycle()
    scheduler = CollectorScheduler(
        registry=FakeRegistry([server("P01")]),
        service=service,
        config=collector_settings(),
        clock=clock,
    )

    scheduler.run(stop_event)

    assert len(service.calls) == 1
    assert stop_event.waits == [7, 60]


def test_scheduler_runs_oracle_profiles_instead_of_checkpoint_fallback() -> None:
    service = FakeCollectorService()
    oracle_service = FakeOracleCollectorService()
    value = server(
        "P01",
        profiles=[
            {
                "collector_id": "aae-be",
                "oracle_instance_id": 101,
                "delivery_semantics": "BE",
                "po_db_schema": "SAPPO",
                "interval_seconds": 300,
            },
            {
                "collector_id": "aae-eo",
                "oracle_instance_id": 102,
                "delivery_semantics": "EO",
                "po_db_schema": "SAPPO",
                "interval_seconds": 600,
            },
        ],
    )
    scheduler = CollectorScheduler(
        registry=FakeRegistry([value]),
        service=service,
        oracle_service=oracle_service,
        config=collector_settings(),
        clock=FakeClock(),
    )

    results = scheduler.run_once()

    assert service.calls == []
    assert [call[:2] for call in oracle_service.calls] == [
        ("P01", "aae-be"),
        ("P01", "aae-eo"),
    ]
    assert [result["collector_id"] for result in results] == ["aae-be", "aae-eo"]
    assert scheduler.next_delay() == 300


def test_oracle_profile_configuration_fails_fast_without_connections() -> None:
    value = server(
        "P01",
        profiles=[
            {
                "collector_id": "aae-be",
                "oracle_instance_id": 101,
                "po_db_schema": "SAPPO",
            }
        ],
    )
    scheduler = CollectorScheduler(
        registry=FakeRegistry([value]),
        service=FakeCollectorService(),
        oracle_service=FakeOracleCollectorService(),
        config=collector_settings(),
        clock=FakeClock(),
    )

    with pytest.raises(ValueError, match="Oracle connection"):
        scheduler.validate_configuration()
