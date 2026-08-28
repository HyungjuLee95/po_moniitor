from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.security import require_permissions
from app.domains.collectors.oracle_service import OracleRtimsCollectorService
from app.domains.collectors.repository import CollectorRepository
from app.domains.collectors.service import CollectorService
from app.domains.configuration.registry import ServerRegistry
from app.integrations.rtims.collector_repository import OracleCollectorRepository


router = APIRouter(prefix="/collectors", tags=["Collectors"])


class CollectorRunRequest(BaseModel):
    sids: list[str] = Field(default_factory=list, max_length=20)
    collector_ids: list[str] = Field(default_factory=list, max_length=50)


@router.get("")
def collector_status(
    user: dict = Depends(require_permissions("collectors:read")),
) -> dict:
    allowed_sids = user.get("allowed_sids")
    servers = [
        server for server in ServerRegistry().list_enabled()
        if "collector" in server.capabilities
        and (allowed_sids is None or server.sid in allowed_sids)
    ]
    profile_count = sum(
        1
        for server in servers
        for profile in server.collectors
        if profile.enabled
    )
    oracle_servers = [server for server in servers if any(p.enabled for p in server.collectors)]
    compatibility_servers = [server for server in servers if not any(p.enabled for p in server.collectors)]
    data = (
        CollectorRepository().list(compatibility_servers)
        if compatibility_servers
        else []
    )
    if oracle_servers:
        if settings.rtims_collector_oracle_configured:
            data.extend(OracleCollectorRepository().list_status(oracle_servers))
        else:
            data.extend(_unconfigured_profile_status(oracle_servers))
    return {
        "data": data,
        "meta": {
            "automatic_enabled": settings.rtims_collector_enabled,
            "startup_delay_seconds": settings.rtims_collector_startup_delay_seconds,
            "interval_seconds": settings.rtims_collector_interval_seconds,
            "limit": settings.rtims_collector_limit,
            "pipeline": (
                "sap-po-hana-to-rtims-oracle"
                if profile_count
                else "sap-po-message-checkpoint"
            ),
            "profile_count": profile_count,
            "oracle_configured": settings.rtims_collector_oracle_configured,
        },
    }


@router.post("/run")
def run_collectors(
    payload: CollectorRunRequest,
    user: dict = Depends(require_permissions("collectors:run")),
) -> dict:
    requested = payload.sids or [
        server.sid for server in ServerRegistry().list_enabled()
        if "collector" in server.capabilities
    ]
    allowed_sids = user.get("allowed_sids")
    if allowed_sids is not None and not set(requested).issubset(allowed_sids):
        raise HTTPException(status_code=403, detail="server access denied")
    servers = [
        ServerRegistry().require_capability(sid, "collector")
        for sid in dict.fromkeys(requested)
    ]
    results = []
    for server in servers:
        configured_profiles = [
            profile
            for profile in server.collectors
            if profile.enabled
        ]
        profiles = [
            profile
            for profile in configured_profiles
            if (
                not payload.collector_ids
                or profile.collector_id in payload.collector_ids
            )
        ]
        if configured_profiles:
            if not profiles:
                raise HTTPException(
                    status_code=404,
                    detail=f"collector profile not found for SID {server.sid}",
                )
            for profile in profiles:
                results.append(
                    OracleRtimsCollectorService().run(
                        server,
                        profile,
                        user["username"],
                    )
                )
        else:
            results.append(CollectorService().run(server, user["username"]))
    return {
        "data": results,
        "meta": {"execution": "sequential"},
    }


def _unconfigured_profile_status(servers: list) -> list[dict]:
    return [
        {
            "sid": server.sid,
            "server_name": server.display_name,
            "collector_id": profile.collector_id,
            "oracle_instance_id": profile.oracle_instance_id,
            "delivery_semantics": profile.delivery_semantics,
            "status": "CONFIG_REQUIRED",
            "last_run_at": None,
            "last_success_at": None,
            "last_window_end": None,
            "checkpoint_message_id": None,
            "item_count": 0,
            "elapsed_ms": 0,
            "detail": "RTIMS Collector Oracle connection is not configured",
        }
        for server in servers
        for profile in server.collectors
        if profile.enabled
    ]
