from __future__ import annotations

from functools import lru_cache
from typing import Literal

from requests import Session
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from urllib3.util.retry import Retry

from app.core.config import PoServer, settings
from app.integrations.sap_po.errors import (
    SapPoConfigurationError,
    SapPoConnectionError,
)


ServiceName = Literal[
    "channels",
    "channel_admin",
    "adapter_monitor",
    "aae_monitor",
    "systatus",
    "business_system",
    "interface_monitor",
]


def credentials(server: PoServer) -> tuple[str, str]:
    username = server.username or settings.sap_po_user
    password = (
        server.password.get_secret_value()
        if server.password is not None
        else settings.sap_po_password.get_secret_value()
    )
    if not username or not password:
        raise SapPoConfigurationError(
            f"SAP PO credentials are not configured for SID {server.sid}"
        )
    return username, password


def service_path(name: ServiceName) -> str:
    return {
        "channels": settings.sap_channel_wsdl_path,
        "channel_admin": settings.sap_channel_admin_wsdl_path,
        "adapter_monitor": settings.sap_adapter_monitor_wsdl_path,
        "aae_monitor": settings.sap_aae_monitor_wsdl_path,
        "systatus": settings.sap_systatus_wsdl_path,
        "business_system": settings.sap_business_system_wsdl_path,
        "interface_monitor": settings.sap_interface_monitor_wsdl_path,
    }[name]


def endpoint(server: PoServer, path: str) -> str:
    return f"{server.origin}/{path.lstrip('/')}"


def build_session(server: PoServer) -> Session:
    username, password = credentials(server)
    session = Session()
    session.auth = HTTPBasicAuth(username, password)
    session.verify = settings.sap_verify_tls
    retry = Retry(
        total=settings.sap_retry_count,
        connect=settings.sap_retry_count,
        read=settings.sap_retry_count,
        backoff_factor=0.35,
        status_forcelist=(429, 502, 503, 504),
        allowed_methods=frozenset({"GET", "HEAD", "OPTIONS"}),
    )
    session.mount("http://", HTTPAdapter(max_retries=retry))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


@lru_cache(maxsize=64)
def soap_client(sid: str, service_name: ServiceName):
    from zeep import Client
    from zeep import Settings as ZeepSettings
    from zeep.transports import Transport

    from app.domains.configuration.registry import ServerRegistry

    server = ServerRegistry().get(sid)
    transport = Transport(
        session=build_session(server),
        timeout=settings.sap_connect_timeout_seconds,
        operation_timeout=settings.sap_read_timeout_seconds,
    )
    try:
        return Client(
            wsdl=endpoint(server, service_path(service_name)),
            transport=transport,
            settings=ZeepSettings(strict=False, xml_huge_tree=True),
        )
    except Exception as exc:
        raise SapPoConnectionError(
            f"failed to initialize {service_name} SOAP client for {server.sid}"
        ) from exc


def call(operation, *args, **kwargs):
    try:
        return operation(*args, **kwargs)
    except Exception as exc:
        raise SapPoConnectionError("SAP PO SOAP operation failed") from exc
