import pytest
from pydantic import ValidationError

from app.domains.dashboard.router import DashboardLayout


def test_default_dashboard_layout_contains_every_widget() -> None:
    layout = DashboardLayout()
    assert set(layout.order) == {
        "health",
        "throughput",
        "channel_status",
        "incidents",
        "server_profile",
    }
    assert layout.hidden == []
    assert layout.density == "comfortable"


def test_dashboard_layout_rejects_duplicate_widget() -> None:
    with pytest.raises(ValidationError):
        DashboardLayout(
            order=[
                "health",
                "health",
                "channel_status",
                "incidents",
                "server_profile",
            ]
        )
