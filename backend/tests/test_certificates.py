from datetime import date, datetime, timedelta

from app.core.config import PoServer
from app.core.security import permissions_for
from app.domains.certificates.service import CertificateService
from app.integrations.sap_po.keystore import (
    KeystoreClient,
    KeystoreEntry,
    _KeystoreServiceError,
    parse_sap_date,
)


def server() -> PoServer:
    return PoServer(
        sid="POQ",
        display_name="Quality",
        environment="quality",
        base_url="https://po.example.internal",
        capabilities=["monitor"],
    )


HELP_RESPONSE = b"""<?xml version="1.0"?>
<Envelope><Body><KeystoreHelp>
<keystoreView>TrustedCAs</keystoreView>
<keystoreAlias>root-ca</keystoreAlias>
<keystoreIssuerDN>CN=Root</keystoreIssuerDN>
<keystoreSubjectDN>CN=Root</keystoreSubjectDN>
<isKey>false</isKey>
</KeystoreHelp></Body></Envelope>
"""

CERTIFICATE_RESPONSE = b"""<?xml version="1.0"?>
<Envelope><Body><KeystoreCertsList>
<viewName>TrustedCAs</viewName>
<aliasName>root-ca</aliasName>
<startDate>2025-01-02T00:00:00Z</startDate>
<endDate>2027-03-04T00:00:00Z</endDate>
<serialNumber>ABC123</serialNumber>
<sigAlgoName>SHA256withRSA</sigAlgoName>
</KeystoreCertsList></Body></Envelope>
"""


def test_sap_date_accepts_iso_and_date_prefix() -> None:
    assert parse_sap_date("2027-03-04T01:02:03Z") is not None
    assert parse_sap_date("2027-03-04 custom") == datetime(2027, 3, 4)
    assert parse_sap_date("invalid") is None


def test_keystore_client_joins_help_and_certificate_sources(monkeypatch) -> None:
    client = KeystoreClient(server())

    def post(path: str, _: bytes) -> bytes:
        return (
            HELP_RESPONSE
            if "KeystoreHelp" in path
            else CERTIFICATE_RESPONSE
        )

    monkeypatch.setattr(client, "_post", post)

    result = client.fetch_all()

    assert result.expiry_available is True
    assert result.services == {
        "keystore_help": "ok",
        "keystore_certificates": "ok",
    }
    assert len(result.entries) == 1
    entry = result.entries[0]
    assert entry.subject_dn == "CN=Root"
    assert entry.serial_number == "ABC123"
    assert entry.sources == {"help", "certificates"}


def test_keystore_client_degrades_when_expiry_service_is_missing(monkeypatch) -> None:
    client = KeystoreClient(server())

    def post(path: str, _: bytes) -> bytes:
        if "KeystoreHelp" in path:
            return HELP_RESPONSE
        raise _KeystoreServiceError("not_found")

    monkeypatch.setattr(client, "_post", post)

    result = client.fetch_all()

    assert len(result.entries) == 1
    assert result.expiry_available is False
    assert result.services["keystore_certificates"] == "not_found"
    assert result.notice


def test_keystore_client_rejects_http_200_soap_fault(monkeypatch) -> None:
    client = KeystoreClient(server())
    fault = b"""<Envelope><Body><Fault><faultstring>internal</faultstring></Fault></Body></Envelope>"""
    monkeypatch.setattr(client, "_post", lambda path, body: fault)

    try:
        client.fetch_all()
    except Exception as exc:
        assert type(exc).__name__ == "SapPoConnectionError"
    else:
        raise AssertionError("SOAP Fault must not be treated as an empty success")


def test_certificate_status_uses_warning_days() -> None:
    today = date.today()
    expiring = CertificateService._row(
        server(),
        KeystoreEntry(
            view="TrustedCAs",
            alias="soon",
            not_after=datetime.combine(
                today + timedelta(days=10),
                datetime.min.time(),
            ),
        ),
        warning_days=30,
    )
    assert expiring["status"] == "EXPIRING"
    assert expiring["days_remaining"] == 10


def test_certificate_permission_is_operator_only() -> None:
    assert "certificates:read" in permissions_for("OPERATOR")
    assert "certificates:read" not in permissions_for("VIEWER")
