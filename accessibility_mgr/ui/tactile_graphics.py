"""Tactile graphics jobs panel."""

from __future__ import annotations

from typing import Optional

from nicegui import ui

from ..db import queries as Q
from .metadata_options import (
    get_dublin_core_examples,
    get_dublin_core_keys,
    get_non_dc_allowed_keys,
    get_option_groups,
)
from .components import confirm_dialog, notify_success, priority_badge, progress_bar, section_header, status_chip

_STEPS = ["designed", "produced", "qa_reviewed", "delivered"]
_STEP_LABELS = {
    "designed": "1. Designed",
    "produced": "2. Produced",
    "qa_reviewed": "3. QA Reviewed",
    "delivered": "4. Delivered",
}


def _job_dialog(on_save, existing: Optional[dict] = None) -> None:
    """ job dialog.
    
    Parameters
    ----------
    on_save : Any
        on_save parameter.
    
    existing : Any
        existing parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
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
                """ save.
                
                Returns
                -------
                Any
                    Function result.
                
                """
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
    """ job detail.
    
    Parameters
    ----------
    job : Any
        job parameter.
    
    content_area : Any
        content_area parameter.
    
    refresh_cb : Any
        refresh_cb parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    job_id = job["id"]

    def _refresh() -> None:
        """ refresh.
        
        Returns
        -------
        Any
            Function result.
        
        """
        updated = Q.get_tactile_job(job_id)
        if updated:
            _render(updated)

    def _render(current: dict) -> None:
        """ render.
        
        Parameters
        ----------
        current : Any
            current parameter.
        
        Returns
        -------
        Any
            Function result.
        
        """
        content_area.clear()
        with content_area:
            with ui.row().classes("items-center gap-3 mb-1"):
                ui.button("← Back", on_click=refresh_cb).props("flat").classes(
                    "text-blue-600 text-sm"
                )
                ui.label(current["title"]).classes("text-2xl font-bold text-slate-800 flex-1")
                priority_badge(current.get("priority", "normal"))

                def _edit() -> None:
                    """ edit.
                    
                    Returns
                    -------
                    Any
                        Function result.
                    
                    """
                    def _do(data: dict) -> None:
                        """ do.
                        
                        Parameters
                        ----------
                        data : Any
                            data parameter.
                        
                        Returns
                        -------
                        Any
                            Function result.
                        
                        """
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
                                """ revert.
                                
                                Parameters
                                ----------
                                s : Any
                                    s parameter.
                                
                                Returns
                                -------
                                Any
                                    Function result.
                                
                                """
                                Q.revert_step("tactile", job_id, s)
                                notify_success(f"Reverted: {s}")
                                _refresh()

                            ui.badge("✓ Done").classes(
                                "bg-green-100 text-green-700 text-xs rounded px-2 cursor-pointer"
                            ).on("click", _revert)
                        else:
                            def _complete(s: str = step) -> None:
                                """ complete.
                                
                                Parameters
                                ----------
                                s : Any
                                    s parameter.
                                
                                Returns
                                -------
                                Any
                                    Function result.
                                
                                """
                                Q.complete_step("tactile", job_id, s)
                                notify_success(f"Completed: {s}")
                                _refresh()

                            ui.button("Mark Done", on_click=_complete).props("flat dense").classes(
                                "text-blue-600 text-xs"
                            )

            def _metadata_dialog() -> None:
                """ metadata dialog.
                
                Returns
                -------
                Any
                    Function result.
                
                """
                existing_meta = Q.list_job_metadata("tactile", job_id)
                option_groups = get_option_groups()
                dc_keys = get_dublin_core_keys()
                dc_examples = get_dublin_core_examples()
                non_dc_keys = get_non_dc_allowed_keys()

                with ui.dialog() as dlg, ui.card().classes(
                    "p-6 gap-4 w-[600px] max-w-full max-h-[90vh] overflow-y-auto"
                ):
                    ui.label("Descriptive Metadata").classes("text-xl font-bold text-slate-800")
                    ui.label(
                        "Dublin Core plus controlled eBraille and METS/PREMIS fields."
                    ).classes("text-slate-500 text-sm")

                    def _show_options() -> None:
                        """ show options.
                        
                        Returns
                        -------
                        Any
                            Function result.
                        
                        """
                        with ui.dialog() as od, ui.card().classes(
                            "p-5 gap-3 w-[720px] max-w-full max-h-[85vh] overflow-y-auto"
                        ):
                            ui.label("Potential Metadata Options").classes("text-lg font-bold text-slate-800")
                            ui.label(
                                "Use Admin Settings -> Metadata Options to add or remove allowed keys."
                            ).classes("text-xs text-slate-500")

                            for group, keys in option_groups.items():
                                ui.separator()
                                ui.label(group).classes(
                                    "text-sm font-semibold text-slate-600 uppercase tracking-wider"
                                )
                                with ui.row().classes("gap-2 flex-wrap"):
                                    for key in keys:
                                        ui.badge(key).classes(
                                            "bg-slate-100 text-slate-700 text-xs rounded px-2 py-1"
                                        )

                            with ui.row().classes("justify-end mt-2"):
                                ui.button("Close", on_click=od.close).classes("bg-slate-700 text-white")

                        od.open()

                    ui.button("Potential Options", on_click=_show_options).props("flat dense").classes(
                        "text-indigo-600 text-sm self-start"
                    )

                    meta_rows: dict[str, ui.input] = {}
                    with ui.grid(columns=2).classes("gap-2 w-full"):
                        for key in dc_keys:
                            with ui.column().classes("gap-0"):
                                inp = ui.input(key, value=existing_meta.get(key, "")).classes(
                                    "w-full font-mono text-sm"
                                )
                                ui.label(dc_examples.get(key, "")).classes(
                                    "text-[11px] text-slate-400"
                                )
                                meta_rows[key] = inp

                    ui.separator()
                    ui.label("Additional Allowed Fields").classes("text-sm font-medium text-slate-600")
                    ui.label(
                        "Choose keys from the approved eBraille and METS/PREMIS list."
                    ).classes("text-xs text-slate-400")

                    extra_rows: list[dict[str, ui.element]] = []
                    extra_box = ui.column().classes("w-full gap-2")

                    def _add_extra_row(initial_key: str = "", initial_val: str = "") -> None:
                        """ add extra row.
                        
                        Parameters
                        ----------
                        initial_key : Any
                            initial_key parameter.
                        
                        initial_val : Any
                            initial_val parameter.
                        
                        Returns
                        -------
                        Any
                            Function result.
                        
                        """
                        with extra_box:
                            with ui.row().classes("gap-2 w-full items-center") as row:
                                key_sel = ui.select(
                                    non_dc_keys,
                                    label="Key",
                                    value=initial_key if initial_key in non_dc_keys else None,
                                ).classes("w-64")
                                val_inp = ui.input("Value", value=initial_val).classes("flex-1")
                                ref = {"row": row, "key": key_sel, "value": val_inp}
                                extra_rows.append(ref)

                                def _remove(r: dict[str, ui.element] = ref) -> None:
                                    """ remove.
                                    
                                    Parameters
                                    ----------
                                    r : Any
                                        r parameter.
                                    
                                    Returns
                                    -------
                                    Any
                                        Function result.
                                    
                                    """
                                    r["row"].delete()
                                    if r in extra_rows:
                                        extra_rows.remove(r)

                                ui.button("✕", on_click=_remove).props("flat dense").classes("text-red-400")

                    ui.button("+ Add Field", on_click=lambda: _add_extra_row()).props("flat dense").classes(
                        "text-indigo-600 text-sm self-start"
                    )

                    for key, value in existing_meta.items():
                        if key not in dc_keys and key in non_dc_keys:
                            _add_extra_row(initial_key=key, initial_val=value)

                    with ui.row().classes("justify-end gap-3 mt-4"):
                        ui.button("Close", on_click=dlg.close).props("flat").classes("text-slate-500")

                        def _save_all() -> None:
                            """ save all.
                            
                            Returns
                            -------
                            Any
                                Function result.
                            
                            """
                            for key, inp in meta_rows.items():
                                v = inp.value.strip()
                                if v:
                                    Q.set_job_metadata("tactile", job_id, key, v)
                                else:
                                    Q.delete_job_metadata("tactile", job_id, key)

                            for key in non_dc_keys:
                                Q.delete_job_metadata("tactile", job_id, key)
                            for row in extra_rows:
                                k = (row["key"].value or "").strip()
                                v = (row["value"].value or "").strip()
                                if k and v and k in non_dc_keys:
                                    Q.set_job_metadata("tactile", job_id, k, v)

                            notify_success("Metadata saved")
                            dlg.close()
                            _refresh()

                        ui.button("Save All", on_click=_save_all).classes("bg-blue-600 text-white")

                dlg.open()

            with ui.card().classes("mt-4 p-5 rounded-xl border border-slate-200"):
                with ui.row().classes("items-center mb-3"):
                    ui.label("Descriptive Metadata").classes("font-semibold text-slate-700 flex-1")
                    ui.button("Edit", on_click=_metadata_dialog).props("flat dense").classes(
                        "text-blue-600 text-sm"
                    )

                meta = Q.list_job_metadata("tactile", job_id)
                if not meta:
                    ui.label("No metadata yet.").classes("text-slate-400 text-sm")
                else:
                    for k, v in meta.items():
                        with ui.row().classes(
                            "gap-2 py-1 border-b border-slate-50 last:border-0"
                        ):
                            ui.label(k).classes(
                                "text-xs text-slate-400 font-mono w-36 shrink-0"
                            )
                            ui.label(v).classes("text-xs text-slate-700 break-all")

            if current.get("notes"):
                with ui.card().classes("mt-4 p-4 rounded-xl border border-slate-200 bg-rose-50"):
                    ui.label("Notes").classes("text-sm font-semibold text-rose-800 mb-1")
                    ui.label(current["notes"]).classes("text-sm text-rose-700")

    _render(job)


def tactile_graphics_page(content_area: ui.element) -> None:
    """Tactile graphics page.
    
    Parameters
    ----------
    content_area : Any
        content_area parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    content_area.clear()
    with content_area:
        with ui.row().classes("items-center mb-4"):
            section_header(
                "Tactile Graphics",
                "Track thermoform, hand-tooled, and embossed figure production",
            )
            ui.element("div").classes("flex-1")

            def _new() -> None:
                """ new.
                
                Returns
                -------
                Any
                    Function result.
                
                """
                def _do(data: dict) -> None:
                    """ do.
                    
                    Parameters
                    ----------
                    data : Any
                        data parameter.
                    
                    Returns
                    -------
                    Any
                        Function result.
                    
                    """
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
                            """ view.
                            
                            Parameters
                            ----------
                            j : Any
                                j parameter.
                            
                            Returns
                            -------
                            Any
                                Function result.
                            
                            """
                            _job_detail(j, content_area, lambda: tactile_graphics_page(content_area))

                        ui.button("View", on_click=_view).props("flat dense").classes(
                            "text-rose-600 text-sm"
                        )

                        def _del(j: dict = job) -> None:
                            """ del.
                            
                            Parameters
                            ----------
                            j : Any
                                j parameter.
                            
                            Returns
                            -------
                            Any
                                Function result.
                            
                            """
                            def _do() -> None:
                                """ do.
                                
                                Returns
                                -------
                                Any
                                    Function result.
                                
                                """
                                Q.delete_tactile_job(j["id"])
                                notify_success("Deleted")
                                tactile_graphics_page(content_area)

                            confirm_dialog(f"Delete '{j['title']}'?", _do)

                        ui.button("Delete", on_click=_del).props("flat dense").classes(
                            "text-red-400 text-sm"
                        )
