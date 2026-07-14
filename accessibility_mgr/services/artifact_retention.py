"""Artifact retention lifecycle management — SQLite-backed."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


def _default_db_path() -> Path:
    try:
        from ..db.schema import DB_PATH
        return DB_PATH
    except Exception:
        return Path("accessibility_mgr.db")


class ArtifactRetentionService:
    """SQLite-backed retention lifecycle management for generated artifacts."""

    def __init__(self, database_path: Path | None = None) -> None:
        self.database_path = database_path or _default_db_path()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS artifact_retention_record (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artifact_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    retention_days INTEGER NOT NULL DEFAULT 30,
                    status TEXT NOT NULL DEFAULT 'active'
                )"""
            )

    def register_artifact(
        self,
        artifact_path: str,
        *,
        retention_days: int = 30,
    ) -> dict[str, Any]:
        created_at = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO artifact_retention_record (artifact_path, created_at, retention_days, status) "
                "VALUES (?, ?, ?, 'active')",
                (artifact_path, created_at, retention_days),
            )
        return {
            "artifact_path": artifact_path,
            "created_at": created_at,
            "retention_days": retention_days,
            "status": "active",
        }

    def evaluate_retention(self) -> list[dict[str, Any]]:
        now = datetime.now(UTC)
        with self._connect() as conn:
            for row in conn.execute(
                "SELECT * FROM artifact_retention_record WHERE status = 'active'"
            ).fetchall():
                created = datetime.fromisoformat(row["created_at"])
                expiry = created + timedelta(days=row["retention_days"])
                if now > expiry:
                    conn.execute(
                        "UPDATE artifact_retention_record SET status = 'expired' WHERE id = ?",
                        (row["id"],),
                    )
            return [
                {
                    "artifact_path": r["artifact_path"],
                    "created_at": r["created_at"],
                    "retention_days": r["retention_days"],
                    "status": r["status"],
                }
                for r in conn.execute(
                    "SELECT * FROM artifact_retention_record"
                ).fetchall()
            ]

    def cleanup_expired(self) -> list[str]:
        removed: list[str] = []
        with self._connect() as conn:
            for row in conn.execute(
                "SELECT * FROM artifact_retention_record WHERE status = 'expired'"
            ).fetchall():
                path = Path(row["artifact_path"])
                if path.exists():
                    path.unlink()
                removed.append(row["artifact_path"])
                conn.execute(
                    "UPDATE artifact_retention_record SET status = 'deleted' WHERE id = ?",
                    (row["id"],),
                )
        return removed


__all__ = ["ArtifactRetentionService"]
