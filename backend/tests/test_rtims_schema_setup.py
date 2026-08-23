from __future__ import annotations

from pathlib import Path

import pytest

from app.integrations.rtims.contract import REQUIRED_COLUMNS, REQUIRED_OBJECTS
from app.integrations.rtims.schema_setup import (
    SchemaSetupError,
    normalize_oracle_identifier,
    normalize_postgresql_dsn,
    split_oracle_statements,
    split_postgresql_statements,
)


ROOT = Path(__file__).resolve().parents[2]


def test_postgresql_dsn_normalizes_sqlalchemy_driver_scheme() -> None:
    assert normalize_postgresql_dsn(
        "postgresql+psycopg://user:secret@db:5432/po_monitor"
    ) == "postgresql://user:secret@db:5432/po_monitor"


def test_postgresql_dsn_rejects_non_postgresql_database() -> None:
    with pytest.raises(SchemaSetupError):
        normalize_postgresql_dsn("oracle://db/RTIMS")


def test_oracle_identifier_rejects_sql_identifier_injection() -> None:
    assert normalize_oracle_identifier("hynixrtims", "schema") == "HYNIXRTIMS"
    with pytest.raises(SchemaSetupError):
        normalize_oracle_identifier("HYNIXRTIMS; DROP USER X", "schema")


def test_ddl_files_cover_the_live_rtims_contract() -> None:
    postgresql = (
        ROOT / "backend" / "migrations" / "006_rtims_compatibility.sql"
    ).read_text(encoding="utf-8").lower()
    oracle = (
        ROOT / "backend" / "oracle" / "001_rtims_monitoring_schema.sql"
    ).read_text(encoding="utf-8").upper()

    for object_name in REQUIRED_OBJECTS:
        assert f"rtims.{object_name.lower()}" in postgresql
        assert object_name in oracle
        for column_name in REQUIRED_COLUMNS[object_name]:
            assert column_name.lower() in postgresql
            assert column_name in oracle

    statements = split_postgresql_statements(postgresql) + split_oracle_statements(oracle)
    for statement in statements:
        executable = "\n".join(
            line for line in statement.splitlines() if not line.strip().startswith("--")
        ).lstrip().lower()
        assert not executable.startswith(("drop ", "truncate ", "delete "))


def test_ddl_splitters_return_executable_units() -> None:
    postgresql = (
        ROOT / "backend" / "migrations" / "006_rtims_compatibility.sql"
    ).read_text(encoding="utf-8")
    oracle = (
        ROOT / "backend" / "oracle" / "001_rtims_monitoring_schema.sql"
    ).read_text(encoding="utf-8")

    assert len(split_postgresql_statements(postgresql)) >= len(REQUIRED_OBJECTS)
    oracle_statements = split_oracle_statements(oracle)
    assert len(oracle_statements) >= len(REQUIRED_OBJECTS)
    assert all(not statement.endswith(";") for statement in oracle_statements)
