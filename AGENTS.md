# PO_MONITOR_MAIN Agent Rules

Before editing, read the root documents and all five documents in the target area and domain. Keep frontend and backend separated. Treat domain documents as part of the implementation.

Never expose `.env`, SAP credentials, database credentials, internal URLs, tokens, or message payloads. Keep authorization server-side. Use lowercase snake_case for PostgreSQL identifiers and add a new numbered migration instead of rewriting applied migrations.

Every domain requires `README.md`, `MANUAL.md`, `SKILL.md`, `ERROR.md`, and `API.md`. `API.md` is the authoritative inventory of routes, permissions, request/response contracts, external data sources, and frontend consumers. Every resolved defect or verification failure requires an ERROR entry with symptom, cause, resolution, verification, and prevention. Cross-domain failures belong in the root `ERROR.md`; domain-specific failures belong in that domain's `ERROR.md`.
