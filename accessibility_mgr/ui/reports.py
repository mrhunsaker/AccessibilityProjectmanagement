"""
Reports page — faceted filtering and export of jobs by student, school,
grade, material type, status, and date range.

New file (FIX-015).
"""

from __future__ import annotations

import csv
import io
from datetime import date

from nicegui import ui

from ..db import queries as Q
from .components import priority_badge, progress_bar, section_header

_TYPE_LABELS = {
    "braille":     "Braille",
    "lp_ebraille": "LP / eBraille / EPUB3",
    "tactile":     "Tactile Graphics",
    "print":       "3-D Print",
}

_STATUS_OPTIONS = [
    ("all",          "All Statuses"),
    ("not_started",  "Not Started"),
    ("in_progress",  "In Progress"),
    ("delivered",    "Delivered"),
]

_TYPE_OPTIONS = [
    ("",           "All Types"),
    ("braille",    "Braille"),
    ("lp_ebraille","LP / eBraille / EPUB3"),
    ("tactile",    "Tactile Graphics"),
    ("print",      "3-D Print"),
]


def reports_page(content_area: ui.element) -> None:
    """Render the Reports page."""
    content_area.clear()
    with content_area:
        section_header(
            "Reports",
            "Filter and export jobs by school, grade, material type, and status",
        )

        # ── Filter controls ───────────────────────────────────────────────────
        with ui.card().classes("w-full p-5 rounded-xl border border-slate-200 mb-4"):
            ui.label("Filters").classes(
                "text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3"
            )
            with ui.grid(columns=3).classes("gap-4 w-full"):
                school_inp = ui.input(
                    "School", placeholder="e.g. Legacy Jr. High"
                ).classes("w-full").props("outlined dense clearable")

                grade_inp = ui.input(
                    "Grade", placeholder="e.g. 7"
                ).classes("w-full").props("outlined dense clearable")

                type_sel = ui.select(
                    {v: l for v, l in _TYPE_OPTIONS},
                    value="",
                    label="Material Type",
                ).classes("w-full").props("outlined dense")

                status_sel = ui.select(
                    {v: l for v, l in _STATUS_OPTIONS},
                    value="all",
                    label="Status",
                ).classes("w-full").props("outlined dense")

                date_from_inp = ui.input(
                    "Created From (YYYY-MM-DD)", placeholder=str(date.today())
                ).classes("w-full").props("outlined dense clearable")

                date_to_inp = ui.input(
                    "Created To (YYYY-MM-DD)", placeholder=str(date.today())
                ).classes("w-full").props("outlined dense clearable")

            # Student selector
            students = Q.list_students()
            student_map = {"": "All Students"}
            for s in students:
                label = f"{s['last_name']}, {s['first_name']}"
                if s.get("school"):
                    label += f" — {s['school']}"
                student_map[str(s["id"])] = label

            student_sel = ui.select(
                student_map,
                value="",
                label="Student",
            ).classes("w-full mt-2").props("outlined dense")

            with ui.row().classes("gap-3 mt-4 items-center"):
                run_btn = ui.button("Run Report").classes(
                    "bg-blue-600 text-white rounded-lg px-4 py-2"
                )
                export_btn = ui.button("Export CSV").props("flat").classes(
                    "text-blue-600 border border-blue-300 rounded-lg px-4 py-2"
                )
                results_label = ui.label("").classes("text-sm text-slate-400 ml-2")

        # ── Results area ──────────────────────────────────────────────────────
        results_area = ui.column().classes("w-full gap-4")

        # Store last result for CSV export
        _last_result: dict = {}

        def _run_report() -> None:
            nonlocal _last_result
            results_area.clear()

            sid_str = student_sel.value
            sid = int(sid_str) if sid_str and sid_str.isdigit() else None
            status_val = status_sel.value if status_sel.value != "all" else None
            type_val = type_sel.value or None
            df = date_from_inp.value.strip() or None
            dt = date_to_inp.value.strip() or None

            result = Q.report_jobs(
                school=school_inp.value.strip() or None,
                grade=grade_inp.value.strip() or None,
                job_type=type_val,
                status=status_val,
                date_from=df,
                date_to=dt,
                student_id=sid,
            )
            _last_result = result

            total = result["total_jobs"]
            by_type = result["by_type"]

            results_label.set_text(
                f"{total} job(s) found"
                + (
                    " — " + ", ".join(f"{_TYPE_LABELS.get(k, k)}: {v}" for k, v in by_type.items() if v)
                    if total else ""
                )
            )

            if total == 0:
                with results_area:
                    with ui.card().classes(
                        "p-8 text-center border border-slate-200 rounded-xl w-full"
                    ):
                        ui.label("No jobs match the selected filters.").classes(
                            "text-slate-400"
                        )
                return

            # ── Summary cards ─────────────────────────────────────────────────
            with results_area:
                with ui.row().classes("gap-3 flex-wrap mb-2"):
                    for jtype, count in by_type.items():
                        if not count:
                            continue
                        color_map = {
                            "braille":     ("bg-indigo-50", "text-indigo-600", "border-indigo-200"),
                            "lp_ebraille": ("bg-green-50",  "text-green-600",  "border-green-200"),
                            "tactile":     ("bg-rose-50",   "text-rose-600",   "border-rose-200"),
                            "print":       ("bg-amber-50",  "text-amber-600",  "border-amber-200"),
                        }
                        bg, text, border = color_map.get(jtype, ("bg-slate-50", "text-slate-600", "border-slate-200"))
                        with ui.card().classes(f"p-4 {bg} border {border} rounded-xl shadow-sm"):
                            ui.label(str(count)).classes(f"text-3xl font-bold {text}")
                            ui.label(_TYPE_LABELS.get(jtype, jtype)).classes(
                                "text-slate-600 text-sm mt-1"
                            )

                # ── Jobs table ────────────────────────────────────────────────
                with ui.card().classes(
                    "w-full rounded-xl border border-slate-200 overflow-hidden"
                ):
                    with ui.row().classes(
                        "px-4 py-2 bg-slate-50 text-xs font-semibold text-slate-500 "
                        "uppercase tracking-wider border-b gap-2"
                    ):
                        ui.label("Title / Object").classes("flex-1")
                        ui.label("Type").classes("w-36")
                        ui.label("Student / Requester").classes("w-44")
                        ui.label("School").classes("w-36")
                        ui.label("Grade").classes("w-16 text-center")
                        ui.label("Priority").classes("w-20 text-center")
                        ui.label("Status").classes("w-24 text-center")
                        ui.label("Created").classes("w-24")

                    for job in result["jobs"]:
                        status = job.get("status", "not_started")
                        status_color = {
                            "delivered":   "bg-green-100 text-green-700",
                            "in_progress": "bg-blue-100 text-blue-700",
                            "not_started": "bg-slate-100 text-slate-500",
                        }.get(status, "bg-slate-100 text-slate-500")
                        status_label = status.replace("_", " ").title()

                        requester = ""
                        if job.get("last_name"):
                            requester = f"{job['last_name']}, {job['first_name']}"
                        elif job.get("requester"):
                            requester = job["requester"]

                        with ui.row().classes(
                            "items-center px-4 py-3 border-b border-slate-50 "
                            "last:border-0 hover:bg-slate-50 gap-2"
                        ):
                            ui.label(job.get("title") or "—").classes(
                                "flex-1 text-sm text-slate-700 truncate"
                            )
                            ui.badge(
                                _TYPE_LABELS.get(job.get("job_type", ""), "—")
                            ).classes(
                                "w-36 text-xs rounded px-1 "
                                + {
                                    "braille":     "bg-indigo-50 text-indigo-700",
                                    "lp_ebraille": "bg-green-50 text-green-700",
                                    "tactile":     "bg-rose-50 text-rose-700",
                                    "print":       "bg-amber-50 text-amber-700",
                                }.get(job.get("job_type", ""), "bg-slate-100 text-slate-600")
                            )
                            ui.label(requester or "—").classes(
                                "w-44 text-xs text-slate-600 truncate"
                            )
                            ui.label(job.get("school") or "—").classes(
                                "w-36 text-xs text-slate-500 truncate"
                            )
                            ui.label(job.get("grade") or "—").classes(
                                "w-16 text-xs text-center text-slate-500"
                            )
                            with ui.element("div").classes("w-20 flex justify-center"):
                                priority_badge(job.get("priority", "normal"))
                            ui.badge(status_label).classes(
                                f"w-24 text-center text-xs rounded {status_color}"
                            )
                            ui.label(str(job.get("created_at", ""))[:10]).classes(
                                "w-24 text-xs text-slate-400 font-mono"
                            )

        def _export_csv() -> None:
            if not _last_result:
                ui.notify("Run a report first.", type="warning", position="top-right")
                return

            jobs = _last_result.get("jobs", [])
            if not jobs:
                ui.notify("No results to export.", type="warning", position="top-right")
                return

            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "id", "title", "job_type", "requester",
                    "last_name", "first_name", "school", "grade",
                    "priority", "status", "created_at",
                ],
                extrasaction="ignore",
            )
            writer.writeheader()
            for job in jobs:
                writer.writerow(job)

            csv_bytes = output.getvalue().encode("utf-8")
            filename = f"accessibility_report_{date.today().isoformat()}.csv"
            ui.download(csv_bytes, filename)

        run_btn.on("click", lambda: _run_report())
        export_btn.on("click", lambda: _export_csv())
