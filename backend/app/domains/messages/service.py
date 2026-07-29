from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.config import PoServer, settings
from app.integrations.sap_po.client import call, soap_client
from app.integrations.sap_po.normalize import (
    iso_value,
    pick,
    records,
    recursive_values,
)


class MessageService:
    def list_recent(
        self,
        server: PoServer,
        limit: int,
        hours: int | None = None,
        status: str | None = None,
        keyword: str | None = None,
    ) -> list[dict]:
        now = datetime.now(timezone.utc)
        if not settings.sap_po_live_mode:
            rows = [
                {
                    "message_id": f"{server.sid}-{index:06d}",
                    "sid": server.sid,
                    "interface_name": (
                        f"HRD_{server.sid}_{index % 4 + 1}"
                        if index % 5 == 0
                        else f"IF_{server.sid}_ORDER_{index % 4 + 1}"
                    ),
                    "status": (
                        "DELIVERING"
                        if index % 13 == 0
                        else ("ERROR" if index % 11 == 0 else "SUCCESS")
                    ),
                    "start_time": (now - timedelta(minutes=index * 3)).isoformat(),
                    "duration_ms": 420 + index * 37,
                }
                for index in range(1, limit + 1)
            ]
            return self._filter(rows, status, keyword)[:limit]
        lookback_minutes = (
            hours * 60 if hours is not None else settings.sap_message_lookback_minutes
        )
        timestamp = now - timedelta(minutes=lookback_minutes)
        cursor = timestamp.strftime("%Y%m%d%H%M%S") + "000"
        client = soap_client(server.sid, "aae_monitor")
        response = call(
            client.service.getMessageLogs,
            cursor,
            settings.sap_aae_delivery_semantics,
            settings.sap_aae_host_id_table,
            settings.sap_aae_host_id_field,
            limit,
        )
        result = []
        for row in records(
            response,
            ("messageId", "msgGuid", "msgStatus", "tranDelvTime", "sentRecvTime"),
        )[:limit]:
            start = pick(row, "sentRecvTime", "tranDelvTime", "startTime")
            end = pick(row, "tranDelvTime", "endTime")
            result.append(
                {
                    "message_id": str(pick(row, "messageId", "msgGuid", "msgId", default="")),
                    "sid": server.sid,
                    "interface_name": str(
                        pick(row, "interfaceName", "obIntfNm", "ibIntfNm", default="")
                    ),
                    "namespace": str(pick(row, "interfaceNamespace", "namespace", default="")),
                    "status": str(pick(row, "msgStatus", "status", default="UNKNOWN")),
                    "start_time": iso_value(start),
                    "end_time": iso_value(end),
                    "duration_ms": pick(row, "durationMs", "elapsedTime"),
                    "source_system": pick(row, "senderService", "obSystem"),
                    "target_system": pick(row, "receiverService", "ibSystem"),
                    "error_text": pick(row, "errorText", "errorCategory"),
                }
            )
        return self._filter(result, status, keyword)[:limit]

    @staticmethod
    def _filter(
        rows: list[dict],
        status: str | None,
        keyword: str | None,
    ) -> list[dict]:
        normalized_status = (status or "").strip().upper()
        aliases = {
            "SUCCESS": {"S", "SUCCESS", "DELIVERED", "DLVD"},
            "FAILED": {"F", "FAIL", "FAILED", "ERROR"},
            "DELIVERING": {"P", "PENDING", "DELIVERING"},
        }
        allowed = aliases.get(normalized_status, {normalized_status})
        normalized_keyword = (keyword or "").strip().lower()
        return [
            row for row in rows
            if (
                not normalized_status
                or str(row.get("status", "")).upper() in allowed
            )
            and (
                not normalized_keyword
                or normalized_keyword in " ".join(
                    str(row.get(key, "") or "").lower()
                    for key in ("interface_name", "source_system", "target_system")
                )
            )
        ]

    def audit(self, server: PoServer, message_id: str) -> list[dict]:
        if not settings.sap_po_live_mode:
            return []
        client = soap_client(server.sid, "adapter_monitor")
        messages = call(
            client.service.getMessagesByIDs,
            messageIds=[message_id],
        )
        keys = recursive_values(messages, "messageKey")
        logs: list[dict] = []
        for key in dict.fromkeys(str(value) for value in keys if value):
            response = call(
                client.service.getLogEntries,
                messageKey=key,
                maxResults=100,
                olderThan=datetime.now(timezone.utc),
            )
            for row in records(response, ("status", "timeStamp", "localizedText")):
                logs.append(
                    {
                        "message_id": message_id,
                        "sid": server.sid,
                        "status": str(pick(row, "status", default="")),
                        "time": iso_value(pick(row, "timeStamp", "time")),
                        "text": str(pick(row, "localizedText", "text", default="")),
                    }
                )
        return logs
