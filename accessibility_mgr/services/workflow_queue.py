"""Workflow queue orchestration primitives."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class WorkflowJob:
    workflow_name: str
    asset_id: int
    priority: int
    status: str
    created_at: str


class WorkflowQueueService:
    """In-memory workflow queue abstraction.

    Designed to evolve into:
    - distributed workers
    - async execution
    - queue persistence
    - SLA orchestration
    """

    def __init__(self) -> None:
        self._jobs: list[WorkflowJob] = []

    def enqueue(
        self,
        *,
        workflow_name: str,
        asset_id: int,
        priority: int = 5,
    ) -> WorkflowJob:
        job = WorkflowJob(
            workflow_name=workflow_name,
            asset_id=asset_id,
            priority=priority,
            status="queued",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        self._jobs.append(job)
        self._jobs.sort(key=lambda j: j.priority)

        return job

    def next_job(self) -> WorkflowJob | None:
        queued = [job for job in self._jobs if job.status == "queued"]

        if not queued:
            return None

        job = queued[0]
        job.status = "running"
        return job

    def complete_job(self, job: WorkflowJob) -> None:
        job.status = "completed"

    def fail_job(self, job: WorkflowJob) -> None:
        job.status = "failed"

    def list_jobs(self) -> list[dict[str, Any]]:
        return [asdict(job) for job in self._jobs]


__all__ = [
    "WorkflowJob",
    "WorkflowQueueService",
]
