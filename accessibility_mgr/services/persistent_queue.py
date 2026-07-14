"""Persistent distributed workflow queue backend.

AUDIT-FIX-004/006: this module was fully implemented (a genuine
SQLite-backed queue) but was never imported anywhere else in the
codebase — the live app used the in-memory WorkflowQueueService instead,
so "Persistent SQLite-backed workflow queue" was true of this file in
isolation but not true of anything a user could actually reach. It now
has full method parity with WorkflowQueueService (next_job / complete_job
/ fail_job) so it can be used as a drop-in replacement, and
services/singletons.py has been updated to use it.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _default_db_path() -> Path:
    """Resolve the canonical DB path from schema to avoid drift."""
    try:
        from ..db.schema import DB_PATH
        return DB_PATH
    except Exception:
        # Fallback for standalone / test use where schema is not importable
        return Path("accessibility_mgr.db")


@dataclass(slots=True)
class PersistentWorkflowJob:
    id: int
    workflow_name: str
    asset_id: int
    priority: int
    status: str
    created_at: str


class PersistentWorkflowQueue:
    """SQLite-backed distributed workflow queue.

    Method names intentionally mirror WorkflowQueueService
    (enqueue / next_job / complete_job / fail_job / list_jobs) so this can
    be used as a drop-in replacement wherever that class is used.
    """

    def __init__(self, database_path: Path | None = None) -> None:
        self.database_path = database_path or _default_db_path()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
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

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO workflow_queue (
                    workflow_name, asset_id, priority, status, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (workflow_name, asset_id, priority, "queued", created_at),
            )
            job_id = cursor.lastrowid

        return PersistentWorkflowJob(
            id=job_id,
            workflow_name=workflow_name,
            asset_id=asset_id,
            priority=priority,
            status="queued",
            created_at=created_at,
        )

    def next_job(self) -> PersistentWorkflowJob | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, workflow_name, asset_id, priority, created_at
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

        return PersistentWorkflowJob(
            id=row[0],
            workflow_name=row[1],
            asset_id=row[2],
            priority=row[3],
            status="running",
            created_at=row[4],
        )

    def complete_job(self, job: PersistentWorkflowJob) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE workflow_queue SET status = 'completed' WHERE id = ?",
                (job.id,),
            )
        job.status = "completed"

    def fail_job(self, job: PersistentWorkflowJob) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE workflow_queue SET status = 'failed' WHERE id = ?",
                (job.id,),
            )
        job.status = "failed"

    def list_jobs(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, workflow_name, asset_id, priority,
                       status, created_at
                FROM workflow_queue
                ORDER BY priority ASC, created_at ASC
                """
            ).fetchall()

        return [
            {
                "id": row[0],
                "workflow_name": row[1],
                "asset_id": row[2],
                "priority": row[3],
                "status": row[4],
                "created_at": row[5],
            }
            for row in rows
        ]


__all__ = [
    "PersistentWorkflowQueue",
    "PersistentWorkflowJob",
]
