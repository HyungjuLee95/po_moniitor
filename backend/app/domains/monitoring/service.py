from __future__ import annotations

import hashlib

from app.domains.configuration.registry import ServerRegistry


def _seed(sid: str) -> int:
    return int(hashlib.sha256(sid.encode()).hexdigest()[:6], 16)


class MonitoringService:
    def summary(self, sid: str) -> dict:
        server = ServerRegistry().require_capability(sid, "monitor")
        seed = _seed(server.sid)
        total = 180 + seed % 90
        errors = seed % 9
        stopped = seed % 5
        return {
            "sid": server.sid,
            "server_name": server.display_name,
            "channels": {
                "total": total,
                "running": total - errors - stopped,
                "error": errors,
                "stopped": stopped,
            },
            "messages_today": 12_000 + seed % 8_000,
            "success_rate": round(99.1 + (seed % 80) / 100, 2),
            "average_latency_ms": 80 + seed % 120,
            "source": "demo",
        }
