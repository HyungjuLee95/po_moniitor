from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.security import require_permissions
from app.domains.configuration.registry import ServerRegistry


router = APIRouter(prefix="/channels", tags=["Channels"])


class ChannelTarget(BaseModel):
    component_id: str
    channel_id: str


class ChannelControlRequest(BaseModel):
    sid: str
    action: str = Field(pattern=r"^(START|STOP)$")
    channels: list[ChannelTarget] = Field(min_length=1, max_length=200)


@router.get("")
def list_channels(
    sid: str,
    _: dict = Depends(require_permissions("channels:read")),
) -> dict:
    server = ServerRegistry().require_capability(sid, "monitor")
    rows = [
        {
            "id": index,
            "sid": server.sid,
            "component_id": f"BS_{server.sid}",
            "channel_id": channel,
            "direction": direction,
            "status": status,
            "latency_ms": latency,
        }
        for index, (channel, direction, status, latency) in enumerate(
            [
                ("REST_Receiver_EMPLOYEE_SYNC", "Receiver", "Running", 61),
                ("JDBC_Sender_MASTER_DATA", "Sender", "Running", 42),
                ("SOAP_Sender_ORDER_STATUS", "Sender", "Error", None),
                ("FILE_Receiver_BATCH", "Receiver", "Stopped", None),
            ],
            start=1,
        )
    ]
    return {"data": rows, "meta": {"sid": server.sid, "source": "demo"}}


@router.post("/control")
def control_channels(
    payload: ChannelControlRequest,
    user: dict = Depends(require_permissions("channels:control")),
) -> dict:
    server = ServerRegistry().require_capability(payload.sid, "channel-control")
    return {
        "data": {
            "sid": server.sid,
            "action": payload.action,
            "requested": len(payload.channels),
            "succeeded": len(payload.channels),
            "failed": 0,
            "requested_by": user["username"],
            "source": "demo",
        }
    }
