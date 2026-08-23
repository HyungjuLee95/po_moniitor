from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

from app.integrations.rtims.contract import REQUIRED_COLUMNS, REQUIRED_OBJECTS


class SchemaSetupError(RuntimeError):
    """Safe schema setup error that does not expose credentials."""


ORACLE_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_$#]{0,127}$")


def normalize_oracle_identifier(value: str, label: str) -> str:
    normalized = value.strip().upper()
    if not ORACLE_IDENTIFIER.fullmatch(normalized):
        raise SchemaSetupError(f"{label} is not a valid unquoted Oracle identifier")
    return normalized


@dataclass(frozen=True)
class SchemaCheck:
    database: str
    object_name: str
    ready: bool
    missing_columns: tuple[str, ...] = ()


def normalize_postgresql_dsn(database_url: str) -> str:
    value = database_url.strip()
    if value.startswith("postgresql+psycopg://"):
        return "postgresql://" + value.removeprefix("postgresql+psycopg://")
    if value.startswith(("postgresql://", "postgres://")):
        return value
    raise SchemaSetupError("DATABASE_URL must use a PostgreSQL scheme")


def split_postgresql_statements(sql_text: str) -> list[str]:
    # The compatibility migration deliberately contains no functions or
    # semicolons in literals, so a strict statement terminator is sufficient.
    return [statement.strip() for statement in sql_text.split(";") if statement.strip()]


def split_oracle_statements(sql_text: str) -> list[str]:
    parts = re.split(r"(?m)^\s*-- statement\s*$", sql_text)
    return [part.strip().removesuffix(";").strip() for part in parts[1:] if part.strip()]


def _missing_columns(found: Iterable[str], required: frozenset[str]) -> tuple[str, ...]:
    normalized = {column.upper() for column in found}
    return tuple(sorted(required - normalized))


def check_postgresql(connection) -> list[SchemaCheck]:
    results: list[SchemaCheck] = []
    with connection.cursor() as cursor:
        for object_name in REQUIRED_OBJECTS:
            table_name = object_name.lower()
            cursor.execute(
                """
                select column_name
                from information_schema.columns
                where table_schema = %s and table_name = %s
                """,
                ("rtims", table_name),
            )
            columns = [row[0] for row in cursor.fetchall()]
            missing = _missing_columns(columns, REQUIRED_COLUMNS[object_name])
            results.append(
                SchemaCheck(
                    database="postgresql",
                    object_name=f"rtims.{table_name}",
                    ready=bool(columns) and not missing,
                    missing_columns=missing,
                )
            )
    return results


def check_oracle(connection) -> list[SchemaCheck]:
    results: list[SchemaCheck] = []
    with connection.cursor() as cursor:
        for object_name in REQUIRED_OBJECTS:
            cursor.execute(
                """
                select column_name
                from user_tab_columns
                where table_name = :table_name
                """,
                {"table_name": object_name},
            )
            columns = [row[0] for row in cursor.fetchall()]
            missing = _missing_columns(columns, REQUIRED_COLUMNS[object_name])
            results.append(
                SchemaCheck(
                    database="oracle",
                    object_name=object_name,
                    ready=bool(columns) and not missing,
                    missing_columns=missing,
                )
            )
    return results


def _ensure_ready(results: list[SchemaCheck]) -> list[SchemaCheck]:
    failures = [result for result in results if not result.ready]
    if failures:
        details = ", ".join(
            (
                f"{result.object_name} (missing: {', '.join(result.missing_columns)})"
                if result.missing_columns
                else result.object_name
            )
            for result in failures
        )
        raise SchemaSetupError(f"RTIMS schema contract is incomplete: {details}")
    return results


def setup_postgresql(database_url: str, ddl_path: Path, apply: bool) -> list[SchemaCheck]:
    try:
        import psycopg
    except ImportError as exc:
        raise SchemaSetupError("psycopg is not installed") from exc

    try:
        with psycopg.connect(normalize_postgresql_dsn(database_url)) as connection:
            if apply:
                statements = split_postgresql_statements(ddl_path.read_text(encoding="utf-8"))
                with connection.cursor() as cursor:
                    for statement in statements:
                        cursor.execute(statement)
                connection.commit()
            return _ensure_ready(check_postgresql(connection))
    except SchemaSetupError:
        raise
    except Exception as exc:
        raise SchemaSetupError("PostgreSQL RTIMS schema setup failed") from exc


def setup_oracle(
    host: str,
    port: int,
    service: str,
    user: str,
    password: str,
    schema: str,
    runtime_user: str,
    ddl_path: Path,
    apply: bool,
    grant_runtime_access: bool = True,
) -> list[SchemaCheck]:
    if not all((host.strip(), service.strip(), user.strip(), password)):
        raise SchemaSetupError("Oracle RTIMS DDL credentials are not fully configured")
    ddl_user = normalize_oracle_identifier(user, "RTIMS_ORACLE_DDL_USER")
    owner_schema = (
        normalize_oracle_identifier(schema, "RTIMS_ORACLE_SCHEMA")
        if schema.strip()
        else ddl_user
    )
    runtime_identifier = (
        normalize_oracle_identifier(runtime_user, "RTIMS_ORACLE_USER")
        if runtime_user.strip()
        else ""
    )
    if apply and owner_schema != ddl_user:
        raise SchemaSetupError(
            "RTIMS_ORACLE_SCHEMA must match RTIMS_ORACLE_DDL_USER during schema creation"
        )
    if apply and runtime_identifier and runtime_identifier != ddl_user and not schema.strip():
        raise SchemaSetupError(
            "RTIMS_ORACLE_SCHEMA is required when DDL and runtime users differ"
        )

    try:
        import oracledb
    except ImportError as exc:
        raise SchemaSetupError("oracledb is not installed") from exc

    try:
        dsn = oracledb.makedsn(host, port, service_name=service)
        with oracledb.connect(user=user, password=password, dsn=dsn) as connection:
            if apply:
                statements = split_oracle_statements(ddl_path.read_text(encoding="utf-8"))
                with connection.cursor() as cursor:
                    for statement in statements:
                        try:
                            cursor.execute(statement)
                        except oracledb.DatabaseError as exc:
                            error = exc.args[0] if exc.args else None
                            code = getattr(error, "code", None)
                            duplicate_index = (
                                code == 1408
                                and statement.lstrip().lower().startswith("create index")
                            )
                            if code != 955 and not duplicate_index:
                                raise
                    if (
                        grant_runtime_access
                        and runtime_identifier
                        and runtime_identifier != ddl_user
                    ):
                        for object_name in REQUIRED_OBJECTS:
                            cursor.execute(
                                f"grant select on {object_name} to {runtime_identifier}"
                            )
                        cursor.execute(
                            "grant update (ERR_STATE, ERR_PROC_MSG, USER_ID) "
                            f"on MON_ERR_HIST to {runtime_identifier}"
                        )
            return _ensure_ready(check_oracle(connection))
    except SchemaSetupError:
        raise
    except Exception as exc:
        raise SchemaSetupError("Oracle RTIMS schema setup failed") from exc
