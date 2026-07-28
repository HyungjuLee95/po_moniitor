from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.config import PoServer, settings
from app.integrations.rtims.repository import RtimsRepository


class ChannelMonitoringService:
    def statistics(self, server: PoServer, channel_id: str) -> dict:
        if settings.rtims_configured:
            return RtimsRepository().channel_statistics(server.sid, channel_id)
        return {
            "total_count": 1842,
            "success_count": 1827,
            "fail_count": 9,
            "pending_count": 6,
            "avg_elapsed_sec": 0.428,
            "total_msg_size": 24_810_442,
            "avg_msg_size": 13_469.3,
        }

    def messages(
        self,
        server: PoServer,
        channel_id: str,
        limit: int,
        offset: int,
    ) -> list[dict]:
        if settings.rtims_configured:
            return RtimsRepository().channel_messages(
                server.sid, channel_id, limit, offset
            )
        now = datetime.now(timezone.utc)
        return [
            {
                "log_id": offset + index + 1,
                "message_id": f"{server.sid}-{channel_id[:8]}-{offset + index + 1:06d}",
                "status": "F" if (offset + index + 1) % 11 == 0 else "S",
                "server_id": server.sid,
                "start_time": (
                    now - timedelta(minutes=(offset + index) * 4)
                ).isoformat(),
                "elapsed_sec": round(0.18 + index * 0.037, 3),
                "msg_size": 4096 + index * 512,
            }
            for index in range(limit)
        ]
