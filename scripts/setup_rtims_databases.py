from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import TYPE_CHECKING


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
REQUIRED_PYTHON = (3, 11, 7)
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

if TYPE_CHECKING:
    from app.integrations.rtims.schema_setup import SchemaCheck


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or validate the PO_MONITOR_MAIN RTIMS compatibility schema."
    )
    parser.add_argument(
        "--target",
        choices=("postgresql", "oracle", "all"),
        default="all",
        help="Database target. Default: all",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Create missing objects. Without this flag the command only validates.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=ROOT / ".env",
        help="Environment file path. Default: project-root/.env",
    )
    parser.add_argument(
        "--skip-runtime-grants",
        action="store_true",
        help="Do not grant Oracle object privileges to RTIMS_ORACLE_USER.",
    )
    return parser.parse_args()


def print_results(results: list["SchemaCheck"]) -> None:
    for result in results:
        print(f"READY {result.database}: {result.object_name}")


def main() -> int:
    args = parse_args()
    if sys.version_info[:3] != REQUIRED_PYTHON:
        print("ERROR: Python 3.11.7 is required", file=sys.stderr)
        return 2
    if not args.env_file.is_file():
        print("ERROR: .env file was not found", file=sys.stderr)
        return 2

    try:
        from app.core.config import Settings
        from app.integrations.rtims.schema_setup import (
            SchemaSetupError,
            setup_oracle,
            setup_postgresql,
        )
    except ImportError:
        print(
            "ERROR: backend dependencies are not installed; run "
            "'python -m pip install -r backend\\requirements.txt'",
            file=sys.stderr,
        )
        return 2

    try:
        settings = Settings(_env_file=args.env_file)
    except Exception:
        print("ERROR: .env configuration is invalid", file=sys.stderr)
        return 2
    action = "apply and validate" if args.apply else "validate only"
    print(f"RTIMS schema setup mode: {action}; target: {args.target}")

    try:
        if args.target in {"postgresql", "all"}:
            print_results(
                setup_postgresql(
                    settings.rtims_postgres_setup_url,
                    ROOT / "backend" / "migrations" / "006_rtims_compatibility.sql",
                    apply=args.apply,
                )
            )

        if args.target in {"oracle", "all"}:
            print_results(
                setup_oracle(
                    host=settings.rtims_oracle_host,
                    port=settings.rtims_oracle_port,
                    service=settings.rtims_oracle_service,
                    user=settings.rtims_oracle_ddl_user,
                    password=settings.rtims_oracle_ddl_password.get_secret_value(),
                    schema=settings.rtims_oracle_schema,
                    runtime_user=settings.rtims_oracle_user,
                    ddl_path=ROOT / "backend" / "oracle" / "001_rtims_monitoring_schema.sql",
                    apply=args.apply,
                    grant_runtime_access=not args.skip_runtime_grants,
                )
            )
    except SchemaSetupError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("RTIMS schema contract is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
