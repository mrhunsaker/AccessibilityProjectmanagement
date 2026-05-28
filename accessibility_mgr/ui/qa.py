"""
QA Tooling page — runs accessibility validation tools and shows history.

Changes applied (see fix_specs.json):
  FIX-012  Run dialog now has optional job-type selector and job-ID input.
           When a job is linked, the result appears in that job's event log.
"""

from __future__ import annotations

import threading

from nicegui import ui

from ..db import queries as Q
from ..services.qa_service import QAService, QATool
from .components import notify_error, notify_success, section_header


def _tool_card(tool: QATool, result_area: ui.element) -> None:
    available = tool.is_available()
    border = "border-slate-200" if available else "border-amber-200 bg-amber-50"
    with ui.card().classes(f"p-4 rounded-xl border {border} w-full"):
        with ui.row().classes("items-start gap-3"):
            with ui.column().classes("flex-1 gap-1"):
                with ui.row().classes("items-center gap-2"):
                    ui.label(tool.name).classes("font-semibold text-slate-800 text-base")
                    ui.badge(tool.domain).classes(
                        "text-xs bg-blue-100 text-blue-700 rounded px-2"
                    )
                    if not available:
                        ui.badge("⚠ Not on PATH").classes(
                            "text-xs bg-amber-100 text-amber-700 rounded px-2"
                        )
                ui.label(tool.description).classes("text-sm text-slate-500")
                ui.label(f"Command: {tool.command_template}").classes(
                    "text-xs text-slate-400 font-mono"
                )

            with ui.column().classes("gap-2 shrink-0"):
                def _run(t: QATool = tool) -> None:
                    _run_tool_dialog(t, result_area)

                ui.button("▶ Run Validation", on_click=_run).classes(
                    "bg-blue-600 text-white text-sm rounded-lg px-3 py-1"
                )

                def _hist(t: QATool = tool) -> None:
                    _show_history(t.name, result_area)

                ui.button("📋 View History", on_click=_hist).props("flat dense").classes(
                    "text-slate-500 text-sm"
                )


def _run_tool_dialog(tool: QATool, result_area: ui.element) -> None:
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[540px] max-w-full"):
        ui.label(f"Run: {tool.name}").classes("text-xl font-bold text-slate-800")
        ui.label(tool.description).classes("text-sm text-slate-500")

        input_path = ui.input(
            "Input File Path (optional)",
            placeholder="/path/to/file.epub",
        ).classes("w-full")

        # FIX-012: optional job link
        ui.separator().classes("my-2")
        ui.label("Link to Job (optional)").classes(
            "text-xs font-semibold text-slate-500 uppercase tracking-wider"
        )
        ui.label(
            "When linked, this QA result will appear in that job's event log."
        ).classes("text-xs text-slate-400 mb-1")

        with ui.row().classes("gap-3 w-full"):
            job_type_sel = ui.select(
                ["(none)", "braille", "lp_ebraille", "tactile", "print"],
                value="(none)",
                label="Job Type",
            ).classes("flex-1")
            job_id_inp = ui.input(
                "Job ID", placeholder="numeric ID"
            ).classes("flex-1")

        with ui.row().classes("justify-end gap-3 mt-4"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _execute() -> None:
                dlg.close()
                result_area.clear()
                with result_area:
                    with ui.card().classes("p-4 rounded-xl border border-slate-200 w-full"):
                        ui.label(f"Running: {tool.name}…").classes(
                            "text-slate-600 font-medium"
                        )
                        ui.spinner("dots", size="sm")

                # FIX-012: parse job link before threading
                jtype_val = job_type_sel.value if job_type_sel.value != "(none)" else None
                jid_str = job_id_inp.value.strip()
                jid_val = int(jid_str) if jtype_val and jid_str.isdigit() else None

                def _do() -> None:
                    res = QAService.run_tool(
                        tool.name,
                        input_path=input_path.value.strip(),
                        job_type=jtype_val,
                        job_id=jid_val,
                    )
                    result_area.clear()
                    with result_area:
                        _render_result(tool.name, res, jtype_val, jid_val)

                threading.Thread(target=_do, daemon=True).start()

            ui.button("Run", on_click=_execute).classes("bg-blue-600 text-white")

    dlg.open()


def _render_result(
    tool_name: str,
    result: object,
    job_type: str | None = None,
    job_id: int | None = None,
) -> None:
    success = getattr(result, "success", False)
    output = getattr(result, "output", "")
    command = getattr(result, "command", "")
    border = "border-green-200 bg-green-50" if success else "border-red-200 bg-red-50"
    label_cls = "text-green-700" if success else "text-red-700"
    icon = "✅" if success else "❌"

    with ui.card().classes(f"p-5 rounded-xl border {border} w-full"):
        ui.label(
            f"{icon} {tool_name} — {'SUCCESS' if success else 'FAILED'}"
        ).classes(f"font-bold {label_cls} text-base mb-1")
        ui.label(f"Command: {command}").classes("text-xs text-slate-500 font-mono mb-1")
        if job_type and job_id:
            ui.label(
                f"Linked to {job_type} job #{job_id} — result recorded in event log"
            ).classes("text-xs text-indigo-600 mb-2")
        if output:
            ui.code(output).classes("text-xs w-full overflow-auto max-h-64")
        else:
            ui.label("(no output)").classes("text-slate-400 text-sm italic")


def _show_history(tool_name: str, result_area: ui.element) -> None:
    runs = Q.list_qa_runs(tool_name=tool_name, limit=20)
    result_area.clear()
    with result_area:
        with ui.card().classes("p-5 rounded-xl border border-slate-200 w-full"):
            ui.label(f"QA History — {tool_name}").classes(
                "font-semibold text-slate-700 mb-3"
            )
            if not runs:
                ui.label("No runs recorded yet.").classes("text-slate-400 text-sm")
                return
            for run in runs:
                ok = bool(run.get("success"))
                border = "border-green-100" if ok else "border-red-100"
                with ui.card().classes(f"p-3 rounded-lg border {border} mb-2"):
                    with ui.row().classes("items-center gap-3"):
                        ui.label("✅" if ok else "❌")
                        ui.label(str(run.get("ran_at", ""))[:19]).classes(
                            "text-xs text-slate-400 font-mono"
                        )
                        if run.get("job_type") and run.get("job_id"):
                            ui.badge(
                                f"{run['job_type']} #{run['job_id']}"
                            ).classes("text-xs bg-indigo-50 text-indigo-700 rounded px-1")
                        ui.label(run.get("command", "")).classes(
                            "text-xs text-slate-500 font-mono flex-1 truncate"
                        )
                    if run.get("output"):
                        ui.code(str(run["output"])[:400]).classes(
                            "text-xs w-full overflow-auto max-h-32 mt-1"
                        )


def qa_page(content_area: ui.element) -> None:
    """Render the QA Tooling page."""
    content_area.clear()
    with content_area:
        section_header(
            "Accessibility QA Tooling",
            "Run validation tools against accessibility-production assets",
        )

        result_area = ui.column().classes("w-full gap-3 mt-2")

        ui.label("Available Tools").classes(
            "text-sm font-semibold text-slate-500 uppercase tracking-wider mt-4 mb-2"
        )
        for tool in QAService.list_tools():
            _tool_card(tool, result_area)

        ui.label("Recent QA Runs").classes(
            "text-sm font-semibold text-slate-500 uppercase tracking-wider mt-8 mb-2"
        )
        recent = Q.list_qa_runs(limit=10)
        if not recent:
            ui.label("No QA runs recorded yet. Run a tool above.").classes(
                "text-slate-400 text-sm"
            )
        else:
            with ui.card().classes("w-full rounded-xl border border-slate-200 overflow-hidden"):
                with ui.row().classes(
                    "px-4 py-2 bg-slate-50 text-xs font-semibold text-slate-500 "
                    "uppercase tracking-wider border-b"
                ):
                    ui.label("Tool").classes("w-44")
                    ui.label("Linked Job").classes("w-36")
                    ui.label("Time").classes("w-36")
                    ui.label("Result").classes("w-20")
                    ui.label("Command").classes("flex-1")
                for run in recent:
                    ok = bool(run.get("success"))
                    with ui.row().classes(
                        "items-center px-4 py-2 border-b border-slate-50 last:border-0 gap-2"
                    ):
                        ui.label(run.get("tool_name", "—")).classes("w-44 text-sm")
                        if run.get("job_type") and run.get("job_id"):
                            ui.label(
                                f"{run['job_type']} #{run['job_id']}"
                            ).classes("w-36 text-xs font-mono text-indigo-600")
                        else:
                            ui.label("—").classes("w-36 text-xs text-slate-400")
                        ui.label(str(run.get("ran_at", ""))[:19]).classes(
                            "w-36 text-xs text-slate-400 font-mono"
                        )
                        ui.badge("✓ OK" if ok else "✗ FAIL").classes(
                            f"w-20 text-center text-xs rounded "
                            f"{'bg-green-100 text-green-700' if ok else 'bg-red-100 text-red-700'}"
                        )
                        ui.label(run.get("command", "")).classes(
                            "flex-1 text-xs font-mono text-slate-500 truncate"
                        )
