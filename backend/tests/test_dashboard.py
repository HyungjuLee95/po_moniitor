import pytest
from pydantic import ValidationError

from app.domains.dashboard.router import DashboardLayout


def test_default_dashboard_layout_contains_every_widget() -> None:
    layout = DashboardLayout()
    assert set(layout.order) == {
        "health",
        "throughput",
        "system_results",
        "queue_status",
        "live_interfaces",
        "daily_checks",
        "channel_status",
        "incidents",
        "server_profile",
    }
    assert layout.hidden == ["channel_status", "server_profile"]
    assert layout.density == "comfortable"
    assert layout.favorite_views == []


def test_dashboard_layout_rejects_duplicate_widget() -> None:
    with pytest.raises(ValidationError):
        DashboardLayout(
            order=[
                "health",
                "health",
            ]
        )


def test_dashboard_layout_upgrades_old_preferences_and_tracks_views() -> None:
    layout = DashboardLayout.model_validate({
        "order": ["health", "throughput", "channel_status", "incidents", "server_profile"],
        "hidden": [],
        "density": "compact",
        "favorite_views": ["realtime_interfaces"],
        "recent_views": ["daily_checks"],
        "view_usage": {"daily_checks": 4},
    })
    assert set(layout.order) >= {"system_results", "queue_status", "live_interfaces", "daily_checks"}
    assert layout.favorite_views == ["realtime_interfaces"]
    assert layout.view_usage["daily_checks"] == 4
