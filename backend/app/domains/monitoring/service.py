from __future__ import annotations

import hashlib
from datetime import date, timedelta

from app.core.config import settings
from app.domains.channels.service import ChannelService
from app.domains.configuration.registry import ServerRegistry
from app.domains.configuration.policy_repository import MonitoringPolicyRepository
from app.domains.messages.service import MessageService
from app.integrations.rtims.repository import RtimsError, RtimsRepository


class MonitoringService:
    def summary(self, sid: str) -> dict:
        server = ServerRegistry().require_capability(sid, "monitor")
        policy = MonitoringPolicyRepository().get(server.sid)
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
                "failed_messages": 17 + seed % 21,
                "pending_messages": 8 + seed % 13,
                "success_rate": round(99.1 + (seed % 80) / 100, 2),
                "average_latency_ms": 80 + seed % 120,
                "latency_window_minutes": policy["response_window_minutes"],
                "source": "demo",
            }

        if settings.rtims_configured:
            rtims = RtimsRepository()
            message_summary = rtims.dashboard_summary(
                server.sid,
                policy["response_window_minutes"],
            )
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
                "failed_messages": message_summary["fail"],
                "pending_messages": message_summary["pending"],
                "success_rate": message_summary["success_rate"],
                "average_latency_ms": message_summary["average_latency_ms"],
                "latency_window_minutes": policy["response_window_minutes"],
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
            "failed_messages": sum(
                1 for row in messages
                if str(row.get("status", "")).upper() in {"F", "FAIL", "FAILED", "ERROR"}
            ),
            "pending_messages": sum(
                1 for row in messages
                if str(row.get("status", "")).upper() in {"P", "PENDING", "DELIVERING"}
            ),
            "success_rate": (
                round(successful_messages / len(messages) * 100, 2)
                if messages else 0.0
            ),
            "average_latency_ms": (
                round(sum(durations) / len(durations))
                if durations else 0
            ),
            "latency_window_minutes": policy["response_window_minutes"],
            "source": "sap-po",
        }

    def throughput(
        self,
        sid: str,
        granularity: str = "hour",
        days: int = 1,
    ) -> list[dict]:
        server = ServerRegistry().require_capability(sid, "monitor")
        if settings.rtims_configured:
            return RtimsRepository().message_throughput(
                server.sid,
                granularity,
                days,
            )
        seed = int(hashlib.sha256(server.sid.encode()).hexdigest()[:6], 16)
        if granularity == "day":
            today = date.today()
            return [
                {
                    "bucket": current.strftime("%Y%m%d"),
                    "label": current.strftime("%m-%d"),
                    "hour": None,
                    "total_count": 185_000 + ((seed + index * 13_739) % 90_000),
                    "success_count": 181_000 + ((seed + index * 13_703) % 87_000),
                    "fail_count": 80 + ((seed + index * 17) % 260),
                    "pending_count": 30 + ((seed + index * 11) % 140),
                    "total_size_bytes": (
                        185_000 + ((seed + index * 13_739) % 90_000)
                    ) * (2_100 + ((seed + index * 37) % 3_900)),
                }
                for index in range(days)
                for current in [today - timedelta(days=days - index - 1)]
            ]
        return [
            {
                "bucket": f"{date.today():%Y%m%d}{hour:02d}",
                "label": f"{hour:02d}:00",
                "hour": hour,
                "total_count": 8_000 + ((seed + hour * 1739) % 14_000),
                "success_count": 7_850 + ((seed + hour * 1703) % 13_700),
                "fail_count": 8 + ((seed + hour * 7) % 35),
                "pending_count": 4 + ((seed + hour * 5) % 22),
                "total_size_bytes": (
                    8_000 + ((seed + hour * 1739) % 14_000)
                ) * (2_100 + ((seed + hour * 37) % 3_900)),
            }
            for hour in range(24)
        ]

    def slow_messages(self, sid: str) -> dict:
        server = ServerRegistry().require_capability(sid, "monitor")
        policy = MonitoringPolicyRepository().get(server.sid)
        rows: list[dict] | None = None
        if settings.rtims_configured:
            try:
                rows = RtimsRepository().slow_messages(
                    server.sid,
                    policy["response_window_minutes"],
                    policy["slow_threshold_ms"],
                    policy["max_detail_rows"],
                )
            except RtimsError:
                if not settings.demo_mode:
                    raise
        if rows is None:
            threshold_seconds = policy["slow_threshold_ms"] / 1000
            rows = [
                {
                    "log_id": index,
                    "message_id": f"MSG-{server.sid}-SLOW-{index:03d}",
                    "status": "S" if index > 1 else "F",
                    "start_time": None,
                    "elapsed_sec": round(threshold_seconds + index * 0.841, 3),
                    "interface_name": f"IF_{server.sid}_{'ORDER' if index == 1 else 'MASTER'}",
                    "source_system": "ERP",
                    "target_system": "MES",
                }
                for index in range(1, 4)
            ]
        return {"items": rows, "policy": policy}

    def performance(self, sid: str, hours: int) -> list[dict]:
        server = ServerRegistry().require_capability(sid, "monitor")
        if settings.rtims_configured:
            return RtimsRepository().interface_performance(server.sid, hours)
        return [
            {
                "interface_name": f"IF_{server.sid}_ORDER",
                "source_system": "ERP",
                "target_system": "MES",
                "total_count": 8421,
                "success_count": 8368,
                "fail_count": 17,
                "pending_count": 36,
                "success_rate": 99.37,
                "avg_latency_ms": 428.0,
                "max_latency_ms": 1842.0,
            },
            {
                "interface_name": f"IF_{server.sid}_MASTER",
                "source_system": "MDM",
                "target_system": "ERP",
                "total_count": 3120,
                "success_count": 3118,
                "fail_count": 2,
                "pending_count": 0,
                "success_rate": 99.94,
                "avg_latency_ms": 216.0,
                "max_latency_ms": 782.0,
            },
        ]

    def resources(self, sid: str) -> list[dict]:
        server = ServerRegistry().require_capability(sid, "monitor")
        if settings.rtims_configured:
            return RtimsRepository().resource_summary(server.sid)
        return [
            {
                "server_id": server.sid,
                "resource_id": 1,
                "resource_type": "CPU",
                "resource_name": "Java CPU",
                "node": "node-1",
                "recent_usage": 34.8,
                "max_usage": 68.2,
                "max_limit": 100,
            },
            {
                "server_id": server.sid,
                "resource_id": 2,
                "resource_type": "MEMORY",
                "resource_name": "JVM Heap",
                "node": "node-1",
                "recent_usage": 61.4,
                "max_usage": 78.9,
                "max_limit": 100,
            },
        ]

    def queues(self, sid: str) -> dict:
        server = ServerRegistry().require_capability(sid, "monitor")
        if settings.rtims_configured:
            return RtimsRepository().queue_summary(server.sid)
        return {
            "adapter_engine": [
                {
                    "servernode": "node-1",
                    "queuename": "MessagingSystem",
                    "conname": "default",
                    "started": "Y",
                    "num_entries": 12,
                    "threads_assigned": 8,
                    "threads_working": 3,
                    "max_thread": 16,
                }
            ],
            "integration_engine": [
                {"client_id": "100", "direction": "I", "normal": 24, "warning": 2, "fail": 0}
            ],
        }

    def system_statistics(self, sid: str, hours: int) -> list[dict]:
        server = ServerRegistry().require_capability(sid, "monitor")
        if settings.rtims_configured:
            return RtimsRepository().system_statistics(server.sid, hours)
        return [
            {
                "group_id": 1,
                "system_name": "ERP Integration",
                "success_count": 8120,
                "fail_count": 14,
                "pending_count": 31,
                "closed_count": 0,
                "total_count": 8165,
                "success_rate": 99.45,
                "fail_rate": 0.17,
            }
        ]

    def system_queue_status(self, sid: str) -> list[dict]:
        server = ServerRegistry().require_capability(sid, "monitor")
        if settings.rtims_configured:
            return RtimsRepository().system_queue_status(server.sid)
        return [
            {
                "server_id": server.sid,
                "client_id": "100",
                "normal": 24,
                "warning": 2,
                "fail": 0,
            }
        ]
