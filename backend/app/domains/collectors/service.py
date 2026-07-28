from __future__ import annotations

from threading import Lock
from time import perf_counter

from app.core.config import settings
from app.domains.collectors.repository import CollectorRepository
from app.domains.messages.service import MessageService


_state_lock = Lock()
_running_sids: set[str] = set()


class CollectorService:
    def run(self, server, username: str) -> dict:
        with _state_lock:
            if server.sid in _running_sids:
                return {
                    "sid": server.sid,
                    "status": "SKIPPED",
                    "fetched": 0,
                    "requested_by": username,
                    "detail": "collector is already running",
                }
            _running_sids.add(server.sid)

        started = perf_counter()
        repository = CollectorRepository()
        try:
            rows = MessageService().list_recent(server, 1000)
            elapsed_ms = round((perf_counter() - started) * 1000)
            repository.save(server, "SUCCESS", len(rows), elapsed_ms)
            return {
                "sid": server.sid,
                "status": "SUCCESS",
                "fetched": len(rows),
                "elapsed_ms": elapsed_ms,
                "requested_by": username,
                "source": "demo" if not settings.sap_po_live_mode else "sap-po-aae-monitor",
            }
        except Exception:
            elapsed_ms = round((perf_counter() - started) * 1000)
            repository.save(
                server,
                "FAILED",
                0,
                elapsed_ms,
                "SAP PO collector request failed",
            )
            raise
        finally:
            with _state_lock:
                _running_sids.discard(server.sid)
