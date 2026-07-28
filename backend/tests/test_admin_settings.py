import json

import pytest
from fastapi import HTTPException

from app.core.security import require_server_access
from app.domains.auth.repository import UserRepository, hash_password, verify_password
from app.domains.configuration.policy_repository import MonitoringPolicyRepository
from app.domains.monitoring.service import MonitoringService


def test_password_hash_round_trip() -> None:
    encoded = hash_password("temporary-password")
    assert verify_password("temporary-password", encoded)
    assert not verify_password("wrong-password", encoded)
    assert "temporary-password" not in encoded


def test_demo_user_role_lifecycle(monkeypatch) -> None:
    monkeypatch.setattr("app.domains.auth.repository.settings.demo_mode", True)
    repository = UserRepository()
    username = "test_manager"
    try:
        created = repository.create_user(
            username,
            "Test Manager",
            "temporary-password",
            "OPERATOR",
            ["POP"],
            "admin",
        )
        assert created["role"] == "OPERATOR"
        updated = repository.update_user(
            username,
            "Test Manager",
            "VIEWER",
            True,
            ["POQ"],
            "admin",
        )
        assert updated["role"] == "VIEWER"
        assert updated["server_sids"] == ["POQ"]
    finally:
        from app.domains.auth import repository as module
        module._demo_users.pop(username, None)


def test_monitoring_policy_controls_slow_message_contract(monkeypatch) -> None:
    monkeypatch.setattr("app.domains.configuration.policy_repository.settings.demo_mode", True)
    monkeypatch.setattr("app.domains.monitoring.service.settings.rtims_enabled", False)
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
    repository = MonitoringPolicyRepository()
    policy = repository.save(
        "POP",
        {
            "response_window_minutes": 30,
            "slow_threshold_ms": 2500,
            "critical_threshold_ms": 9000,
            "max_detail_rows": 50,
        },
        "admin",
    )
    result = MonitoringService().slow_messages("POP")
    assert policy["response_window_minutes"] == 30
    assert result["policy"]["slow_threshold_ms"] == 2500
    assert all(row["elapsed_sec"] >= 2.5 for row in result["items"])


def test_server_scope_is_enforced() -> None:
    user = {"username": "viewer", "role": "VIEWER", "allowed_sids": ["POQ"]}
    assert require_server_access("POQ", user)["username"] == "viewer"
    with pytest.raises(HTTPException) as exc:
        require_server_access("POP", user)
    assert exc.value.status_code == 403


def test_admin_routes_are_in_openapi() -> None:
    from app.main import app

    paths = app.openapi()["paths"]
    assert "/api/v1/auth/users" in paths
    assert "/api/v1/auth/users/{username}" in paths
    assert "/api/v1/configuration/monitoring-policy" in paths
    assert "/api/v1/monitoring/slow-messages" in paths
