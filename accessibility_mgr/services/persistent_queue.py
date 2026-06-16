"""Persistent distributed workflow queue backend."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path


def _default_db_path() -> Path:
    """FUN-006: resolve the canonical DB path from schema to avoid drift."""
    try:
        from ..db.schema import DB_PATH
        return DB_PATH
    except Exception:
        # Fallback for standalone / test use where schema is not importable
        return Path("accessibility_mgr.db")


DATABASE_PATH = _default_db_path()


@dataclass(slots=True)
class PersistentWorkflowJob:
    workflow_name: str
    asset_id: int
    priority: int
    status: str
    created_at: str


class PersistentWorkflowQueue:
    """SQLite-backed distributed workflow queue."""

    def __init__(self, database_path: Path | None = None) -> None:
        self.database_path = database_path or DATABASE_PATH
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_name TEXT NOT NULL,
                    asset_id INTEGER NOT NULL,
                    priority INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def enqueue(
        self,
        *,
        workflow_name: str,
        asset_id: int,
        priority: int = 5,
    ) -> PersistentWorkflowJob:
        created_at = datetime.now(timezone.utc).isoformat()

        job = PersistentWorkflowJob(
            workflow_name=workflow_name,
            asset_id=asset_id,
            priority=priority,
            status="queued",
            created_at=created_at,
        )

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO workflow_queue (
                    workflow_name,
                    asset_id,
                    priority,
                    status,
                    created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    job.workflow_name,
                    job.asset_id,
                    job.priority,
                    job.status,
                    job.created_at,
                ),
            )

        return job

    def list_jobs(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT workflow_name, asset_id, priority,
                       status, created_at
                FROM workflow_queue
                ORDER BY priority ASC, created_at ASC
                """
            ).fetchall()

        return [
            {
                "workflow_name": row[0],
                "asset_id": row[1],
                "priority": row[2],
                "status": row[3],
                "created_at": row[4],
            }
            for row in rows
        ]

    def dequeue(self) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, workflow_name, asset_id,
                       priority, status, created_at
                FROM workflow_queue
                WHERE status = 'queued'
                ORDER BY priority ASC, created_at ASC
                LIMIT 1
                """
            ).fetchone()

            if not row:
                return None

            connection.execute(
                "UPDATE workflow_queue SET status = 'running' WHERE id = ?",
                (row[0],),
            )

        return {
            "id": row[0],
            "workflow_name": row[1],
            "asset_id": row[2],
            "priority": row[3],
            "status": "running",
            "created_at": row[5],
        }


__all__ = [
    "PersistentWorkflowQueue",
    "PersistentWorkflowJob",
]
