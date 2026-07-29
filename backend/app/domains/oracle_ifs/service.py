from __future__ import annotations

from datetime import date, datetime, timezone
from threading import Event, Lock
from typing import Any

from sqlalchemy import text

from app.core.config import settings
from app.database import session_scope


_sync_lock = Lock()
_demo_rows: list[dict[str, Any]] = []


class OracleIfsService:
    def list_rows(self, username: str, is_admin: bool) -> list[dict]:
        if settings.demo_mode:
            return list(_demo_rows)
        where = "" if is_admin else "where lower(eai_dev_user_id) = lower(:username)"
        with session_scope() as session:
            rows = session.execute(
                text(
                    f"""
                    select req_seq, eai_dev_user_id, ifs_ids, source_system,
                           source_adapter, target_system, target_adapter,
                           progress_status, process_date, target_date, synced_at
                    from operations.oracle_ifs_cache
                    {where}
                    order by process_date desc nulls last, req_seq
                    """
                ),
                {} if is_admin else {"username": username},
            ).mappings().all()
        return [dict(row) for row in rows]

    def sync(self) -> dict:
        if not settings.ifs_oracle_configured:
            raise RuntimeError("IFS Oracle is not configured")
        if not _sync_lock.acquire(blocking=False):
            return {"status": "SKIPPED", "row_count": 0, "detail": "sync already running"}
        started = datetime.now(timezone.utc)
        try:
            usernames = self._usernames()
            if not usernames:
                return {"status": "SUCCESS", "row_count": 0}
            import oracledb

            connection = oracledb.connect(
                user=settings.ifs_oracle_user,
                password=settings.ifs_oracle_password.get_secret_value(),
                dsn=oracledb.makedsn(
                    settings.ifs_oracle_host,
                    settings.ifs_oracle_port,
                    service_name=settings.ifs_oracle_service,
                ),
            )
            try:
                binds = {f"user_{index}": value for index, value in enumerate(usernames)}
                placeholders = ", ".join(f":{name}" for name in binds)
                cursor = connection.cursor()
                cursor.execute(
                    f"""
                    select trim(eai_dev_user_id), ifs_req_seq, ifs_id, src_sys_id,
                           src_adapter_method1_cd, tgt_sys_id, tgt_adapter_method1_cd,
                           progrs_status_cd, process_tm
                    from ifs_def_info_tmp
                    where upper(trim(eai_dev_user_id)) in ({placeholders})
                    """,
                    {key: value.upper() for key, value in binds.items()},
                )
                rows = cursor.fetchall()
            finally:
                connection.close()
            grouped = self._group(rows)
            self._store(grouped, started)
            self._log("SUCCESS", len(grouped), None, started)
            return {"status": "SUCCESS", "row_count": len(grouped)}
        except Exception:
            self._log("FAILED", 0, "Oracle IFS synchronization failed", started)
            raise
        finally:
            _sync_lock.release()

    def update_target_date(self, req_seq: str, target_date: date | None) -> dict:
        if settings.demo_mode:
            for row in _demo_rows:
                if row["req_seq"] == req_seq:
                    row["target_date"] = target_date.isoformat() if target_date else None
                    return row
            raise LookupError("IFS request not found")
        with session_scope() as session:
            row = session.execute(
                text(
                    """
                    update operations.oracle_ifs_cache
                    set target_date = :target_date
                    where req_seq = :req_seq
                    returning req_seq, target_date
                    """
                ),
                {"req_seq": req_seq, "target_date": target_date},
            ).mappings().first()
        if row is None:
            raise LookupError("IFS request not found")
        return dict(row)

    def run_scheduler(self, stop_event: Event) -> None:
        while not stop_event.is_set():
            try:
                self.sync()
            except Exception:
                pass
            stop_event.wait(max(settings.ifs_sync_interval_seconds, 60))

    @staticmethod
    def _usernames() -> list[str]:
        if settings.demo_mode:
            return [settings.demo_admin_username]
        with session_scope() as session:
            return list(
                session.execute(
                    text("select username from iam.app_user where active = true order by username")
                ).scalars()
            )

    @staticmethod
    def _group(rows: list[tuple]) -> list[dict]:
        grouped: dict[str, dict] = {}
        for row in rows:
            req_seq = str(row[1])
            current = grouped.setdefault(
                req_seq,
                {
                    "req_seq": req_seq,
                    "eai_dev_user_id": row[0],
                    "ifs_ids": [],
                    "source_system": row[3],
                    "source_adapter": row[4],
                    "target_system": row[5],
                    "target_adapter": row[6],
                    "progress_status": row[7],
                    "process_date": row[8],
                },
            )
            if row[2] and str(row[2]) not in current["ifs_ids"]:
                current["ifs_ids"].append(str(row[2]))
            if row[8] and (not current["process_date"] or row[8] > current["process_date"]):
                current["process_date"] = row[8]
        return list(grouped.values())

    @staticmethod
    def _store(rows: list[dict], synced_at: datetime) -> None:
        if settings.demo_mode:
            _demo_rows[:] = rows
            return
        with session_scope() as session:
            for row in rows:
                session.execute(
                    text(
                        """
                        insert into operations.oracle_ifs_cache (
                            req_seq, eai_dev_user_id, ifs_ids, source_system,
                            source_adapter, target_system, target_adapter,
                            progress_status, process_date, synced_at
                        ) values (
                            :req_seq, :eai_dev_user_id, :ifs_ids, :source_system,
                            :source_adapter, :target_system, :target_adapter,
                            :progress_status, :process_date, :synced_at
                        )
                        on conflict (req_seq) do update set
                            eai_dev_user_id = excluded.eai_dev_user_id,
                            ifs_ids = excluded.ifs_ids,
                            source_system = excluded.source_system,
                            source_adapter = excluded.source_adapter,
                            target_system = excluded.target_system,
                            target_adapter = excluded.target_adapter,
                            progress_status = excluded.progress_status,
                            process_date = excluded.process_date,
                            synced_at = excluded.synced_at
                        """
                    ),
                    {**row, "synced_at": synced_at},
                )

    @staticmethod
    def _log(status: str, row_count: int, detail: str | None, started: datetime) -> None:
        if settings.demo_mode:
            return
        with session_scope() as session:
            session.execute(
                text(
                    """
                    insert into operations.oracle_ifs_sync_log (
                        status, row_count, detail, started_at, completed_at
                    ) values (:status, :row_count, :detail, :started_at, now())
                    """
                ),
                {
                    "status": status,
                    "row_count": row_count,
                    "detail": detail,
                    "started_at": started,
                },
            )
