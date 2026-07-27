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
    def list_recent(self, server: PoServer, limit: int) -> list[dict]:
        now = datetime.now(timezone.utc)
        if not settings.sap_po_live_mode:
            return [
                {
                    "message_id": f"{server.sid}-{index:06d}",
                    "sid": server.sid,
                    "interface_name": f"IF_{server.sid}_ORDER_{index % 4 + 1}",
                    "status": "ERROR" if index % 11 == 0 else "SUCCESS",
                    "start_time": (now - timedelta(minutes=index * 3)).isoformat(),
                    "duration_ms": 420 + index * 37,
                }
                for index in range(1, limit + 1)
            ]
        timestamp = now - timedelta(minutes=settings.sap_message_lookback_minutes)
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
        return result

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
