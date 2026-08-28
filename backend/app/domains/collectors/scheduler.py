from __future__ import annotations

import logging
from threading import Event
from time import monotonic
from typing import Protocol

from app.core.config import Settings, settings
from app.domains.collectors.oracle_service import OracleRtimsCollectorService
from app.domains.collectors.service import CollectorService
from app.domains.configuration.registry import ServerRegistry


logger = logging.getLogger(__name__)


class StopEvent(Protocol):
    def is_set(self) -> bool: ...

    def wait(self, timeout: float | None = None) -> bool: ...


class CollectorScheduler:
    """Fixed-delay scheduler for Oracle profiles and the compatibility collector."""

    def __init__(
        self,
        registry: ServerRegistry | None = None,
        service: CollectorService | None = None,
        oracle_service: OracleRtimsCollectorService | None = None,
        config: Settings | None = None,
        clock=monotonic,
    ) -> None:
        self.registry = registry or ServerRegistry()
        self.service = service or CollectorService()
        self.oracle_service = oracle_service or OracleRtimsCollectorService()
        self.config = config or settings
        self.clock = clock
        self._next_due: dict[tuple[str, str], float] = {}

    def validate_configuration(self) -> None:
        servers = [
            server
            for server in self.registry.list_enabled()
            if server.enabled and "collector" in server.capabilities
        ]
        profiles = [
            (server, profile)
            for server in servers
            for profile in server.collectors
            if profile.enabled
        ]
        if not profiles:
            return
        if not self.config.rtims_collector_oracle_configured:
            raise ValueError("RTIMS Collector Oracle connection is not configured")
        for server, profile in profiles:
            hana_host = profile.hana_host.strip() or self.config.sap_hana_host.strip()
            hana_user = profile.hana_user.strip() or self.config.sap_hana_user.strip()
            hana_password = (
                profile.hana_password.get_secret_value()
                or self.config.sap_hana_password.get_secret_value()
            )
            if not profile.po_db_schema or not hana_host or not hana_user or not hana_password:
                raise ValueError(
                    f"RTIMS Collector profile is not fully configured for SID {server.sid} "
                    f"profile {profile.collector_id}"
                )

    def run_once(self) -> list[dict]:
        results: list[dict] = []
        active_keys: set[tuple[str, str]] = set()
        servers = [
            server
            for server in self.registry.list_enabled()
            if server.enabled and "collector" in server.capabilities
        ]
        for server in servers:
            profiles = [profile for profile in server.collectors if profile.enabled]
            if profiles:
                for profile in profiles:
                    key = (server.sid, profile.collector_id)
                    active_keys.add(key)
                    if self.clock() < self._next_due.get(key, 0):
                        continue
                    try:
                        results.append(
                            self.oracle_service.run(
                                server,
                                profile,
                                "system:rtims-collector",
                            )
                        )
                    except Exception:
                        logger.exception(
                            "Oracle RTIMS Collector run failed for SID %s profile %s",
                            server.sid,
                            profile.collector_id,
                        )
                        results.append(
                            {
                                "sid": server.sid,
                                "collector_id": profile.collector_id,
                                "status": "FAILED",
                                "fetched": 0,
                                "detail": "Oracle RTIMS Collector run failed",
                            }
                        )
                    finally:
                        self._next_due[key] = self.clock() + profile.interval_seconds
                continue

            key = (server.sid, "message-checkpoint")
            active_keys.add(key)
            if self.clock() < self._next_due.get(key, 0):
                continue
            try:
                results.append(
                    self.service.run(
                        server,
                        "system:rtims-collector",
                        limit=self.config.rtims_collector_limit,
                    )
                )
            except Exception:
                logger.exception("RTIMS collector run failed for SID %s", server.sid)
                results.append(
                    {
                        "sid": server.sid,
                        "status": "FAILED",
                        "fetched": 0,
                        "detail": "collector run failed",
                    }
                )
            finally:
                self._next_due[key] = (
                    self.clock() + self.config.rtims_collector_interval_seconds
                )
        self._next_due = {
            key: due for key, due in self._next_due.items() if key in active_keys
        }
        return results

    def next_delay(self) -> float:
        if not self._next_due:
            return float(self.config.rtims_collector_interval_seconds)
        remaining = min(self._next_due.values()) - self.clock()
        return max(1.0, remaining)

    def run(self, stop_event: StopEvent | Event) -> None:
        if stop_event.wait(self.config.rtims_collector_startup_delay_seconds):
            return
        while not stop_event.is_set():
            try:
                self.run_once()
            except Exception:
                logger.exception("RTIMS collector cycle failed before SID execution")
            if stop_event.wait(self.next_delay()):
                return
