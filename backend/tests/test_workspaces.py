from app.domains.workspaces.repository import WorkspaceRepository
from app.domains.workspaces.service import WorkspaceService


def test_workspace_demo_lifecycle(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.domains.workspaces.repository.settings.demo_mode",
        True,
    )
    username = "workspace-test-user"
    repository = WorkspaceRepository()
    created = repository.create(
        username,
        {
            "task_name": "채널 제어 검증",
            "description": "POQ에서 검증",
            "progress": 10,
            "target_date": None,
        },
    )
    assert created is not None
    assert created["status"] == "planned"

    advanced = WorkspaceService().advance(username, created["workspace_id"])
    assert advanced is not None
    assert advanced["status"] == "in_progress"
    assert advanced["progress"] == 25

    assert repository.delete(username, created["workspace_id"]) is True
    assert repository.get(username, created["workspace_id"]) is None


def test_workspace_is_scoped_to_owner(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.domains.workspaces.repository.settings.demo_mode",
        True,
    )
    repository = WorkspaceRepository()
    created = repository.create(
        "workspace-owner-a",
        {
            "task_name": "소유자 전용 작업",
            "description": None,
            "progress": 0,
            "target_date": None,
        },
    )
    assert created is not None
    assert repository.get("workspace-owner-b", created["workspace_id"]) is None
