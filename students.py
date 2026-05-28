"""
Students page — manage student records and view all jobs for a student.

New file (FIX-010): provides a student entity so jobs can be reliably linked
to a person rather than relying on free-text requester strings.
"""

from __future__ import annotations

from typing import Optional

from nicegui import ui

from ..db import queries as Q
from .components import (
    confirm_dialog,
    notify_error,
    notify_success,
    priority_badge,
    progress_bar,
    section_header,
    status_chip,
)

_BRAILLE_STEPS   = ["digitized", "formatted", "brailled", "proofread", "delivered"]
_LP_STEPS        = ["digitized", "formatted", "converted", "proofread", "delivered"]
_TACTILE_STEPS   = ["designed", "produced", "qa_reviewed", "delivered"]
_PRINT_STEPS     = ["designed", "sliced", "printed", "inspected", "delivered"]

_TYPE_COLORS = {
    "braille":     "bg-indigo-50 text-indigo-700",
    "lp_ebraille": "bg-green-50 text-green-700",
    "tactile":     "bg-rose-50 text-rose-700",
    "print":       "bg-amber-50 text-amber-700",
}


# ── Student form dialog ───────────────────────────────────────────────────────

def _student_dialog(on_save, existing: Optional[dict] = None) -> None:
    is_edit = existing is not None
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[480px] max-w-full"):
        ui.label("Edit Student" if is_edit else "Add Student").classes(
            "text-xl font-bold text-slate-800"
        )

        with ui.row().classes("gap-4 w-full"):
            last_inp = ui.input(
                "Last Name*",
                value=existing.get("last_name", "") if is_edit else "",
            ).classes("flex-1")
            first_inp = ui.input(
                "First Name*",
                value=existing.get("first_name", "") if is_edit else "",
            ).classes("flex-1")

        school_inp = ui.input(
            "School",
            value=existing.get("school", "") if is_edit else "",
        ).classes("w-full")

        grade_inp = ui.input(
            "Grade",
            value=existing.get("grade", "") if is_edit else "",
            placeholder="e.g. 7, K, 10",
        ).classes("w-full")

        formats_inp = ui.input(
            "Preferred Formats",
            value=existing.get("preferred_formats", "") if is_edit else "",
            placeholder="e.g. Braille (UEB), Large Print 18pt, EPUB3",
        ).classes("w-full")

        notes_inp = ui.textarea(
            "Notes",
            value=existing.get("notes", "") if is_edit else "",
        ).classes("w-full").props("rows=2")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _save() -> None:
                if not last_inp.value.strip() or not first_inp.value.strip():
                    notify_error("First and last name are required")
                    return
                on_save({
                    "last_name":         last_inp.value.strip(),
                    "first_name":        first_inp.value.strip(),
                    "school":            school_inp.value.strip(),
                    "grade":             grade_inp.value.strip(),
                    "preferred_formats": formats_inp.value.strip(),
                    "notes":             notes_inp.value.strip(),
                })
                dlg.close()

            ui.button("Save", on_click=_save).classes("bg-blue-600 text-white")

    dlg.open()


# ── Student detail view ───────────────────────────────────────────────────────

def _student_detail(student: dict, content_area: ui.element, refresh_cb) -> None:
    sid = student["id"]

    def _refresh() -> None:
        updated = Q.get_student(sid)
        if updated:
            _render(updated)

    def _render(s: dict) -> None:
        content_area.clear()
        with content_area:
            with ui.row().classes("items-center gap-3 mb-2"):
                ui.button("← Back", on_click=refresh_cb).props("flat").classes(
                    "text-blue-600 text-sm"
                )
                ui.label(
                    f"{s['last_name']}, {s['first_name']}"
                ).classes("text-2xl font-bold text-slate-800 flex-1")
                if not s.get("active", 1):
                    ui.badge("Inactive").classes("bg-slate-200 text-slate-500 text-xs rounded px-2")

                def _edit() -> None:
                    def _do(data: dict) -> None:
                        Q.update_student(sid, **data)
                        notify_success("Student updated")
                        _refresh()
                    _student_dialog(_do, existing=s)

                ui.button("Edit", on_click=_edit).props("flat").classes("text-blue-600")

                def _deactivate() -> None:
                    def _do() -> None:
                        Q.delete_student(sid)
                        notify_success("Student deactivated")
                        refresh_cb()
                    confirm_dialog(
                        f"Deactivate {s['first_name']} {s['last_name']}? "
                        "Their job history will be preserved.",
                        _do, "Deactivate Student",
                    )

                ui.button("Deactivate", on_click=_deactivate).props("flat").classes(
                    "text-red-400 text-sm"
                )

            with ui.row().classes("gap-6 text-sm text-slate-500 mb-6 flex-wrap"):
                ui.label(f"School: {s.get('school') or '—'}")
                ui.label(f"Grade: {s.get('grade') or '—'}")
                if s.get("preferred_formats"):
                    ui.label(f"Preferred formats: {s['preferred_formats']}")
                if s.get("notes"):
                    ui.label(f"Notes: {s['notes']}")

            # ── All jobs for this student ──────────────────────────────────────
            jobs = Q.list_jobs_for_student(sid)

            type_labels = {
                "braille":     "Braille",
                "lp_ebraille": "Large Print / eBraille / EPUB3",
                "tactile":     "Tactile Graphics",
                "print":       "3-D Print",
            }
            type_steps = {
                "braille":     _BRAILLE_STEPS,
                "lp_ebraille": _LP_STEPS,
                "tactile":     _TACTILE_STEPS,
                "print":       _PRINT_STEPS,
            }
            total = sum(len(v) for v in jobs.values())

            if total == 0:
                with ui.card().classes(
                    "p-8 text-center border border-slate-200 rounded-xl w-full"
                ):
                    ui.label("No jobs linked to this student yet.").classes(
                        "text-slate-400"
                    )
                return

            for jtype, jlist in jobs.items():
                if not jlist:
                    continue

                ui.label(type_labels.get(jtype, jtype)).classes(
                    "text-xs font-semibold text-slate-500 uppercase tracking-wider mt-6 mb-2"
                )

                steps = type_steps.get(jtype, [])
                color = _TYPE_COLORS.get(jtype, "bg-slate-50 text-slate-700")

                with ui.element("div").classes("grid gap-2 w-full"):
                    for job in jlist:
                        done = sum(job.get(st, 0) for st in steps)
                        title = job.get("title") or job.get("object_name") or "Untitled"
                        with ui.card().classes(
                            "p-4 rounded-xl border border-slate-200"
                        ):
                            with ui.row().classes("items-start gap-3"):
                                with ui.column().classes("flex-1 gap-1 min-w-0"):
                                    with ui.row().classes("items-center gap-2"):
                                        ui.label(title).classes(
                                            "font-semibold text-slate-800 truncate"
                                        )
                                        priority_badge(job.get("priority", "normal"))
                                        if job.get("delivery_date"):
                                            ui.badge("✓ Delivered").classes(
                                                "text-xs bg-green-100 text-green-700 rounded px-2"
                                            )
                                    with ui.row().classes("gap-3 text-xs text-slate-400 flex-wrap"):
                                        jt_display = job.get("job_type") or jtype
                                        ui.label(jt_display.replace("_", " ").title())
                                        if job.get("due_date"):
                                            ui.label(f"Due: {job['due_date']}")
                                        ui.label(
                                            str(job.get("created_at", ""))[:10]
                                        )
                                    if steps:
                                        progress_bar(done, len(steps))

    _render(student)


# ── Main list view ────────────────────────────────────────────────────────────

def students_page(content_area: ui.element) -> None:
    """Render the Students page."""
    content_area.clear()
    with content_area:
        with ui.row().classes("items-center mb-4"):
            section_header(
                "Students",
                "Student records and cross-job production history",
            )
            ui.element("div").classes("flex-1")

            def _new() -> None:
                def _do(data: dict) -> None:
                    Q.add_student(**data)
                    notify_success("Student added")
                    students_page(content_area)
                _student_dialog(_do)

            ui.button("+ Add Student", on_click=_new).classes(
                "bg-blue-600 text-white rounded-lg px-4 py-2"
            )

        # Filter bar
        with ui.row().classes("gap-3 mb-4 flex-wrap"):
            search_inp = ui.input(
                placeholder="Search name or school…"
            ).classes("w-64").props("outlined dense clearable")
            show_inactive = ui.checkbox("Show inactive", value=False)

        students = Q.list_students(active_only=True)
        all_students = Q.list_students(active_only=False)

        grid = ui.element("div").classes("grid gap-3 w-full")

        def _render_list() -> None:
            grid.clear()
            q = (search_inp.value or "").lower()
            pool = all_students if show_inactive.value else students
            filtered = [
                s for s in pool
                if q in s["last_name"].lower()
                or q in s["first_name"].lower()
                or q in (s.get("school") or "").lower()
            ] if q else pool

            with grid:
                if not filtered:
                    ui.label("No students found.").classes(
                        "text-slate-400 text-center py-8 col-span-full"
                    )
                    return

                for student in filtered:
                    # Count linked jobs
                    job_counts = Q.list_jobs_for_student(student["id"])
                    total_jobs = sum(len(v) for v in job_counts.values())
                    active = bool(student.get("active", 1))

                    with ui.card().classes(
                        f"p-4 rounded-xl border {'border-slate-200' if active else 'border-slate-100 opacity-60'} "
                        "hover:border-blue-300 hover:shadow-sm transition-all"
                    ):
                        with ui.row().classes("items-center gap-3"):
                            with ui.column().classes("flex-1 gap-0 min-w-0"):
                                ui.label(
                                    f"{student['last_name']}, {student['first_name']}"
                                ).classes("font-semibold text-slate-800 truncate")
                                with ui.row().classes(
                                    "gap-3 text-xs text-slate-400 flex-wrap"
                                ):
                                    if student.get("school"):
                                        ui.label(student["school"])
                                    if student.get("grade"):
                                        ui.label(f"Grade {student['grade']}")
                                    ui.label(f"{total_jobs} job(s)")
                                    if student.get("preferred_formats"):
                                        ui.label(student["preferred_formats"]).classes(
                                            "italic"
                                        )

                            def _view(s: dict = student) -> None:
                                _student_detail(
                                    s, content_area,
                                    lambda: students_page(content_area),
                                )

                            ui.button("View", on_click=_view).props("flat dense").classes(
                                "text-blue-600 text-sm"
                            )

        search_inp.on("update:model-value", lambda _: _render_list())
        show_inactive.on("update:model-value", lambda _: _render_list())
        _render_list()
