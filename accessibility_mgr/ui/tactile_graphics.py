"""Tactile graphics jobs panel."""

from __future__ import annotations

from typing import Optional

from nicegui import ui

import db.queries as Q
from ui.components import confirm_dialog, notify_success, priority_badge, progress_bar, section_header, status_chip

_STEPS = ["designed", "produced", "qa_reviewed", "delivered"]
_STEP_LABELS = {
    "designed": "1. Designed",
    "produced": "2. Produced",
    "qa_reviewed": "3. QA Reviewed",
    "delivered": "4. Delivered",
}


def _job_dialog(on_save, existing: Optional[dict] = None) -> None:
    title = "Edit Tactile Graphics Job" if existing else "New Tactile Graphics Job"
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[520px] max-w-full"):
        ui.label(title).classes("text-xl font-bold text-slate-800")

        title_inp = ui.input(
            "Title*", value=existing.get("title", "") if existing else ""
        ).classes("w-full")

        tactile_types = Q.list_material_categories("tactile_type")
        type_labels = [item["label"] for item in tactile_types]
        type_values = [item["value"] for item in tactile_types]
        current_type = existing.get("tactile_type", "thermoform_swell") if existing else "thermoform_swell"
        current_label = type_labels[type_values.index(current_type)] if current_type in type_values else (type_labels[0] if type_labels else "Thermoform / SWELL")
        type_sel = ui.select(type_labels, label="Production Method*", value=current_label).classes("w-full")

        with ui.row().classes("gap-4 w-full"):
            req_input = ui.input(
                "Requester", value=existing.get("requester", "") if existing else ""
            ).classes("flex-1")
            req_date_input = ui.input(
                "Request Date (YYYY-MM-DD)",
                value=existing.get("request_date", "") if existing else "",
            ).classes("flex-1")

        with ui.row().classes("gap-4 w-full"):
            due_input = ui.input(
                "Due Date (YYYY-MM-DD)",
                value=existing.get("due_date", "") if existing else "",
            ).classes("flex-1")
            priorities = Q.list_material_categories("priority")
            pri_labels = [item["label"] for item in priorities]
            pri_values = [item["value"] for item in priorities]
            current_pri = existing.get("priority", "normal") if existing else "normal"
            current_pri_label = pri_labels[pri_values.index(current_pri)] if current_pri in pri_values else (pri_labels[0] if pri_labels else "Normal")
            pri_sel = ui.select(pri_labels, label="Priority", value=current_pri_label).classes("flex-1")

        notes_input = ui.textarea(
            "Notes", value=existing.get("notes", "") if existing else ""
        ).classes("w-full").props("rows=3")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _save() -> None:
                if not title_inp.value.strip():
                    return
                try:
                    tactile_type = type_values[type_labels.index(type_sel.value)]
                except (ValueError, IndexError):
                    tactile_type = "thermoform_swell"
                try:
                    priority = pri_values[pri_labels.index(pri_sel.value)]
                except (ValueError, IndexError):
                    priority = "normal"
                on_save(
                    {
                        "title": title_inp.value.strip(),
                        "tactile_type": tactile_type,
                        "requester": req_input.value.strip(),
                        "request_date": req_date_input.value.strip() or None,
                        "due_date": due_input.value.strip() or None,
                        "priority": priority,
                        "notes": notes_input.value.strip(),
                    }
                )
                dlg.close()

            ui.button("Save", on_click=_save).classes("bg-rose-600 text-white")

    dlg.open()


def _job_detail(job: dict, content_area: ui.element, refresh_cb) -> None:
    job_id = job["id"]

    def _refresh() -> None:
        updated = Q.get_tactile_job(job_id)
        if updated:
            _render(updated)

    def _render(current: dict) -> None:
        content_area.clear()
        with content_area:
            with ui.row().classes("items-center gap-3 mb-1"):
                ui.button("← Back", on_click=refresh_cb).props("flat").classes(
                    "text-blue-600 text-sm"
                )
                ui.label(current["title"]).classes("text-2xl font-bold text-slate-800 flex-1")
                priority_badge(current.get("priority", "normal"))

                def _edit() -> None:
                    def _do(data: dict) -> None:
                        Q.update_tactile_job(job_id, **data)
                        notify_success("Job updated")
                        _refresh()

                    _job_dialog(_do, existing=current)

                ui.button("Edit", on_click=_edit).props("flat").classes("text-blue-600")

            with ui.row().classes("gap-6 text-sm text-slate-500 mb-6 flex-wrap"):
                ui.label(f"Method: {current.get('tactile_type', '').replace('_', ' ').title()}")
                ui.label(f"Requester: {current.get('requester') or '—'}")
                ui.label(f"Requested: {current.get('request_date') or '—'}")
                ui.label(f"Due: {current.get('due_date') or '—'}")
                ui.label(f"Created: {str(current.get('created_at', ''))[:10]}")

            with ui.card().classes("flex-1 min-w-72 p-5 rounded-xl border border-slate-200"):
                ui.label("Workflow Steps").classes("font-semibold text-slate-700 mb-3")
                done = sum(current.get(step, 0) for step in _STEPS)
                progress_bar(done, len(_STEPS))
                ui.element("div").classes("h-3")
                for step in _STEPS:
                    is_done = bool(current.get(step, 0))
                    with ui.row().classes(
                        "items-center gap-3 py-2 border-b border-slate-50 last:border-0"
                    ):
                        ui.label(_STEP_LABELS[step]).classes("flex-1 text-sm font-medium text-slate-700")
                        if is_done:
                            def _revert(s: str = step) -> None:
                                Q.revert_step("tactile", job_id, s)
                                notify_success(f"Reverted: {s}")
                                _refresh()

                            ui.badge("✓ Done").classes(
                                "bg-green-100 text-green-700 text-xs rounded px-2 cursor-pointer"
                            ).on("click", _revert)
                        else:
                            def _complete(s: str = step) -> None:
                                Q.complete_step("tactile", job_id, s)
                                notify_success(f"Completed: {s}")
                                _refresh()

                            ui.button("Mark Done", on_click=_complete).props("flat dense").classes(
                                "text-blue-600 text-xs"
                            )

            if current.get("notes"):
                with ui.card().classes("mt-4 p-4 rounded-xl border border-slate-200 bg-rose-50"):
                    ui.label("Notes").classes("text-sm font-semibold text-rose-800 mb-1")
                    ui.label(current["notes"]).classes("text-sm text-rose-700")

    _render(job)


def tactile_graphics_page(content_area: ui.element) -> None:
    content_area.clear()
    with content_area:
        with ui.row().classes("items-center mb-4"):
            section_header(
                "Tactile Graphics",
                "Track thermoform, hand-tooled, and embossed figure production",
            )
            ui.element("div").classes("flex-1")

            def _new() -> None:
                def _do(data: dict) -> None:
                    Q.add_tactile_job(**data)
                    notify_success("Job created")
                    tactile_graphics_page(content_area)

                _job_dialog(_do)

            ui.button("+ New Job", on_click=_new).classes(
                "bg-rose-600 text-white rounded-lg px-4 py-2"
            )

        jobs = Q.list_tactile_jobs()
        if not jobs:
            with ui.card().classes("p-10 text-center border border-slate-200 rounded-xl w-full"):
                ui.label("No tactile graphics jobs yet.").classes("text-slate-400 text-lg")
            return

        for job in jobs:
            done = sum(job.get(step, 0) for step in _STEPS)
            with ui.card().classes(
                "p-4 rounded-xl border border-slate-200 hover:border-rose-300 hover:shadow-md transition-all mb-3"
            ):
                with ui.row().classes("items-start gap-3"):
                    with ui.column().classes("flex-1 gap-1 min-w-0"):
                        with ui.row().classes("items-center gap-2"):
                            ui.label(job["title"]).classes(
                                "font-semibold text-slate-800 text-base truncate"
                            )
                            priority_badge(job.get("priority", "normal"))
                            ui.badge(job.get("tactile_type", "").replace("_", " ").title()).classes(
                                "text-xs bg-rose-50 text-rose-700 rounded px-2"
                            )
                        with ui.row().classes("gap-4 text-xs text-slate-500 flex-wrap"):
                            if job.get("requester"):
                                ui.label(f"→ {job['requester']}")
                            if job.get("due_date"):
                                ui.label(f"Due: {job['due_date']}")
                        progress_bar(done, len(_STEPS))
                        with ui.row().classes("gap-1 flex-wrap mt-1"):
                            for step in _STEPS:
                                status_chip(_STEP_LABELS[step].split('. ')[1], bool(job.get(step, 0)))

                    with ui.column().classes("gap-1 shrink-0"):
                        def _view(j: dict = job) -> None:
                            _job_detail(j, content_area, lambda: tactile_graphics_page(content_area))

                        ui.button("View", on_click=_view).props("flat dense").classes(
                            "text-rose-600 text-sm"
                        )

                        def _del(j: dict = job) -> None:
                            def _do() -> None:
                                Q.delete_tactile_job(j["id"])
                                notify_success("Deleted")
                                tactile_graphics_page(content_area)

                            confirm_dialog(f"Delete '{j['title']}'?", _do)

                        ui.button("Delete", on_click=_del).props("flat dense").classes(
                            "text-red-400 text-sm"
                        )
