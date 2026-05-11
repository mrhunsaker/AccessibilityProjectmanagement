"""
Pipeline orchestration page — executes multi-stage accessibility production pipelines.

Each pipeline run calls PipelineService.run_pipeline() which invokes each step
via ExecutionService and persists results to DB via db.queries.
"""

from __future__ import annotations

import threading

from nicegui import ui

import db.queries as Q
from services.pipeline_service import PipelineService, WorkflowPipeline
from ui.components import notify_error, notify_success, section_header


def _pipeline_card(pipeline: WorkflowPipeline, result_area: ui.element) -> None:
    with ui.card().classes("p-5 rounded-xl border border-slate-200 w-full"):
        ui.label(pipeline.name).classes("font-semibold text-slate-800 text-base")
        ui.label(pipeline.description).classes("text-sm text-slate-500 mb-3")

        with ui.row().classes("gap-2 flex-wrap mb-3"):
            for i, step in enumerate(pipeline.steps):
                with ui.row().classes("items-center gap-1"):
                    ui.badge(f"{i + 1}").classes(
                        "bg-blue-600 text-white text-xs rounded-full w-5 h-5 "
                        "flex items-center justify-center"
                    )
                    with ui.column().classes("gap-0"):
                        ui.label(step.name).classes("text-xs font-medium text-slate-700")
                        ui.label(step.tool).classes("text-xs text-slate-400")
                    if i < len(pipeline.steps) - 1:
                        ui.label("→").classes("text-slate-300 text-xs")

        with ui.row().classes("gap-2"):
            def _run(p: WorkflowPipeline = pipeline) -> None:
                _run_pipeline_dialog(p, result_area)

            ui.button("▶ Execute Pipeline", on_click=_run).classes(
                "bg-indigo-600 text-white text-sm rounded-lg px-3 py-1"
            )

            def _hist(p: WorkflowPipeline = pipeline) -> None:
                _show_pipeline_history(p.name, result_area)

            ui.button("📋 View History", on_click=_hist).props("flat dense").classes(
                "text-slate-500 text-sm"
            )


def _run_pipeline_dialog(pipeline: WorkflowPipeline, result_area: ui.element) -> None:
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[520px] max-w-full"):
        ui.label(f"Execute: {pipeline.name}").classes("text-xl font-bold text-slate-800")
        ui.label(pipeline.description).classes("text-sm text-slate-500")

        input_path = ui.input(
            "Input File Path (optional)",
            placeholder="/path/to/source-document.docx",
        ).classes("w-full")

        ui.label("Steps that will run:").classes("text-sm font-medium text-slate-600 mt-2")
        for i, step in enumerate(pipeline.steps):
            with ui.row().classes("items-center gap-2 text-sm text-slate-600"):
                ui.label(f"{i + 1}.").classes("w-4 shrink-0 text-slate-400")
                ui.label(step.name).classes("font-medium")
                ui.label(f"({step.tool})").classes("text-slate-400")

        with ui.row().classes("justify-end gap-3 mt-4"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _execute() -> None:
                dlg.close()
                result_area.clear()
                with result_area:
                    with ui.card().classes("p-4 rounded-xl border border-slate-200 w-full"):
                        ui.label(f"Running pipeline: {pipeline.name}…").classes(
                            "text-slate-600 font-medium mb-2"
                        )
                        ui.spinner("dots", size="sm")

                def _do() -> None:
                    run_result = PipelineService.run_pipeline(
                        pipeline.name, input_path=input_path.value.strip()
                    )
                    result_area.clear()
                    with result_area:
                        _render_pipeline_result(pipeline, run_result)

                threading.Thread(target=_do, daemon=True).start()

            ui.button("Execute", on_click=_execute).classes("bg-indigo-600 text-white")

    dlg.open()


def _render_pipeline_result(pipeline: WorkflowPipeline, run_result: object) -> None:
    overall = getattr(run_result, "overall_success", False)
    step_results = getattr(run_result, "step_results", [])
    run_id = getattr(run_result, "run_id", -1)
    border = "border-green-200 bg-green-50" if overall else "border-red-200 bg-red-50"
    label_cls = "text-green-700" if overall else "text-red-700"
    icon = "✅" if overall else "❌"

    with ui.card().classes(f"p-5 rounded-xl border {border} w-full"):
        ui.label(
            f"{icon} {pipeline.name} — {'ALL STEPS PASSED' if overall else 'ONE OR MORE STEPS FAILED'}"
        ).classes(f"font-bold {label_cls} text-base mb-3")

        if run_id > 0:
            ui.label(f"Run ID: {run_id}").classes("text-xs text-slate-400 font-mono mb-3")

        for i, (step, result) in enumerate(
            zip(pipeline.steps, step_results)
        ):
            ok = getattr(result, "success", False)
            s_border = "border-green-100" if ok else "border-red-100"
            s_bg = "bg-green-50" if ok else "bg-red-50"
            with ui.card().classes(f"p-3 rounded-lg border {s_border} {s_bg} mb-2"):
                with ui.row().classes("items-center gap-2 mb-1"):
                    ui.label("✓" if ok else "✗").classes(
                        f"font-bold {'text-green-600' if ok else 'text-red-600'}"
                    )
                    ui.label(f"Step {i + 1}: {step.name}").classes(
                        "font-medium text-slate-700 text-sm"
                    )
                    ui.badge(step.tool).classes(
                        "text-xs bg-slate-100 text-slate-600 rounded px-1"
                    )
                ui.label(getattr(result, "command", "")).classes(
                    "text-xs font-mono text-slate-400 mb-1"
                )
                output = getattr(result, "output", "")
                if output:
                    ui.code(output[:600]).classes(
                        "text-xs w-full overflow-auto max-h-32"
                    )


def _show_pipeline_history(pipeline_name: str, result_area: ui.element) -> None:
    runs = Q.list_pipeline_runs(limit=20)
    runs = [r for r in runs if r.get("pipeline_name") == pipeline_name]
    result_area.clear()
    with result_area:
        with ui.card().classes("p-5 rounded-xl border border-slate-200 w-full"):
            ui.label(f"Pipeline History — {pipeline_name}").classes(
                "font-semibold text-slate-700 mb-3"
            )
            if not runs:
                ui.label("No runs recorded yet.").classes("text-slate-400 text-sm")
                return
            for run in runs:
                ok = run.get("status") == "completed"
                border = "border-green-100" if ok else "border-red-100"
                with ui.card().classes(f"p-3 rounded-lg border {border} mb-2"):
                    with ui.row().classes("items-center gap-3"):
                        ui.label("✅" if ok else "❌")
                        ui.label(f"Run #{run['id']}").classes(
                            "text-sm font-medium text-slate-700"
                        )
                        ui.badge(run.get("status", "?")).classes(
                            "text-xs bg-slate-100 text-slate-600 rounded px-1"
                        )
                        ui.label(str(run.get("started_at", ""))[:19]).classes(
                            "text-xs text-slate-400 font-mono"
                        )
                        if run.get("finished_at"):
                            ui.label(f"→ {str(run['finished_at'])[:19]}").classes(
                                "text-xs text-slate-400 font-mono"
                            )

                    steps = Q.list_pipeline_step_runs(run["id"])
                    if steps:
                        with ui.column().classes("mt-2 gap-1 pl-4"):
                            for s in steps:
                                s_ok = bool(s.get("success"))
                                ui.label(
                                    f"{'✓' if s_ok else '✗'} {s['step_name']} ({s['tool']})"
                                ).classes(
                                    f"text-xs {'text-green-600' if s_ok else 'text-red-600'}"
                                )


def pipelines_page(content_area: ui.element) -> None:
    """Render the Workflow Pipelines page."""
    content_area.clear()
    with content_area:
        section_header(
            "Workflow Pipelines",
            "Execute multi-stage accessibility production pipelines",
        )

        result_area = ui.column().classes("w-full gap-3 mt-2")

        ui.label("Available Pipelines").classes(
            "text-sm font-semibold text-slate-500 uppercase tracking-wider mt-4 mb-2"
        )

        for pipeline in PipelineService.list_pipelines():
            _pipeline_card(pipeline, result_area)

        ui.label("Recent Pipeline Runs").classes(
            "text-sm font-semibold text-slate-500 uppercase tracking-wider mt-8 mb-2"
        )
        recent_runs = Q.list_pipeline_runs(limit=10)
        if not recent_runs:
            ui.label("No pipeline runs recorded yet. Execute a pipeline above.").classes(
                "text-slate-400 text-sm"
            )
        else:
            with ui.card().classes("w-full rounded-xl border border-slate-200 overflow-hidden"):
                with ui.row().classes(
                    "px-4 py-2 bg-slate-50 text-xs font-semibold text-slate-500 "
                    "uppercase tracking-wider border-b"
                ):
                    ui.label("Pipeline").classes("flex-1")
                    ui.label("Status").classes("w-24")
                    ui.label("Started").classes("w-36")
                    ui.label("Finished").classes("w-36")
                for run in recent_runs:
                    ok = run.get("status") == "completed"
                    with ui.row().classes(
                        "items-center px-4 py-2 border-b border-slate-50 last:border-0 gap-2"
                    ):
                        ui.label(run.get("pipeline_name", "—")).classes(
                            "flex-1 text-sm text-slate-700"
                        )
                        ui.badge(run.get("status", "?")).classes(
                            f"w-24 text-center text-xs rounded "
                            f"{'bg-green-100 text-green-700' if ok else 'bg-red-100 text-red-700'}"
                        )
                        ui.label(str(run.get("started_at", ""))[:19]).classes(
                            "w-36 text-xs font-mono text-slate-400"
                        )
                        ui.label(str(run.get("finished_at", "") or "—")[:19]).classes(
                            "w-36 text-xs font-mono text-slate-400"
                        )
