from __future__ import annotations

from fastapi import HTTPException

from app.core.config import PoServer, settings


class ServerRegistry:
    def list_enabled(self) -> list[PoServer]:
        return [server for server in settings.po_servers if server.enabled]

    def get(self, sid: str) -> PoServer:
        normalized = sid.upper()
        server = next(
            (item for item in settings.po_servers if item.sid == normalized and item.enabled),
            None,
        )
        if server is None:
            raise HTTPException(status_code=404, detail=f"unknown server sid: {normalized}")
        return server

    def require_capability(self, sid: str, capability: str) -> PoServer:
        server = self.get(sid)
        if capability not in server.capabilities:
            raise HTTPException(
                status_code=409,
                detail=f"{server.sid} does not support capability: {capability}",
            )
        return server
