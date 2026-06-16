"""Workflow execution monitoring dashboard."""

from __future__ import annotations

import os

from nicegui import ui

from ..services.worker_runtime import WorkerRuntime
from ..services.workflow_queue import WorkflowQueueService
from .components import section_header


_queue = WorkflowQueueService()
_runtime = WorkerRuntime(_queue)

_started = False


def _ensure_runtime_started() -> None:
    """Start the worker runtime the first time the monitor page is opened."""
    global _started  # noqa: PLW0603
    if _started:
        return
    _started = True

    if os.getenv("ACCESSMAN_DEV", "0").lower() in {"1", "true", "yes"}:
        # Seed dev-only demo jobs so the monitor is not empty during development.
        _queue.enqueue(workflow_name="epub_accessibility_pipeline", asset_id=1, priority=1)
        _queue.enqueue(workflow_name="metadata_governance_pipeline", asset_id=2, priority=3)

    import logging
    from ..services.pipeline_service import PipelineService

    _wm_log = logging.getLogger(__name__)

    def _real_handler(job) -> None:
        """Dispatch workflow jobs to PipelineService by workflow_name."""
        try:
            PipelineService.run_pipeline(job.workflow_name)
        except Exception as exc:  # noqa: BLE001
            _wm_log.error(
                "Worker handler error for workflow %r (asset %s): %s",
                job.workflow_name, job.asset_id, exc,
                exc_info=True,
            )

    _runtime.start(_real_handler)



def workflow_monitor_page(content_area: ui.element) -> None:
    """Render workflow execution monitoring UI."""
    _ensure_runtime_started()
    content_area.clear()

    with content_area:
        section_header(
            "Workflow Monitor",
            "Background orchestration and execution monitoring",
        )

        with ui.card().classes(
            "w-full p-5 rounded-xl border border-slate-200 mb-6"
        ):
            ui.label("Queue State").classes(
                "text-base font-semibold text-slate-700 mb-3"
            )

            for job in _queue.list_jobs():
                with ui.row().classes(
                    "items-center justify-between border-b border-slate-100 py-2"
                ):
                    with ui.column().classes("gap-0"):
                        ui.label(job["workflow_name"]).classes(
                            "text-sm font-medium text-slate-700"
                        )

                        ui.label(
                            f"Asset #{job['asset_id']}"
                        ).classes("text-xs text-slate-500")

                    ui.badge(job["status"]).classes(
                        "bg-slate-100 text-slate-700"
                    )

        with ui.card().classes(
            "w-full p-5 rounded-xl border border-slate-200"
        ):
            ui.label("Worker Executions").classes(
                "text-base font-semibold text-slate-700 mb-3"
            )

            for execution in _runtime.list_executions():
                with ui.row().classes(
                    "items-start justify-between border-b border-slate-100 py-2 gap-3"
                ):
                    with ui.column().classes("gap-0 flex-1"):
                        ui.label(execution["workflow_name"]).classes(
                            "text-sm font-medium text-slate-700"
                        )

                        ui.label(
                            f"Worker: {execution['worker_name']}"
                        ).classes("text-xs text-slate-500")

                        ui.label(
                            f"Asset #{execution['asset_id']}"
                        ).classes("text-xs text-slate-500")

                    ui.label(execution["status"]).classes(
                        "text-sm font-semibold text-green-600"
                    )

                    ui.label(execution["started_at"][:19]).classes(
                        "text-xs text-slate-400 font-mono"
                    )
