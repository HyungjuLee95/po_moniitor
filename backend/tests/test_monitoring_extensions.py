import json

from app.core.config import PoServer
from app.domains.monitoring.service import MonitoringService


def test_monitoring_extension_demo_contracts(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.domains.monitoring.service.settings.rtims_enabled",
        False,
    )
    monkeypatch.setattr(
        "app.domains.monitoring.service.settings.po_servers_json",
        json.dumps(
            [{
                "sid": "POP",
                "display_name": "Production",
                "environment": "production",
                "base_url": "https://example.internal",
                "capabilities": ["monitor"],
            }]
        ),
    )
    service = MonitoringService()
    performance = service.performance("POP", 24)
    resources = service.resources("POP")
    queues = service.queues("POP")
    throughput = service.throughput("POP")
    daily_throughput = service.throughput("POP", "day", 7)

    assert performance[0]["avg_latency_ms"] >= 0
    assert resources[0]["resource_type"] == "CPU"
    assert "adapter_engine" in queues
    assert len(throughput) == 24
    assert throughput[0]["total_count"] > 0
    assert throughput[0]["total_size_bytes"] > 0
    assert len(daily_throughput) == 7
    assert daily_throughput[0]["hour"] is None


def test_topology_demo_contract(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.domains.interfaces.service.settings.rtims_enabled",
        False,
    )
    from app.domains.interfaces.service import InterfaceService

    server = PoServer(
        sid="POP",
        display_name="Production",
        environment="production",
        base_url="https://example.internal",
    )
    rows = InterfaceService().topology(server)
    assert rows[0]["source_system"]
    assert rows[0]["target_system"]
