from __future__ import annotations

from datetime import date, datetime, timedelta

from app.core.config import PoServer, settings
from app.integrations.sap_po.keystore import KeystoreClient, KeystoreEntry


def _local_date(value: datetime | None) -> date | None:
    if value is None:
        return None
    if value.tzinfo is not None:
        value = value.astimezone()
    return value.date()


class CertificateService:
    @staticmethod
    def _demo_entries(server: PoServer) -> list[KeystoreEntry]:
        today = date.today()
        return [
            KeystoreEntry(
                view="TrustedCAs",
                alias=f"{server.sid}_ROOT_CA",
                subject_dn="CN=Demo Root CA",
                issuer_dn="CN=Demo Root CA",
                not_before=datetime.combine(today - timedelta(days=700), datetime.min.time()),
                not_after=datetime.combine(today + timedelta(days=420), datetime.min.time()),
                serial_number="DEMO-ROOT",
                signature_algorithm="SHA256withRSA",
                sources={"help", "certificates"},
            ),
            KeystoreEntry(
                view="TrustedCAs",
                alias=f"{server.sid}_EXPIRING",
                subject_dn="CN=Demo Expiring Certificate",
                issuer_dn="CN=Demo Root CA",
                not_before=datetime.combine(today - timedelta(days=300), datetime.min.time()),
                not_after=datetime.combine(today + timedelta(days=14), datetime.min.time()),
                serial_number="DEMO-WARNING",
                signature_algorithm="SHA256withRSA",
                sources={"help", "certificates"},
            ),
        ]

    @staticmethod
    def _row(server: PoServer, entry: KeystoreEntry, warning_days: int) -> dict:
        expiry_date = _local_date(entry.not_after)
        days_remaining = (expiry_date - date.today()).days if expiry_date else None
        if days_remaining is None:
            status = "UNKNOWN"
        elif days_remaining < 0:
            status = "EXPIRED"
        elif days_remaining <= warning_days:
            status = "EXPIRING"
        else:
            status = "VALID"
        return {
            "sid": server.sid,
            "view": entry.view,
            "alias": entry.alias,
            "kind": "PRIVATE_KEY" if entry.is_key else "TRUSTED_CERTIFICATE",
            "subject_dn": entry.subject_dn,
            "issuer_dn": entry.issuer_dn,
            "not_before": entry.not_before.isoformat() if entry.not_before else None,
            "not_after": entry.not_after.isoformat() if entry.not_after else None,
            "not_before_raw": entry.not_before_raw,
            "not_after_raw": entry.not_after_raw,
            "serial_number": entry.serial_number,
            "signature_algorithm": entry.signature_algorithm,
            "days_remaining": days_remaining,
            "status": status,
            "sources": sorted(entry.sources),
        }

    def list(self, server: PoServer, warning_days: int) -> tuple[list[dict], dict]:
        if settings.sap_po_live_mode:
            fetched = KeystoreClient(server).fetch_all()
            entries = fetched.entries
            expiry_available = fetched.expiry_available
            notice = fetched.notice
            services = fetched.services
            source = "sap-po-keystore"
        else:
            entries = self._demo_entries(server)
            expiry_available = True
            notice = ""
            services = {
                "keystore_help": "demo",
                "keystore_certificates": "demo",
            }
            source = "demo"

        rows = [self._row(server, entry, warning_days) for entry in entries]
        summary = {
            status.lower(): sum(1 for row in rows if row["status"] == status)
            for status in ("EXPIRED", "EXPIRING", "VALID", "UNKNOWN")
        }
        return rows, {
            "sid": server.sid,
            "count": len(rows),
            "views": sorted({row["view"] for row in rows if row["view"]}),
            "warning_days": warning_days,
            "expiry_available": expiry_available,
            "summary": summary,
            "notice": notice,
            "services": services,
            "source": source,
        }
