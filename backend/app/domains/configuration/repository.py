from __future__ import annotations

import json

from sqlalchemy import text

from app.core.config import PoServer
from app.database import session_scope


class ConfigurationRepository:
    def sync_servers(self, servers: list[PoServer]) -> None:
        with session_scope() as session:
            for server in servers:
                session.execute(
                    text(
                        """
                        insert into configuration.po_server (
                            sid, display_name, environment, base_url, port,
                            capabilities, enabled
                        ) values (
                            :sid, :display_name, :environment, :base_url, :port,
                            cast(:capabilities as jsonb), :enabled
                        )
                        on conflict (sid) do update set
                            display_name = excluded.display_name,
                            environment = excluded.environment,
                            base_url = excluded.base_url,
                            port = excluded.port,
                            capabilities = excluded.capabilities,
                            enabled = excluded.enabled,
                            updated_at = now()
                        """
                    ),
                    {
                        "sid": server.sid,
                        "display_name": server.display_name,
                        "environment": server.environment,
                        "base_url": str(server.base_url),
                        "port": server.port,
                        "capabilities": json.dumps(server.capabilities),
                        "enabled": server.enabled,
                    },
                )
