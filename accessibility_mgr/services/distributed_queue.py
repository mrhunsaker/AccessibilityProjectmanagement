"""Persistent distributed workflow queue coordination."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Any

from .sqlite_store import SQLiteStore


@dataclass(slots=True)
class QueueLease:
    lease_id: str
    workflow_id: int
    worker_id: str
    leased_until: str


class DistributedQueueService:
    """Persistent workflow queue coordination service."""

    def __init__(self, store: SQLiteStore | None = None) -> None:
        self.store = store or SQLiteStore()
        self._initialize_tables()

    def _initialize_tables(self) -> None:
        self.store.execute(
            """
            CREATE TABLE IF NOT EXISTS distributed_workflow_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_name TEXT NOT NULL,
                asset_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                priority INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    def enqueue(
        self,
        *,
        workflow_name: str,
        asset_id: int,
        priority: int = 5,
    ) -> None:
        self.store.execute(
            """
            INSERT INTO distributed_workflow_queue (
                workflow_name,
                asset_id,
                status,
                priority
            ) VALUES (?, ?, ?, ?)
            """,
            (workflow_name, asset_id, "queued", priority),
        )

    def acquire_lease(
        self,
        *,
        worker_id: str,
        lease_minutes: int = 5,
    ) -> QueueLease | None:
        rows = self.store.fetch_all(
            """
            SELECT *
            FROM distributed_workflow_queue
            WHERE status = 'queued'
            ORDER BY priority ASC, created_at ASC
            LIMIT 1
            """
        )

        if not rows:
            return None

        workflow = rows[0]

        self.store.execute(
            """
            UPDATE distributed_workflow_queue
            SET status = 'leased'
            WHERE id = ?
            """,
            (workflow["id"],),
        )

        return QueueLease(
            lease_id=str(uuid.uuid4()),
            workflow_id=workflow["id"],
            worker_id=worker_id,
            leased_until=(
                datetime.now(timezone.utc)
                + timedelta(minutes=lease_minutes)
            ).isoformat(),
        )

    def complete_workflow(self, workflow_id: int) -> None:
        self.store.execute(
            """
            UPDATE distributed_workflow_queue
            SET status = 'completed'
            WHERE id = ?
            """,
            (workflow_id,),
        )

    def list_workflows(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.store.fetch_all(
            "SELECT * FROM distributed_workflow_queue"
        )]


__all__ = [
    "DistributedQueueService",
    "QueueLease",
]
