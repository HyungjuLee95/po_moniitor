from __future__ import annotations

import hashlib

from app.core.config import settings
from app.domains.channels.service import ChannelService
from app.domains.configuration.registry import ServerRegistry
from app.domains.messages.service import MessageService
from app.integrations.rtims.repository import RtimsRepository


class MonitoringService:
    def summary(self, sid: str) -> dict:
        server = ServerRegistry().require_capability(sid, "monitor")
        if not settings.sap_po_live_mode:
            seed = int(hashlib.sha256(server.sid.encode()).hexdigest()[:6], 16)
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

        if settings.rtims_configured:
            rtims = RtimsRepository()
            message_summary = rtims.dashboard_summary(server.sid, 24)
            channel_summary = rtims.channel_summary(server.sid)
            total_channels = sum(channel_summary.values())
            errors = channel_summary.get("ERROR", 0) + channel_summary.get("WARNING", 0)
            stopped = channel_summary.get("STOPPED", 0)
            return {
                "sid": server.sid,
                "server_name": server.display_name,
                "channels": {
                    "total": total_channels,
                    "running": channel_summary.get("OK", 0),
                    "error": errors,
                    "stopped": stopped,
                },
                "messages_today": message_summary["total"],
                "success_rate": message_summary["success_rate"],
                "average_latency_ms": message_summary["average_latency_ms"],
                "source": "rtims-oracle",
            }

        channels = ChannelService().list_status(server)
        messages = MessageService().list_recent(server, 1000)
        errors = sum(
            1 for row in channels
            if str(row.get("status", "")).lower() == "error"
        )
        stopped = sum(
            1 for row in channels
            if str(row.get("status", "")).lower() == "stopped"
        )
        successful_messages = sum(
            1 for row in messages
            if str(row.get("status", "")).upper() in {"SUCCESS", "DLVD", "DELIVERED"}
        )
        durations = [
            float(row["duration_ms"])
            for row in messages
            if isinstance(row.get("duration_ms"), (int, float))
        ]
        return {
            "sid": server.sid,
            "server_name": server.display_name,
            "channels": {
                "total": len(channels),
                "running": len(channels) - errors - stopped,
                "error": errors,
                "stopped": stopped,
            },
            "messages_today": len(messages),
            "success_rate": (
                round(successful_messages / len(messages) * 100, 2)
                if messages else 0.0
            ),
            "average_latency_ms": (
                round(sum(durations) / len(durations))
                if durations else 0
            ),
            "source": "sap-po",
        }
