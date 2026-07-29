import json
from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.security import require_permissions, require_server_access
from app.domains.channels.service import ChannelService
from app.domains.channels.bulk_service import ChannelBulkService
from app.domains.channels.monitoring_service import ChannelMonitoringService
from app.domains.configuration.registry import ServerRegistry


router = APIRouter(prefix="/channels", tags=["Channels"])


class ChannelTarget(BaseModel):
    component_id: str = Field(min_length=1, max_length=256)
    channel_id: str = Field(min_length=1, max_length=256)


class ChannelControlRequest(BaseModel):
    sid: str
    action: str = Field(pattern=r"^(START|STOP|CHECK|AUTOMATIC|MANUAL|EXTERNAL)$")
    channels: list[ChannelTarget] = Field(min_length=1, max_length=200)


class ChannelBatchControlRequest(BaseModel):
    sid: str
    action: str = Field(pattern=r"^(START|STOP|CHECK|AUTOMATIC|MANUAL|EXTERNAL)$")
    channel_list: str = Field(min_length=3, max_length=100_000)
    mode: str = Field(default="MASS", pattern=r"^(MASS|ONE)$")


@router.get("")
def list_channels(
    sid: str,
    _: dict = Depends(require_permissions("channels:read")),
    __: dict = Depends(require_server_access),
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
    __: dict = Depends(require_server_access),
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
    __: dict = Depends(require_server_access),
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
    __: dict = Depends(require_server_access),
) -> dict:
    server = ServerRegistry().require_capability(sid, "monitor")
    return {
        "data": ChannelService().detail(
            server, component_id, channel_id, include_password=True
        )
    }


@router.get("/statistics")
def channel_statistics(
    sid: str,
    channel_id: str = Query(min_length=1, max_length=256),
    _: dict = Depends(require_permissions("channels:read")),
    __: dict = Depends(require_server_access),
) -> dict:
    server = ServerRegistry().require_capability(sid, "monitor")
    return {
        "data": ChannelMonitoringService().statistics(server, channel_id),
        "meta": {
            "sid": server.sid,
            "channel_id": channel_id,
            "source": "rtims-oracle" if settings.rtims_configured else "demo",
        },
    }


@router.get("/message-history")
def channel_message_history(
    sid: str,
    channel_id: str = Query(min_length=1, max_length=256),
    limit: int = Query(default=50, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_permissions("channels:read")),
    __: dict = Depends(require_server_access),
) -> dict:
    server = ServerRegistry().require_capability(sid, "monitor")
    rows = ChannelMonitoringService().messages(
        server, channel_id, limit, offset
    )
    return {
        "data": rows,
        "meta": {
            "sid": server.sid,
            "channel_id": channel_id,
            "count": len(rows),
            "limit": limit,
            "offset": offset,
            "source": "rtims-oracle" if settings.rtims_configured else "demo",
        },
    }


@router.post("/control")
def control_channels(
    payload: ChannelControlRequest,
    user: dict = Depends(require_permissions("channels:control")),
) -> dict:
    allowed_sids = user.get("allowed_sids")
    if allowed_sids is not None and payload.sid.upper() not in allowed_sids:
        raise HTTPException(status_code=403, detail="server access denied")
    server = ServerRegistry().require_capability(payload.sid, "channel-control")
    allowed = settings.sap_control_allowed_sids
    if (
        settings.sap_po_live_mode
        and payload.action != "CHECK"
        and (not allowed or server.sid not in allowed)
    ):
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


def _authorize_control(sid: str, action: str, user: dict):
    allowed_sids = user.get("allowed_sids")
    if allowed_sids is not None and sid.upper() not in allowed_sids:
        raise HTTPException(status_code=403, detail="server access denied")
    server = ServerRegistry().require_capability(sid, "channel-control")
    allowed = settings.sap_control_allowed_sids
    if settings.sap_po_live_mode and action != "CHECK" and (
        not allowed or server.sid not in allowed
    ):
        raise HTTPException(status_code=403, detail="channel control is not enabled")
    return server


@router.post("/batch-control-stream")
def batch_control_stream(
    payload: ChannelBatchControlRequest,
    user: dict = Depends(require_permissions("channels:control")),
):
    server = _authorize_control(payload.sid, payload.action, user)
    targets = []
    for line in payload.channel_list.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = [part.strip() for part in stripped.split("|", 1)]
        if len(parts) != 2 or not all(parts):
            raise HTTPException(status_code=422, detail="channel_list must use Component|Channel")
        targets.append(ChannelTarget(component_id=parts[0], channel_id=parts[1]))
    if not targets or len(targets) > 1000:
        raise HTTPException(status_code=422, detail="channel count must be between 1 and 1000")

    def events():
        results = []
        try:
            for index, target in enumerate(targets, 1):
                result = ChannelService().control(server, payload.action, [target])
                item = result["results"][0]
                results.append(item)
                yield "data: " + json.dumps(
                    {
                        "type": "progress",
                        "current": index,
                        "total": len(targets),
                        "channel": f"{target.component_id}|{target.channel_id}",
                        "data": item,
                    },
                    default=str,
                ) + "\n\n"
            yield "data: " + json.dumps(
                {
                    "type": "complete",
                    "data": {
                        "requested": len(results),
                        "succeeded": sum(1 for item in results if item["success"]),
                        "failed": sum(1 for item in results if not item["success"]),
                        "results": results,
                    },
                },
                default=str,
            ) + "\n\n"
        except Exception:
            yield 'data: {"type":"error","message":"channel batch control failed"}\n\n'

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/bulk-export")
def bulk_export(
    sid: str,
    component_id: str = Query(default="*", min_length=1, max_length=256),
    channel_pattern: str = Query(default="*", min_length=1, max_length=256),
    _: dict = Depends(require_permissions("channels:secrets")),
    __: dict = Depends(require_server_access),
):
    server = ServerRegistry().require_capability(sid, "monitor")
    content = ChannelBulkService().export(server, component_id, channel_pattern)
    return StreamingResponse(
        BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="Channels_{server.sid}.xlsx"',
            "Cache-Control": "no-store",
        },
    )


@router.post("/bulk-preview")
async def bulk_preview(
    sid: str = Form(...),
    file: UploadFile = File(...),
    user: dict = Depends(require_permissions("channels:secrets")),
) -> dict:
    allowed_sids = user.get("allowed_sids")
    if allowed_sids is not None and sid.upper() not in allowed_sids:
        raise HTTPException(status_code=403, detail="server access denied")
    if not (file.filename or "").lower().endswith(".xlsx"):
        raise HTTPException(status_code=422, detail="xlsx file required")
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="file is too large")
    server = ServerRegistry().require_capability(sid, "monitor")
    return {"data": ChannelBulkService().preview(server, content)}
