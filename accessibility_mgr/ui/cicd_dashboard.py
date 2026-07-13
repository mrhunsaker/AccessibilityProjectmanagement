"""CI/CD accessibility validation dashboard.

AUDIT-FIX (follow-up): this page used to be a static capability checklist
with no way to actually trigger a validation run — it only displayed
history that nothing in the app ever wrote to. It now has a real "Run
Validation" form that calls CICDValidationHookService against a real
EPUB path and persists the result to the database (see
integrations/cicd_hooks.py + db/queries.py).
"""

from __future__ import annotations

import threading

from nicegui import ui

from ..integrations.cicd_hooks import CICDValidationHookService
from .components import notify_error, section_header

_service = CICDValidationHookService()

_STATUS_STYLE = {
    "passed": ("✅", "text-green-700 bg-green-50 border-green-200"),
    "failed": ("❌", "text-red-700 bg-red-50 border-red-200"),
    "warning": ("⚠️", "text-amber-700 bg-amber-50 border-amber-200"),
}


def cicd_dashboard(content_area: ui.element) -> None:
    """Render CI/CD accessibility validation dashboard."""

    content_area.clear()

    with content_area:
        section_header(
            "CI/CD Accessibility Validation",
            "Run DAISY Ace and EPUBCheck as a release gate, and review validation history",
        )

        result_area = ui.column().classes("w-full gap-3 mt-2")

        with ui.card().classes(
            "w-full p-5 rounded-xl border border-slate-200 mb-6"
        ):
            ui.label("Run Validation").classes(
                "text-base font-semibold text-slate-700 mb-3"
            )
            ui.label(
                "Fails the gate if either tool reports violations "
                "(non-zero exit code); warns if a tool isn't installed."
            ).classes("text-xs text-slate-500 mb-3")

            with ui.row().classes("gap-3 w-full items-end"):
                pipeline_id_inp = ui.input(
                    "Pipeline ID",
                    placeholder="e.g. ci-build-1423",
                ).classes("flex-1")
                epub_path_inp = ui.input(
                    "EPUB File Path*",
                    placeholder="/path/to/file.epub",
                ).classes("flex-1")

                def _run_validation() -> None:
                    epub_path = epub_path_inp.value.strip()
                    if not epub_path:
                        notify_error("Enter an EPUB file path first.")
                        return

                    pipeline_id = pipeline_id_inp.value.strip() or "manual-run"

                    result_area.clear()
                    with result_area:
                        with ui.card().classes(
                            "p-4 rounded-xl border border-slate-200 w-full"
                        ):
                            ui.label(
                                f"Validating {epub_path}…"
                            ).classes("text-slate-600 font-medium")
                            ui.spinner("dots", size="sm")

                    def _do() -> None:
                        result = _service.validate_epub_pipeline(
                            pipeline_id=pipeline_id, epub_path=epub_path
                        )
                        result_area.clear()
                        with result_area:
                            _render_validation_result(result)
                            _render_history(_service.list_history())

                    threading.Thread(target=_do, daemon=True).start()

                ui.button("▶ Run Validation", on_click=_run_validation).classes(
                    "bg-blue-600 text-white"
                )

        ui.label("Validation History").classes(
            "text-sm font-semibold text-slate-500 uppercase tracking-wider mb-2"
        )
        _render_history(_service.list_history())


def _render_validation_result(result) -> None:
    icon, classes = _STATUS_STYLE.get(result.status, ("•", "border-slate-200"))
    with ui.card().classes(f"w-full p-4 border {classes} rounded-xl"):
        ui.label(f"{icon} {result.pipeline_id} — {result.status.upper()}").classes(
            "font-bold text-base mb-1"
        )
        ace_exec = result.metadata.get("ace", {}).get("execution", {})
        epubcheck_exec = result.metadata.get("epubcheck", {}).get("execution", {})
        ui.label(
            f"Ace exit code: {ace_exec.get('exit_code', '—')} · "
            f"EPUBCheck exit code: {epubcheck_exec.get('exit_code', '—')}"
        ).classes("text-xs text-slate-500")


def _render_history(history: list[dict]) -> None:
    with ui.card().classes(
        "w-full p-5 rounded-xl border border-slate-200"
    ):
        ui.label("Recent Validation Activity").classes(
            "text-base font-semibold text-slate-700 mb-3"
        )

        if not history:
            ui.label(
                "No CI/CD validation activity recorded yet. Run a validation above."
            ).classes("text-sm text-slate-500")
            return

        for item in history:
            icon, classes = _STATUS_STYLE.get(item["status"], ("•", "border-slate-200"))
            with ui.row().classes(
                f"w-full items-center justify-between border-b border-slate-100 py-2"
            ):
                with ui.column().classes("gap-0"):
                    ui.label(item["pipeline_id"]).classes(
                        "text-sm font-medium text-slate-700"
                    )
                    ui.label(item.get("epub_path", "")).classes(
                        "text-xs text-slate-400 font-mono"
                    )

                ui.label(str(item.get("executed_at", ""))[:19]).classes(
                    "text-xs text-slate-400 font-mono"
                )

                ui.badge(f"{icon} {item['status']}").classes(
                    f"text-xs rounded px-2 {classes}"
                )
