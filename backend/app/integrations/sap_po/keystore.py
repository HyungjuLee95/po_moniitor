from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime

from requests import RequestException, Response

from app.core.config import PoServer, settings
from app.integrations.sap_po.client import build_session, endpoint
from app.integrations.sap_po.errors import SapPoConnectionError


HELP_ENVELOPE = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"'
    ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
    "<SOAP-ENV:Body>"
    '<vi:getKeystore xmlns:vi="urn:KeystoreHelpVi">'
    '<vi:keystoreHelpParameter xsi:nil="true"/>'
    "</vi:getKeystore>"
    "</SOAP-ENV:Body>"
    "</SOAP-ENV:Envelope>"
).encode("utf-8")

CERTIFICATES_ENVELOPE = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"'
    ' xmlns:api="http://sap.com/aii/tpm/internal/api/">'
    "<soapenv:Header/>"
    "<soapenv:Body>"
    "<api:GetKeystoreCertificates></api:GetKeystoreCertificates>"
    "</soapenv:Body>"
    "</soapenv:Envelope>"
).encode("utf-8")


@dataclass
class KeystoreEntry:
    view: str
    alias: str
    subject_dn: str = ""
    issuer_dn: str = ""
    is_key: bool = False
    not_before: datetime | None = None
    not_after: datetime | None = None
    not_before_raw: str = ""
    not_after_raw: str = ""
    serial_number: str = ""
    signature_algorithm: str = ""
    sources: set[str] = field(default_factory=set)


@dataclass
class KeystoreFetchResult:
    entries: list[KeystoreEntry]
    expiry_available: bool
    notice: str
    services: dict[str, str]


class _KeystoreServiceError(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_sap_date(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip()
    try:
        return datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        pass
    if len(normalized) >= 10:
        try:
            return datetime.strptime(normalized[:10], "%Y-%m-%d")
        except ValueError:
            return None
    return None


def _parse_xml(body: bytes) -> ET.Element:
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise _KeystoreServiceError("invalid_xml") from exc
    if any(_local_name(element.tag) == "Fault" for element in root.iter()):
        raise _KeystoreServiceError("soap_fault")
    return root


def _read_limited(response: Response) -> bytes:
    raw_length = response.headers.get("Content-Length", "")
    try:
        content_length = int(raw_length)
    except (TypeError, ValueError):
        content_length = 0
    if content_length > settings.sap_keystore_max_response_bytes:
        raise _KeystoreServiceError("response_too_large")
    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        total += len(chunk)
        if total > settings.sap_keystore_max_response_bytes:
            raise _KeystoreServiceError("response_too_large")
        chunks.append(chunk)
    return b"".join(chunks)


class KeystoreClient:
    def __init__(self, server: PoServer):
        self.server = server

    def _post(self, path: str, envelope: bytes) -> bytes:
        try:
            with build_session(self.server) as session:
                with session.post(
                    endpoint(self.server, path),
                    data=envelope,
                    headers={
                        "Content-Type": "text/xml; charset=utf-8",
                        "SOAPAction": '""',
                    },
                    timeout=(
                        settings.sap_connect_timeout_seconds,
                        settings.sap_read_timeout_seconds,
                    ),
                    allow_redirects=False,
                    stream=True,
                ) as response:
                    if 300 <= response.status_code < 400:
                        raise _KeystoreServiceError("redirect")
                    if response.status_code == 401:
                        raise _KeystoreServiceError("unauthorized")
                    if response.status_code == 403:
                        raise _KeystoreServiceError("forbidden")
                    if response.status_code == 404:
                        raise _KeystoreServiceError("not_found")
                    if response.status_code >= 400:
                        raise _KeystoreServiceError("http_error")
                    return _read_limited(response)
        except _KeystoreServiceError:
            raise
        except RequestException as exc:
            raise _KeystoreServiceError("connection") from exc

    def fetch_help_entries(self) -> list[KeystoreEntry]:
        path = self.server.endpoint_path(
            "keystore_help",
            settings.sap_keystore_help_path,
        )
        root = _parse_xml(self._post(path, HELP_ENVELOPE))
        entries: list[KeystoreEntry] = []
        for element in root.iter():
            if _local_name(element.tag) != "KeystoreHelp":
                continue
            values = {
                _local_name(child.tag): (child.text or "").strip()
                for child in element
            }
            entries.append(
                KeystoreEntry(
                    view=values.get("keystoreView", ""),
                    alias=values.get("keystoreAlias", ""),
                    subject_dn=values.get("keystoreSubjectDN", ""),
                    issuer_dn=values.get("keystoreIssuerDN", ""),
                    is_key=values.get("isKey", "").lower() == "true",
                    sources={"help"},
                )
            )
        return entries

    def fetch_certificate_entries(self) -> list[KeystoreEntry]:
        path = self.server.endpoint_path(
            "keystore_certificates",
            settings.sap_keystore_certificates_path,
        )
        root = _parse_xml(self._post(path, CERTIFICATES_ENVELOPE))
        entries: list[KeystoreEntry] = []
        for element in root.iter():
            if _local_name(element.tag) != "KeystoreCertsList":
                continue
            values = {
                _local_name(child.tag): (child.text or "").strip()
                for child in element
            }
            entries.append(
                KeystoreEntry(
                    view=values.get("viewName", ""),
                    alias=values.get("aliasName", ""),
                    not_before=parse_sap_date(values.get("startDate")),
                    not_after=parse_sap_date(values.get("endDate")),
                    not_before_raw=values.get("startDate", ""),
                    not_after_raw=values.get("endDate", ""),
                    serial_number=values.get("serialNumber", ""),
                    signature_algorithm=values.get("sigAlgoName", ""),
                    sources={"certificates"},
                )
            )
        return entries

    def fetch_all(self) -> KeystoreFetchResult:
        help_entries: list[KeystoreEntry] = []
        certificate_entries: list[KeystoreEntry] = []
        errors: dict[str, _KeystoreServiceError] = {}

        try:
            help_entries = self.fetch_help_entries()
        except _KeystoreServiceError as exc:
            errors["keystore_help"] = exc
        try:
            certificate_entries = self.fetch_certificate_entries()
        except _KeystoreServiceError as exc:
            errors["keystore_certificates"] = exc

        if len(errors) == 2:
            raise SapPoConnectionError("SAP PO keystore services are unavailable")

        merged: dict[tuple[str, str], KeystoreEntry] = {
            (entry.view, entry.alias): entry for entry in help_entries
        }
        for certificate in certificate_entries:
            entry = merged.get((certificate.view, certificate.alias))
            if entry is None:
                merged[(certificate.view, certificate.alias)] = certificate
                continue
            entry.not_before = certificate.not_before
            entry.not_after = certificate.not_after
            entry.not_before_raw = certificate.not_before_raw
            entry.not_after_raw = certificate.not_after_raw
            entry.serial_number = certificate.serial_number
            entry.signature_algorithm = certificate.signature_algorithm
            entry.sources.update(certificate.sources)

        notice = ""
        if "keystore_certificates" in errors:
            reason = errors["keystore_certificates"].reason
            if reason == "not_found":
                notice = "만료일 서비스가 배포되지 않아 기본 키스토어 정보만 표시합니다."
            elif reason in {"unauthorized", "forbidden"}:
                notice = "만료일 서비스 조회 권한이 없어 기본 키스토어 정보만 표시합니다."
            else:
                notice = "만료일 서비스 조회에 실패해 기본 키스토어 정보만 표시합니다."
        elif "keystore_help" in errors:
            notice = "DN 정보 조회에 실패해 인증서 만료 정보만 표시합니다."

        services = {
            "keystore_help": (
                errors["keystore_help"].reason
                if "keystore_help" in errors
                else "ok"
            ),
            "keystore_certificates": (
                errors["keystore_certificates"].reason
                if "keystore_certificates" in errors
                else "ok"
            ),
        }
        return KeystoreFetchResult(
            entries=sorted(
                merged.values(),
                key=lambda entry: (entry.view.lower(), entry.alias.lower()),
            ),
            expiry_available="keystore_certificates" not in errors,
            notice=notice,
            services=services,
        )
