# PO_MONITOR_MAIN Agent Rules

Before editing, read the root documents and all four documents in the target area and domain. Keep frontend and backend separated. Treat domain documents as part of the implementation.

Never expose `.env`, SAP credentials, database credentials, internal URLs, tokens, or message payloads. Keep authorization server-side. Use lowercase snake_case for PostgreSQL identifiers and add a new numbered migration instead of rewriting applied migrations.

Every new domain requires `README.md`, `MANUAL.md`, `SKILL.md`, and `ERROR.md`. Every resolved defect requires an ERROR entry with symptom, cause, resolution, verification, and prevention.
