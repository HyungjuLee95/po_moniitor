from __future__ import annotations

import base64
import re

from app.core.config import PoServer, settings
from app.integrations.sap_po.client import build_session, endpoint
from app.integrations.sap_po.errors import SapPoConnectionError


PASSWORD_PATTERN = re.compile(
    r"<(?:\w+:)?dbpassword[^>]*>(.*?)</(?:\w+:)?dbpassword>",
    re.IGNORECASE | re.DOTALL,
)


def read_channel_xml(
    server: PoServer,
    component_id: str,
    channel_id: str,
) -> str:
    session = build_session(server)
    try:
        response = session.get(
            endpoint(server, settings.sap_directory_path),
            params={
                "method": "PLAIN",
                "TYPE": "Channel",
                "KEY": f"|{component_id}|{channel_id}",
                "VC": "DIR",
                "UC": "true",
                "release": "7.0",
            },
            timeout=(
                settings.sap_connect_timeout_seconds,
                settings.sap_read_timeout_seconds,
            ),
        )
        response.raise_for_status()
        return response.text
    except Exception as exc:
        raise SapPoConnectionError(
            f"Directory API request failed for SID {server.sid}"
        ) from exc


def extract_and_decrypt_password(raw_xml: str) -> str | None:
    match = PASSWORD_PATTERN.search(raw_xml)
    if match is None:
        return None
    try:
        decoded = base64.b64decode(match.group(1).strip(), validate=True)
        if not decoded:
            return ""
        # The legacy Java implementation skips the first marker byte, XORs
        # each remaining byte with 0x74, then restores reverse order.
        output = bytearray(len(decoded) - 1)
        for index in range(1, len(decoded)):
            output[len(decoded) - 1 - index] = decoded[index] ^ 0x74
        return output.decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise SapPoConnectionError(
            "Directory API password payload could not be decoded"
        ) from exc
