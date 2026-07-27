from contextlib import asynccontextmanager

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
from app.domains.incidents.router import router as incidents_router
from app.domains.interfaces.router import router as interfaces_router
from app.domains.messages.router import router as messages_router
from app.domains.monitoring.router import router as monitoring_router
from app.integrations.sap_po.errors import SapPoError
from app.integrations.rtims.repository import RtimsError
from app.domains.dashboard.router import router as dashboard_router
from app.domains.llm_search.router import router as llm_search_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.database_connect_on_startup and not settings.demo_mode:
        check_database()
    yield


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
