"""Background workflow worker runtime."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from .workflow_queue import WorkflowJob, WorkflowQueueService


@dataclass(slots=True)
class WorkerExecution:
    worker_name: str
    workflow_name: str
    asset_id: int
    started_at: str
    completed_at: str | None
    status: str


class WorkerRuntime:
    """Simple threaded worker runtime.

    Foundation for:
    - distributed orchestration
    - SLA monitoring
    - retry execution
    - async workflow execution
    """

    def __init__(
        self,
        queue_service: WorkflowQueueService,
    ) -> None:
        self.queue_service = queue_service
        self._executions: list[WorkerExecution] = []
        self._running = False
        self._thread: threading.Thread | None = None

    def start(
        self,
        handler: Callable[[WorkflowJob], None],
        *,
        poll_interval: float = 1.0,
    ) -> None:
        if self._running:
            return

        self._running = True

        def _runner() -> None:
            while self._running:
                job = self.queue_service.next_job()

                if not job:
                    time.sleep(poll_interval)
                    continue

                execution = WorkerExecution(
                    worker_name="default-worker",
                    workflow_name=job.workflow_name,
                    asset_id=job.asset_id,
                    started_at=datetime.now(timezone.utc).isoformat(),
                    completed_at=None,
                    status="running",
                )

                self._executions.append(execution)

                try:
                    handler(job)
                    self.queue_service.complete_job(job)
                    execution.status = "completed"
                except Exception:
                    self.queue_service.fail_job(job)
                    execution.status = "failed"
                finally:
                    execution.completed_at = (
                        datetime.now(timezone.utc).isoformat()
                    )

        self._thread = threading.Thread(
            target=_runner,
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False

        if self._thread:
            self._thread.join(timeout=2)

    def list_executions(self) -> list[dict]:
        return [
            {
                "worker_name": execution.worker_name,
                "workflow_name": execution.workflow_name,
                "asset_id": execution.asset_id,
                "started_at": execution.started_at,
                "completed_at": execution.completed_at,
                "status": execution.status,
            }
            for execution in self._executions
        ]


__all__ = [
    "WorkerExecution",
    "WorkerRuntime",
]
