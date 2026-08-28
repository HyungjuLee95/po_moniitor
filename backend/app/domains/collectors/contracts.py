from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class CollectorCheckpoint:
    timestamp: str
    message_id: str = ""


@dataclass(frozen=True)
class AaeMessage:
    msg_id: str
    direction: str
    ref_msg_id: str | None
    status: str | None
    to_service_name: str | None
    to_service_type: str | None
    from_service_name: str | None
    from_service_type: str | None
    action_name: str | None
    action_type: str | None
    delivery_semantics: str
    sent_recv_time: str
    tran_delv_time: str
    schedule_time: str | None
    persist_until: str | None
    transport: str | None
    node: str | None
    error_code: str | None
    error_category: str | None
    recv_action_name: str | None
    recv_action_type: str | None
    bytes_length: int | None
    host_id: str | None
    checkpoint_time: str

    @classmethod
    def from_mapping(cls, row: dict) -> "AaeMessage":
        return cls(
            msg_id=str(row.get("msg_id") or ""),
            direction=str(row.get("direction") or ""),
            ref_msg_id=_optional_string(row.get("ref_to_msg_id")),
            status=_optional_string(row.get("status")),
            to_service_name=_optional_string(row.get("to_service_name")),
            to_service_type=_optional_string(row.get("to_service_type")),
            from_service_name=_optional_string(row.get("from_service_name")),
            from_service_type=_optional_string(row.get("from_service_type")),
            action_name=_optional_string(row.get("action_name")),
            action_type=_optional_string(row.get("action_type")),
            delivery_semantics=str(row.get("delivery_semantics") or ""),
            sent_recv_time=str(row.get("sent_recv_time") or ""),
            tran_delv_time=str(row.get("tran_delv_time") or ""),
            schedule_time=_optional_string(row.get("schedule_time")),
            persist_until=_optional_string(row.get("persist_until")),
            transport=_optional_string(row.get("transport")),
            node=_optional_string(row.get("node")),
            error_code=_optional_string(row.get("error_code")),
            error_category=_optional_string(row.get("error_category")),
            recv_action_name=_optional_string(row.get("recv_action_name")),
            recv_action_type=_optional_string(row.get("recv_action_type")),
            bytes_length=(
                int(row["bytes_length"])
                if row.get("bytes_length") is not None
                else None
            ),
            host_id=_optional_string(row.get("host_id")),
            checkpoint_time=str(row.get("checkpoint_time") or ""),
        )

    @property
    def checkpoint(self) -> CollectorCheckpoint:
        return CollectorCheckpoint(self.checkpoint_time, self.msg_id)


def utc_checkpoint_now(lookback_seconds: int = 0) -> CollectorCheckpoint:
    from datetime import timedelta

    value = datetime.now(timezone.utc) - timedelta(seconds=lookback_seconds)
    return CollectorCheckpoint(value.strftime("%Y%m%d%H%M%S%f")[:17], "")


def _optional_string(value) -> str | None:
    return None if value is None else str(value)
