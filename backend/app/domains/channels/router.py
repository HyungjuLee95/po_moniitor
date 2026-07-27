from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.security import require_permissions
from app.domains.channels.service import ChannelService
from app.domains.configuration.registry import ServerRegistry


router = APIRouter(prefix="/channels", tags=["Channels"])


class ChannelTarget(BaseModel):
    component_id: str = Field(min_length=1, max_length=256)
    channel_id: str = Field(min_length=1, max_length=256)


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
    rows = ChannelService().list_status(server)
    return {
        "data": rows,
        "meta": {
            "sid": server.sid,
            "count": len(rows),
            "source": "demo" if not settings.sap_po_live_mode else "sap-po-systatus",
        },
    }


@router.get("/inventory")
def channel_inventory(
    sid: str,
    component_id: str = Query(default="*", min_length=1, max_length=256),
    channel_pattern: str = Query(default="*", min_length=1, max_length=256),
    _: dict = Depends(require_permissions("channels:read")),
) -> dict:
    server = ServerRegistry().require_capability(sid, "monitor")
    rows = ChannelService().inventory(server, component_id, channel_pattern)
    return {"data": rows, "meta": {"sid": server.sid, "count": len(rows)}}


@router.get("/detail")
def channel_detail(
    sid: str,
    component_id: str,
    channel_id: str,
    _: dict = Depends(require_permissions("channels:read")),
) -> dict:
    server = ServerRegistry().require_capability(sid, "monitor")
    return {
        "data": ChannelService().detail(
            server, component_id, channel_id, include_password=False
        )
    }


@router.get("/detail-with-secret")
def channel_detail_with_secret(
    sid: str,
    component_id: str,
    channel_id: str,
    _: dict = Depends(require_permissions("channels:secrets")),
) -> dict:
    server = ServerRegistry().require_capability(sid, "monitor")
    return {
        "data": ChannelService().detail(
            server, component_id, channel_id, include_password=True
        )
    }


@router.post("/control")
def control_channels(
    payload: ChannelControlRequest,
    user: dict = Depends(require_permissions("channels:control")),
) -> dict:
    server = ServerRegistry().require_capability(payload.sid, "channel-control")
    allowed = settings.sap_control_allowed_sids
    if settings.sap_po_live_mode and (not allowed or server.sid not in allowed):
        raise HTTPException(
            status_code=403,
            detail=f"channel control is not enabled for SID {server.sid}",
        )
    result = ChannelService().control(server, payload.action, payload.channels)
    return {
        "data": {
            "sid": server.sid,
            "action": payload.action,
            "requested_by": user["username"],
            **result,
        }
    }
