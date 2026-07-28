from __future__ import annotations

from app.domains.workspaces.repository import WorkspaceRepository


NEXT_STATUS = {
    "planned": ("in_progress", 25),
    "in_progress": ("review", 80),
    "review": ("completed", 100),
}


class WorkspaceService:
    def __init__(self) -> None:
        self.repository = WorkspaceRepository()

    def advance(self, username: str, workspace_id: int) -> dict | None:
        current = self.repository.get(username, workspace_id)
        if current is None:
            return None
        transition = NEXT_STATUS.get(current["status"])
        if transition is None:
            return current
        status, minimum_progress = transition
        progress = max(int(current["progress"]), minimum_progress)
        return self.repository.advance(username, workspace_id, status, progress)
