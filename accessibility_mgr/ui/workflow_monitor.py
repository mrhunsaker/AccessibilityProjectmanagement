"""Workflow execution monitoring dashboard."""

from __future__ import annotations

from nicegui import ui

from ..services.worker_runtime import WorkerRuntime
from ..services.workflow_queue import WorkflowQueueService
from .components import section_header


_queue = WorkflowQueueService()
_runtime = WorkerRuntime(_queue)


# Seed representative jobs.
_queue.enqueue(
    workflow_name="epub_accessibility_pipeline",
    asset_id=1,
    priority=1,
)

_queue.enqueue(
    workflow_name="metadata_governance_pipeline",
    asset_id=2,
    priority=3,
)


def _mock_handler(job) -> None:
    """Simulated workflow execution handler."""

    import time

    time.sleep(0.2)


_runtime.start(_mock_handler)



def workflow_monitor_page(content_area: ui.element) -> None:
    """Render workflow execution monitoring UI."""

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
