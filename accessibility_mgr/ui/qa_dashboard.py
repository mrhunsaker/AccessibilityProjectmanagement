"""EPUB accessibility QA review page.

Runs a real DAISY Ace accessibility check against a user-supplied EPUB
file, then opens a popup form pre-filled with the measures Ace reported
(score, pass/fail, issues) so a reviewer can confirm or adjust them
before submitting the result to the database.

AUDIT-FIX-002: this page previously ran against a hardcoded
SAMPLE_EPUBS list through a self-documented "simulated" Ace check, and
persisted results to an in-memory QAPersistenceService that was wiped
on every restart. It now calls the real binary integration
(services/epub_qa.py -> services/toolchain_binaries.py) and writes
confirmed measures to the qa_measure table via db/queries.py.
"""

from __future__ import annotations

import threading

from nicegui import ui

from ..db import queries as Q
from ..services.epub_qa import EPUBQAService, QAResult
from .components import notify_error, notify_success, section_header

_qa_service = EPUBQAService()

_JOB_TYPES = ["(none)", "braille", "lp_ebraille", "epub3_daisy", "tactile", "print"]


def qa_dashboard_page(content_area: ui.element) -> None:
    """Render the EPUB accessibility QA review page."""
    content_area.clear()

    with content_area:
        section_header(
            "EPUB Accessibility QA Review",
            "Run DAISY Ace against a real EPUB, then review and submit the measures",
        )

        result_area = ui.column().classes("w-full gap-3 mt-2")

        with ui.card().classes("w-full p-5 rounded-xl border border-slate-200"):
            ui.label("Run Accessibility Check").classes(
                "text-lg font-semibold text-slate-700 mb-3"
            )

            epub_path_input = ui.input(
                "EPUB File Path",
                placeholder="/path/to/file.epub",
            ).classes("w-full")

            ui.separator().classes("my-2")
            ui.label("Link to Job (optional)").classes(
                "text-xs font-semibold text-slate-500 uppercase tracking-wider"
            )
            ui.label(
                "When linked, the submitted measure appears in that job's event log."
            ).classes("text-xs text-slate-400 mb-1")

            with ui.row().classes("gap-3 w-full"):
                job_type_sel = ui.select(
                    _JOB_TYPES, value="(none)", label="Job Type",
                ).classes("flex-1")
                job_id_inp = ui.input(
                    "Job ID", placeholder="numeric ID",
                ).classes("flex-1")

            def _run_check() -> None:
                epub_path = epub_path_input.value.strip()
                if not epub_path:
                    notify_error("Enter an EPUB file path first.")
                    return

                job_type_val = (
                    job_type_sel.value if job_type_sel.value != "(none)" else None
                )
                job_id_raw = job_id_inp.value.strip()
                job_id_val = (
                    int(job_id_raw)
                    if job_type_val and job_id_raw.isdigit()
                    else None
                )

                result_area.clear()
                with result_area:
                    with ui.card().classes(
                        "p-4 rounded-xl border border-slate-200 w-full"
                    ):
                        ui.label(f"Running DAISY Ace against {epub_path}…").classes(
                            "text-slate-600 font-medium"
                        )
                        ui.spinner("dots", size="sm")

                def _do() -> None:
                    # asset_id is only used as an in-process dict key inside
                    # EPUBQAService; the database link is job_type/job_id.
                    result = _qa_service.run_ace_check(
                        asset_id=job_id_val or 0,
                        epub_path=epub_path,
                    )
                    result_area.clear()
                    with result_area:
                        _render_result_card(result, epub_path)
                    _open_measure_dialog(
                        result, epub_path, job_type_val, job_id_val, measures_box
                    )

                threading.Thread(target=_do, daemon=True).start()

            ui.button("▶ Run Ace Check", on_click=_run_check).classes(
                "bg-blue-600 text-white mt-4"
            )

        ui.label("Submitted QA Measures").classes(
            "text-sm font-semibold text-slate-500 uppercase tracking-wider mt-8 mb-2"
        )
        measures_box = ui.column().classes("w-full gap-2")
        _render_measures_box(measures_box)


def _issue_rows(issues) -> None:
    """Render a list of QAIssue (or dict) entries with severity coloring."""
    for issue in issues:
        severity = getattr(issue, "severity", None) or issue.get("severity", "warning")
        code = getattr(issue, "code", None) or issue.get("code", "")
        message = getattr(issue, "message", None) or issue.get("message", "")
        color = {
            "error": "text-red-600",
            "warning": "text-amber-600",
            "info": "text-slate-500",
        }.get(severity, "text-amber-600")
        ui.label(f"[{severity.upper()}] {code}: {message}").classes(
            f"text-xs {color}"
        )


def _render_result_card(result: QAResult, epub_path: str) -> None:
    status = "PASSED" if result.passed else "FAILED"
    border = "border-green-200 bg-green-50" if result.passed else "border-red-200 bg-red-50"
    color = "text-green-700" if result.passed else "text-red-700"

    with ui.card().classes(f"w-full p-4 border {border} rounded-xl"):
        ui.label(f"{status} — {epub_path}").classes(
            f"text-base font-semibold {color}"
        )
        ui.label(f"Engine: {result.engine}").classes("text-sm text-slate-500")
        ui.label(f"Score: {result.score}").classes("text-sm text-slate-500")

        if result.issues:
            ui.separator()
            ui.label("Issues").classes("text-sm font-semibold text-slate-700")
            _issue_rows(result.issues)
        else:
            ui.label("No accessibility issues detected").classes(
                "text-sm text-green-600"
            )

        ui.label(
            "A review form has opened — confirm or adjust the measures "
            "to submit them to the database."
        ).classes("text-xs text-indigo-600 mt-2")


def _open_measure_dialog(
    result: QAResult,
    epub_path: str,
    job_type: str | None,
    job_id: int | None,
    measures_box: ui.element,
) -> None:
    """Popup form pre-filled with the Ace measures for reviewer confirmation."""
    error_count = sum(1 for i in result.issues if i.severity == "error")
    warning_count = sum(1 for i in result.issues if i.severity == "warning")
    info_count = sum(1 for i in result.issues if i.severity == "info")

    with ui.dialog() as dialog, ui.card().classes("p-6 gap-3 w-[560px] max-w-full"):
        ui.label("Confirm QA Measures").classes("text-xl font-bold text-slate-800")
        ui.label(f"{result.engine} — {epub_path}").classes(
            "text-sm text-slate-500 mb-1"
        )

        with ui.row().classes("gap-3 w-full"):
            score_input = ui.number(
                "Score", value=result.score, min=0, max=100,
            ).classes("flex-1")
            passed_switch = ui.switch("Passed", value=result.passed).classes(
                "flex-1 mt-2"
            )

        ui.label(
            f"Detected: {error_count} error(s), {warning_count} warning(s), "
            f"{info_count} info"
        ).classes("text-xs text-slate-500")

        if result.issues:
            with ui.scroll_area().classes(
                "w-full h-32 border border-slate-100 rounded-lg p-2"
            ):
                _issue_rows(result.issues)

        ui.separator().classes("my-1")

        reviewer_input = ui.input(
            "Reviewer name", placeholder="Who is confirming this result?",
        ).classes("w-full")
        notes_input = ui.textarea(
            "Reviewer notes",
            placeholder="Optional notes about this QA measure…",
        ).classes("w-full")

        if job_type and job_id:
            ui.label(f"Will be linked to {job_type} job #{job_id}").classes(
                "text-xs text-indigo-600"
            )

        with ui.row().classes("justify-end gap-3 mt-3"):
            ui.button("Cancel", on_click=dialog.close).props("flat").classes(
                "text-slate-500"
            )

            def _submit() -> None:
                Q.log_qa_measure(
                    engine=result.engine,
                    epub_path=epub_path,
                    passed=bool(passed_switch.value),
                    score=int(score_input.value or 0),
                    error_count=error_count,
                    warning_count=warning_count,
                    info_count=info_count,
                    issues=[
                        {
                            "severity": i.severity,
                            "code": i.code,
                            "message": i.message,
                            "location": i.location,
                        }
                        for i in result.issues
                    ],
                    job_type=job_type,
                    job_id=job_id,
                    reviewer=reviewer_input.value.strip() or None,
                    reviewer_notes=notes_input.value.strip(),
                    checked_at=result.checked_at,
                )
                dialog.close()
                notify_success("QA measure submitted to the database.")
                _render_measures_box(measures_box)

            ui.button("Submit to Database", on_click=_submit).classes(
                "bg-blue-600 text-white"
            )

    dialog.open()


def _render_measures_box(measures_box: ui.element) -> None:
    measures_box.clear()
    with measures_box:
        rows = Q.list_qa_measures(limit=20)
        if not rows:
            ui.label("No QA measures submitted yet.").classes(
                "text-slate-400 text-sm"
            )
            return

        with ui.card().classes(
            "w-full rounded-xl border border-slate-200 overflow-hidden"
        ):
            with ui.row().classes(
                "px-4 py-2 bg-slate-50 text-xs font-semibold text-slate-500 "
                "uppercase tracking-wider border-b"
            ):
                ui.label("Engine").classes("w-28")
                ui.label("EPUB").classes("flex-1")
                ui.label("Linked Job").classes("w-32")
                ui.label("Score").classes("w-16")
                ui.label("Result").classes("w-20")
                ui.label("Reviewer").classes("w-28")
                ui.label("Submitted").classes("w-36")

            for row in rows:
                ok = bool(row.get("passed"))
                with ui.row().classes(
                    "items-center px-4 py-2 border-b border-slate-50 "
                    "last:border-0 gap-2"
                ):
                    ui.label(row.get("engine", "—")).classes("w-28 text-sm")
                    ui.label(row.get("epub_path", "—")).classes(
                        "flex-1 text-xs font-mono text-slate-500 truncate"
                    )
                    if row.get("job_type") and row.get("job_id"):
                        ui.label(
                            f"{row['job_type']} #{row['job_id']}"
                        ).classes("w-32 text-xs font-mono text-indigo-600")
                    else:
                        ui.label("—").classes("w-32 text-xs text-slate-400")
                    ui.label(str(row.get("score", "—"))).classes(
                        "w-16 text-sm"
                    )
                    ui.badge("✓ PASS" if ok else "✗ FAIL").classes(
                        f"w-20 text-center text-xs rounded "
                        f"{'bg-green-100 text-green-700' if ok else 'bg-red-100 text-red-700'}"
                    )
                    ui.label(row.get("reviewer") or "—").classes(
                        "w-28 text-xs text-slate-500"
                    )
                    ui.label(str(row.get("submitted_at", ""))[:19]).classes(
                        "w-36 text-xs text-slate-400 font-mono"
                    )
