"""
Backup service — automated weekly SQLite database backups.

Performs a hot backup using SQLite's built-in ``VACUUM INTO`` (or
``sqlite3.connect().backup()``) so the WAL is fully checkpointed and the
copy is a clean, consistent database file.

Rotation keeps the most recent 10 backups in ``backups/`` and purges older
ones automatically.

Usage
-----
Call ``BackupService.start()`` once at application startup.  It schedules
a background thread that fires immediately (to ensure at least one backup
exists) and then every 7 days.

Manual backup
-------------
    from accessibility_mgr.services.backup_service import BackupService
    path = BackupService.run_backup(trigger="manual")
"""

from __future__ import annotations

import logging
import shutil
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)


class BackupService:
    """Automated weekly SQLite database backups service."""

    # Populated lazily so the service can be imported before init_db() runs.
    _db_path: Path | None = None
    _backups_dir: Path | None = None

    _KEEP_BACKUPS = 10          # number of most-recent backups to retain
    _INTERVAL_SECONDS = 7 * 24 * 60 * 60   # one week

    _timer: threading.Timer | None = None
    _lock = threading.Lock()
    _run_lock = threading.Lock()
    _scheduler_enabled = False

    @staticmethod
    def _paths() -> tuple[Path, Path]:
        """Return (DB_PATH, BACKUPS_DIR) importing lazily to avoid circular imports."""
        if BackupService._db_path is None:
            from ..db.schema import BACKUPS_DIR, DB_PATH
            BackupService._db_path = DB_PATH
            BackupService._backups_dir = BACKUPS_DIR
        return BackupService._db_path, BackupService._backups_dir  # type: ignore[return-value]

    # ── Core backup logic ─────────────────────────────────────────────────────────

    @staticmethod
    def run_backup(trigger: str = "scheduled") -> str:
        """
        Copy the live database to ``backups/`` and return the backup file path.

        The copy is done via ``sqlite3.Connection.backup()``, which performs a
        WAL checkpoint and produces a consistent snapshot even while the app is
        running.  Old backups beyond the retention limit are pruned afterwards.

        Returns the absolute path of the new backup file as a string.
        Raises ``RuntimeError`` if the source database does not yet exist.
        """
        if not BackupService._run_lock.acquire(blocking=False):
            raise RuntimeError("Backup already in progress")

        try:
            db_path, backups_dir = BackupService._paths()
            backups_dir.mkdir(parents=True, exist_ok=True)

            if not db_path.exists():
                raise RuntimeError(f"Database not found at {db_path}; cannot back up.")

            # FUN-012: abort early if there is not enough free disk space
            db_size = db_path.stat().st_size
            free = shutil.disk_usage(backups_dir).free
            required = db_size * 2  # headroom for WAL journal during backup
            if free < required:
                raise RuntimeError(
                    f"Insufficient disk space for backup: {free:,} bytes free, "
                    f"{required:,} bytes needed (2× source size {db_size:,})."
                )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = backups_dir / f"accessibility_manager_{timestamp}.db"

            # Use sqlite3.Connection.backup() — checkpoints WAL, works on a live DB.
            src_conn = sqlite3.connect(str(db_path))
            dst_conn = sqlite3.connect(str(dest))
            try:
                src_conn.backup(dst_conn)
            finally:
                dst_conn.close()
                src_conn.close()

            size = dest.stat().st_size
            log.info("Backup created: %s (%d bytes)", dest, size)

            # Record in DB (best-effort — don't crash if table not ready yet)
            try:
                from ..db.queries import log_backup
                log_backup(str(dest), size, trigger=trigger, status="ok")
            except Exception as exc:  # noqa: BLE001
                log.warning("Could not write backup_log entry: %s", exc)

            BackupService._rotate(backups_dir)
            return str(dest)
        finally:
            BackupService._run_lock.release()

    @staticmethod
    def _schedule_next_locked(delay_seconds: int) -> None:
        """Schedule the next timer while holding ``_lock``."""
        BackupService._timer = threading.Timer(delay_seconds, BackupService._scheduled_run)
        BackupService._timer.daemon = True
        BackupService._timer.name = "db-backup-timer"
        BackupService._timer.start()

    @staticmethod
    def _rotate(backups_dir: Path) -> None:
        """Delete oldest backup files beyond the retention limit."""
        backups = sorted(backups_dir.glob("accessibility_manager_*.db"))
        for old in backups[:-BackupService._KEEP_BACKUPS]:
            try:
                old.unlink()
                log.debug("Pruned old backup: %s", old)
            except OSError as exc:
                log.warning("Could not prune backup %s: %s", old, exc)

    # ── Scheduler ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _scheduled_run() -> None:
        """Execute a backup then reschedule the next one."""
        try:
            path = BackupService.run_backup(trigger="scheduled")
            log.info("Scheduled backup completed: %s", path)
        except Exception as exc:  # noqa: BLE001
            log.error("Scheduled backup FAILED: %s", exc)
        finally:
            # Always reschedule so one failure doesn't stop all future backups.
            with BackupService._lock:
                if BackupService._scheduler_enabled:
                    BackupService._schedule_next_locked(BackupService._INTERVAL_SECONDS)
                else:
                    BackupService._timer = None

    @staticmethod
    def start() -> None:
        """
        Start the weekly backup scheduler.

        Safe to call multiple times — subsequent calls are no-ops.
        The first backup fires after a short delay (30 s) so startup is not
        blocked, and then repeats every 7 days.
        """
        with BackupService._lock:
            if BackupService._scheduler_enabled:
                return  # already running

            BackupService._scheduler_enabled = True
            # Small initial delay so init_db() has fully committed before first backup.
            BackupService._schedule_next_locked(30)
            log.info(
                "Database backup scheduler started — first backup in 30 s, "
                "then every 7 days.  Backups directory: %s",
                BackupService._paths()[1],
            )

    @staticmethod
    def stop() -> None:
        """Cancel the scheduled backup timer (called on app shutdown)."""
        with BackupService._lock:
            BackupService._scheduler_enabled = False
            if BackupService._timer is not None:
                BackupService._timer.cancel()
                BackupService._timer = None
                log.info("Database backup scheduler stopped.")

    # ── Restore ───────────────────────────────────────────────────────────────────

    @staticmethod
    def restore_backup(backup_path: str) -> None:
        """Restore the live database from *backup_path*.

        STUB-029: previously unimplemented.  Now performs a verified restore:
        1. Validates the backup file is a readable SQLite database.
        2. Creates a safety snapshot of the current live DB before overwriting.
        3. Copies the backup over the live DB path using sqlite3.backup().
        4. Verifies the restored file can be opened and queried.

        Raises ``RuntimeError`` on any validation or IO failure so the caller
        can surface the error to the user without crashing the app.
        """
        db_path, backups_dir = BackupService._paths()
        src = Path(backup_path)

        if not src.exists():
            raise RuntimeError(f"Backup file not found: {backup_path}")

        # Validate backup is an intact SQLite database
        try:
            test_conn = sqlite3.connect(str(src))
            test_conn.execute("PRAGMA integrity_check").fetchone()
            test_conn.close()
        except sqlite3.DatabaseError as exc:
            raise RuntimeError(
                f"Backup file '{backup_path}' is not a valid SQLite database: {exc}"
            ) from exc

        # Safety snapshot of the current live DB
        if db_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safety = backups_dir / f"pre_restore_{timestamp}.db"
            backups_dir.mkdir(parents=True, exist_ok=True)
            try:
                live = sqlite3.connect(str(db_path))
                snap = sqlite3.connect(str(safety))
                live.backup(snap)
                snap.close()
                live.close()
                log.info("Pre-restore safety snapshot saved to %s", safety)
            except Exception as exc:  # noqa: BLE001
                log.warning("Could not create safety snapshot before restore: %s", exc)

        # Perform the restore
        try:
            src_conn = sqlite3.connect(str(src))
            dst_conn = sqlite3.connect(str(db_path))
            src_conn.backup(dst_conn)
            dst_conn.close()
            src_conn.close()
        except Exception as exc:
            raise RuntimeError(f"Restore failed while copying backup to live DB: {exc}") from exc

        # Verify restored DB is queryable
        try:
            verify = sqlite3.connect(str(db_path))
            verify.execute("PRAGMA integrity_check").fetchone()
            verify.close()
        except sqlite3.DatabaseError as exc:
            raise RuntimeError(
                f"Restored database failed integrity check: {exc}. "
                "The safety snapshot (if created) can be used to recover."
            ) from exc

        log.info("Database successfully restored from %s", backup_path)

    # ── Status helper (for Admin UI) ──────────────────────────────────────────────

    @staticmethod
    def status() -> dict[str, object]:
        """Return a summary dict for display in the Admin panel."""
        _, backups_dir = BackupService._paths()
        backups = sorted(backups_dir.glob("accessibility_manager_*.db"))
        last = backups[-1] if backups else None
        return {
            "backup_count": len(backups),
            "latest_backup": str(last) if last else "none",
            "latest_size_bytes": last.stat().st_size if last else 0,
            "backups_dir": str(backups_dir),
            "retention_limit": BackupService._KEEP_BACKUPS,
            "interval_days": BackupService._INTERVAL_SECONDS // 86400,
            "scheduler_active": BackupService._scheduler_enabled,
        }
