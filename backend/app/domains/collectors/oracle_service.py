from __future__ import annotations

from dataclasses import replace
import logging
from threading import Lock
from time import perf_counter

from app.core.config import PoServer, RtimsCollectorProfile
from app.domains.collectors.contracts import AaeMessage, utc_checkpoint_now
from app.integrations.rtims.collector_repository import OracleCollectorRepository
from app.integrations.sap_po.hana_collector import HanaAaeMessageSource


logger = logging.getLogger(__name__)
_state_lock = Lock()
_running_profiles: set[tuple[str, str]] = set()


class OracleRtimsCollectorService:
    def __init__(
        self,
        source: HanaAaeMessageSource | None = None,
        repository: OracleCollectorRepository | None = None,
    ) -> None:
        self.source = source or HanaAaeMessageSource()
        self.repository = repository or OracleCollectorRepository()

    def run(
        self,
        server: PoServer,
        profile: RtimsCollectorProfile,
        requested_by: str,
    ) -> dict:
        key = (server.sid, profile.collector_id)
        with _state_lock:
            if key in _running_profiles:
                return {
                    "sid": server.sid,
                    "collector_id": profile.collector_id,
                    "status": "SKIPPED",
                    "fetched": 0,
                    "requested_by": requested_by,
                    "detail": "collector profile is already running",
                }
            _running_profiles.add(key)

        started = perf_counter()
        try:
            checkpoint = self.repository.load_checkpoint(profile.oracle_instance_id)
            if checkpoint is None:
                checkpoint = utc_checkpoint_now(profile.initial_lookback_seconds)
            new_messages = self.source.fetch(server, profile, checkpoint)
            pending_ids = self.repository.load_pending_message_ids(
                server.sid,
                profile.delivery_semantics,
                profile.pending_search_minutes,
                profile.limit,
            )
            status_messages = self.source.fetch_status_updates(
                server,
                profile,
                pending_ids,
            )
            messages = new_messages + status_messages
            messages = _mark_duplicate_versions(messages)
            next_checkpoint = new_messages[-1].checkpoint if new_messages else checkpoint
            self.repository.persist_success(
                server.sid,
                profile,
                messages,
                next_checkpoint,
                started,
            )
            return {
                "sid": server.sid,
                "collector_id": profile.collector_id,
                "oracle_instance_id": profile.oracle_instance_id,
                "delivery_semantics": profile.delivery_semantics,
                "status": "SUCCESS",
                "fetched": len(messages),
                "new_rows": len(new_messages),
                "status_rows": len(status_messages),
                "elapsed_ms": round((perf_counter() - started) * 1000),
                "requested_by": requested_by,
                "source": "sap-po-hana",
                "target": "rtims-oracle",
                "checkpoint": {
                    "timestamp": next_checkpoint.timestamp,
                    "message_id": next_checkpoint.message_id,
                },
            }
        except Exception:
            try:
                self.repository.persist_failure(profile.oracle_instance_id, started)
            except Exception:
                logger.exception(
                    "RTIMS Collector failure log could not be stored for SID %s profile %s",
                    server.sid,
                    profile.collector_id,
                )
            raise
        finally:
            with _state_lock:
                _running_profiles.discard(key)


def _mark_duplicate_versions(messages: list[AaeMessage]) -> list[AaeMessage]:
    seen: set[str] = set()
    output = list(messages)
    for index in range(len(output) - 1, -1, -1):
        message_id = output[index].msg_id
        if message_id in seen:
            output[index] = replace(output[index], status="DLNG")
        else:
            seen.add(message_id)
    return output
