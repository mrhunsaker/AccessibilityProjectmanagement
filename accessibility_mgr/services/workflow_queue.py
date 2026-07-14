"""Workflow queue primitives and in-memory queue service.

Provides:
- ``WorkflowJob`` dataclass shared across queue implementations.
- ``WorkflowQueueService`` in-memory priority queue that implements
  the ``_QueueLike`` protocol used by ``WorkerRuntime``.

The SQLite-backed ``PersistentWorkflowQueue`` in ``persistent_queue.py``
is the production-grade replacement; this in-memory version is useful
for tests, lightweight deployments, and as a reference implementation.
"""

from __future__ import annotations

import heapq
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class WorkflowJob:
    """Represents a single queued workflow execution request."""

    workflow_name: str
    asset_id: int
    priority: int
    status: str
    created_at: str


class WorkflowQueueService:
    """In-memory priority queue for workflow execution requests.

    Thread-safe.  Implements the ``_QueueLike`` protocol expected by
    ``WorkerRuntime``: ``next_job()`` / ``complete_job()`` / ``fail_job()`` /
    ``list_jobs()``.
    """

    def __init__(self) -> None:
        self._queue: list[tuple[int, str, WorkflowJob]] = []
        self._counter = 0
        self._lock = threading.Lock()

    def enqueue(
        self,
        *,
        workflow_name: str,
        asset_id: int,
        priority: int = 5,
    ) -> WorkflowJob:
        """Add a new job to the queue and return it."""
        created_at = datetime.now(UTC).isoformat()
        job = WorkflowJob(
            workflow_name=workflow_name,
            asset_id=asset_id,
            priority=priority,
            status="queued",
            created_at=created_at,
        )
        with self._lock:
            self._counter += 1
            heapq.heappush(
                self._queue,
                (priority, self._counter, job),
            )
        return job

    def next_job(self) -> WorkflowJob | None:
        """Pop and return the highest-priority (lowest number) queued job.

        Returns ``None`` when the queue is empty.
        """
        with self._lock:
            while self._queue:
                _pri, _seq, job = heapq.heappop(self._queue)
                if job.status == "queued":
                    job.status = "running"
                    return job
        return None

    def complete_job(self, job: WorkflowJob) -> None:
        """Mark *job* as completed."""
        job.status = "completed"

    def fail_job(self, job: WorkflowJob) -> None:
        """Mark *job* as failed."""
        job.status = "failed"

    def list_jobs(self) -> list[dict[str, Any]]:
        """Return all jobs (queued, running, completed, failed) in insertion order."""
        with self._lock:
            return [
                {
                    "workflow_name": j.workflow_name,
                    "asset_id": j.asset_id,
                    "priority": j.priority,
                    "status": j.status,
                    "created_at": j.created_at,
                }
                for _pri, _seq, j in sorted(self._queue, key=lambda x: x[1])
            ]


__all__ = [
    "WorkflowJob",
    "WorkflowQueueService",
]
