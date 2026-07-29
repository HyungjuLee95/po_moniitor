from contextlib import asynccontextmanager
from threading import Event, Thread

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import check_database
from app.domains.auth.router import router as auth_router
from app.domains.alerts.router import router as alerts_router
from app.domains.channels.router import router as channels_router
from app.domains.collectors.router import router as collectors_router
from app.domains.configuration.router import router as configuration_router
from app.domains.configuration.repository import ConfigurationRepository
from app.domains.configuration.registry import ServerRegistry
from app.domains.incidents.router import router as incidents_router
from app.domains.interfaces.router import router as interfaces_router
from app.domains.messages.router import router as messages_router
from app.domains.monitoring.router import router as monitoring_router
from app.domains.workspaces.router import router as workspaces_router
from app.integrations.sap_po.errors import SapPoError
from app.integrations.rtims.repository import RtimsError
from app.domains.dashboard.router import router as dashboard_router
from app.domains.llm_search.router import router as llm_search_router
from app.domains.hrd.router import router as hrd_router
from app.domains.oracle_ifs.router import router as oracle_ifs_router
from app.domains.posts.router import router as posts_router
from app.domains.oracle_ifs.service import OracleIfsService


@asynccontextmanager
async def lifespan(_: FastAPI):
    ifs_stop = Event()
    ifs_thread = None
    if settings.database_connect_on_startup and not settings.demo_mode:
        check_database()
        ConfigurationRepository().sync_servers(ServerRegistry().list_enabled())
    if settings.ifs_sync_scheduler_enabled and settings.ifs_oracle_configured:
        ifs_thread = Thread(
            target=OracleIfsService().run_scheduler,
            args=(ifs_stop,),
            name="oracle-ifs-sync",
            daemon=True,
        )
        ifs_thread.start()
    try:
        yield
    finally:
        ifs_stop.set()
        if ifs_thread is not None:
            ifs_thread.join(timeout=5)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="SAP PO monitoring and operations API",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(SapPoError)
def sap_po_error_handler(_, exc: SapPoError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(RtimsError)
def rtims_error_handler(_, exc: RtimsError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": str(exc)})

for router in (
    auth_router,
    configuration_router,
    dashboard_router,
    monitoring_router,
    channels_router,
    messages_router,
    incidents_router,
    alerts_router,
    llm_search_router,
    collectors_router,
    interfaces_router,
    workspaces_router,
    hrd_router,
    oracle_ifs_router,
    posts_router,
):
    app.include_router(router, prefix=settings.api_prefix)


@app.get("/health", tags=["System"])
def health() -> dict:
    return {
        "status": "ok",
        "application": settings.app_name,
        "version": settings.app_version,
        "mode": "demo" if settings.demo_mode else "live",
    }
