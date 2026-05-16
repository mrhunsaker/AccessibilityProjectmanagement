"""REST API service layer.

Provides API-oriented orchestration access for:
- workflow execution
- analytics retrieval
- provenance inspection
- governance operations
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from ..services.persistent_analytics import PersistentAnalyticsService
from ..services.persistent_provenance import (
    PersistentProvenanceRegistry,
)
from ..services.workflow_queue import WorkflowQueueService


@dataclass(slots=True)
class APIResponse:
    status: str
    payload: dict[str, Any]


class AccessibilityPlatformAPI:
    """Internal REST-oriented application service facade."""

    def __init__(self) -> None:
        self.workflow_queue = WorkflowQueueService()
        self.analytics = PersistentAnalyticsService()
        self.provenance = PersistentProvenanceRegistry()

    def enqueue_workflow(
        self,
        *,
        workflow_name: str,
        asset_id: int,
        priority: int = 5,
    ) -> dict[str, Any]:
        job = self.workflow_queue.enqueue(
            workflow_name=workflow_name,
            asset_id=asset_id,
            priority=priority,
        )

        self.provenance.register_event(
            asset_id=asset_id,
            event_type="workflow_enqueued",
            summary=f"Workflow queued: {workflow_name}",
            metadata={"priority": priority},
        )

        return asdict(
            APIResponse(
                status="accepted",
                payload={
                    "workflow": workflow_name,
                    "asset_id": asset_id,
                    "priority": priority,
                    "status": job.status,
                },
            )
        )

    def analytics_summary(self) -> dict[str, Any]:
        return asdict(
            APIResponse(
                status="ok",
                payload=self.analytics.summarize(),
            )
        )

    def provenance_events(self) -> dict[str, Any]:
        return asdict(
            APIResponse(
                status="ok",
                payload={
                    "events": self.provenance.list_events(),
                },
            )
        )


__all__ = [
    "AccessibilityPlatformAPI",
    "APIResponse",
]
