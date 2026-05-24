"""REST API foundation layer.

Provides initial API endpoints for:
- workflow execution
- governance inspection
- analytics retrieval
- QA visibility
"""

from __future__ import annotations

from fastapi import FastAPI

from ..services.analytics import AnalyticsService
from ..services.provenance_registry import ProvenanceRegistry
from ..services.workflow_queue import WorkflowQueueService


app = FastAPI(
    title="Accessibility Operations API",
    version="0.1.0",
)

_queue = WorkflowQueueService()
_analytics = AnalyticsService()
_provenance = ProvenanceRegistry()


@app.get("/health")
def healthcheck() -> dict:
    return {
        "status": "ok",
        "service": "accessibility-operations-api",
    }


@app.get("/workflows")
def list_workflows() -> dict:
    return {
        "jobs": _queue.list_jobs(),
    }


@app.post("/workflows/enqueue")
def enqueue_workflow(
    workflow_name: str,
    asset_id: int,
    priority: int = 5,
) -> dict:
    job = _queue.enqueue(
        workflow_name=workflow_name,
        asset_id=asset_id,
        priority=priority,
    )

    return {
        "workflow": workflow_name,
        "asset_id": asset_id,
        "status": job.status,
    }


@app.get("/analytics")
def analytics_summary() -> dict:
    return _analytics.summarize()


@app.get("/provenance")
def provenance_events() -> dict:
    return {
        "events": _provenance.list_events(),
    }
