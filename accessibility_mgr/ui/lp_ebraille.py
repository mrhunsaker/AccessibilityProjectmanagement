"""LP / eBraille / EPUB3-DAISY jobs panel — mirrors braille_jobs structure."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from nicegui import ui

from ..db import queries as Q
from .metadata_options import (
    get_dublin_core_examples,
    get_dublin_core_keys,
    get_non_dc_allowed_keys,
    get_option_groups,
)
from .components import (
    OUTCOME_COLORS,
    confirm_dialog,
    file_use_badge,
    notify_error,
    notify_success,
    priority_badge,
    progress_bar,
    section_header,
    status_chip,
)

_STEPS = ["digitized", "formatted", "converted", "proofread", "delivered"]
_STEP_LABELS = {
    "digitized": "1. Digitized",
    "formatted": "2. Formatted",
    "converted": "3. eBraille / LP",
    "proofread": "4. Proofread",
    "delivered": "5. Delivered",
}
_LP_FORMATS = [
    "PDF", "DOCX", "ODT", "EPUB", "EPUB3", "DAISY", "HTML", "TXT", "BRF", "EBRF", "Other",
]
_FILE_USES = ["ORIGINAL", "DERIVATIVE", "INTERMEDIATE", "SOURCE", "REFERENCE"]


def _job_dialog(
    on_save,
    existing: Optional[dict] = None,
    forced_job_type: str | None = None,
    title_override: str | None = None,
) -> None:
    """ job dialog.
    
    Parameters
    ----------
    on_save : Any
        on_save parameter.
    
    existing : Any
        existing parameter.
    
    forced_job_type : Any
        forced_job_type parameter.
    
    title_override : Any
        title_override parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    title = title_override or ("Edit Large Print / eBraille Job" if existing else "New Large Print / eBraille Job")
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[520px] max-w-full"):
        ui.label(title).classes("text-xl font-bold text-slate-800")

        t_input = ui.input(
            "Title*", value=existing.get("title", "") if existing else ""
        ).classes("w-full")

        types = [r["label"] for r in Q.list_material_categories("lp_type")]
        type_vals = [r["value"] for r in Q.list_material_categories("lp_type")]
        cur_type = forced_job_type or (existing.get("job_type", "large_print") if existing else "large_print")
        try:
            cur_label = types[type_vals.index(cur_type)]
        except ValueError:
            cur_label = types[0] if types else "Large Print"
        if forced_job_type:
            ui.input("Job Type", value=cur_label).props("readonly").classes("w-full")
            jt_select = None
        else:
            jt_select = ui.select(types, label="Job Type*", value=cur_label).classes("w-full")

        with ui.row().classes("gap-4 w-full"):
            req_input = ui.input(
                "Requester", value=existing.get("requester", "") if existing else ""
            ).classes("flex-1")
            rdate_input = ui.input(
                "Request Date (YYYY-MM-DD)",
                value=existing.get("request_date", "") if existing else "",
            ).classes("flex-1")

        with ui.row().classes("gap-4 w-full"):
            due_input = ui.input(
                "Due Date (YYYY-MM-DD)",
                value=existing.get("due_date", "") if existing else "",
            ).classes("flex-1")
            pris = [r["label"] for r in Q.list_material_categories("priority")]
            pri_vals = [r["value"] for r in Q.list_material_categories("priority")]
            cur_pri = existing.get("priority", "normal") if existing else "normal"
            try:
                cur_pri_label = pris[pri_vals.index(cur_pri)]
            except ValueError:
                cur_pri_label = "Normal"
            pri_select = ui.select(pris, label="Priority", value=cur_pri_label).classes(
                "flex-1"
            )

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
                if not t_input.value.strip():
                    notify_error("Title is required")
                    return
                if forced_job_type:
                    jt_val = forced_job_type
                else:
                    try:
                        jt_val = type_vals[types.index(jt_select.value)]
                    except (ValueError, IndexError):
                        jt_val = "large_print"
                try:
                    pi_val = pri_vals[pris.index(pri_select.value)]
                except (ValueError, IndexError):
                    pi_val = "normal"
                on_save({
                    "title":        t_input.value.strip(),
                    "job_type":     jt_val,
                    "requester":    req_input.value.strip(),
                    "request_date": rdate_input.value.strip() or None,
                    "due_date":     due_input.value.strip() or None,
                    "priority":     pi_val,
                    "notes":        notes_input.value.strip(),
                })
                dlg.close()

            ui.button("Save", on_click=_save).classes("bg-blue-600 text-white")

    dlg.open()


def _ingest_dialog(job_id: int, on_done) -> None:
    """ ingest dialog.
    
    Parameters
    ----------
    job_id : Any
        job_id parameter.
    
    on_done : Any
        on_done parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[560px] max-w-full"):
        ui.label("Attach File to Job").classes("text-xl font-bold text-slate-800")
        path_input = ui.input("File Path*").classes("w-full")
        step_opts = ["(job level)"] + [_STEP_LABELS[s] for s in _STEPS]
        step_select = ui.select(
            step_opts, label="Workflow Step", value="(job level)"
        ).classes("w-full")
        use_select = ui.select(_FILE_USES, label="File Use*", value="ORIGINAL").classes("w-full")
        fmt_select = ui.select(_LP_FORMATS, label="Format", value="PDF").classes("w-full")
        ver_input = ui.input("Format Version").classes("w-full")

        ui.label("Tools & Processes").classes(
            "text-xs font-semibold text-slate-500 uppercase tracking-wider"
        )
        ui.label(
            'Record tool(s) and process(es), e.g. tool: "ace by daisy", process: "EPUB validation".'
        ).classes("text-xs text-slate-400")

        tool_rows: list[dict] = []
        proc_rows: list[dict] = []
        tool_box = ui.column().classes("w-full gap-1")
        proc_box = ui.column().classes("w-full gap-1")

        def _add_tool() -> None:
            """ add tool.
            
            Returns
            -------
            Any
                Function result.
            
            """
            with tool_box:
                with ui.row().classes("w-full gap-1 items-center") as row:
                    inp = ui.input("Tool", placeholder="e.g. ace by daisy").classes("flex-1")
                    ref = {"row": row, "inp": inp}
                    tool_rows.append(ref)

                    def _rm(r=ref) -> None:
                        """ rm.
                        
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
                        if r in tool_rows:
                            tool_rows.remove(r)

                    ui.button("✕", on_click=_rm).props("flat dense").classes("text-red-400")

        def _add_proc() -> None:
            """ add proc.
            
            Returns
            -------
            Any
                Function result.
            
            """
            with proc_box:
                with ui.row().classes("w-full gap-1 items-center") as row:
                    inp = ui.input("Process", placeholder="e.g. daisy conversion").classes("flex-1")
                    ref = {"row": row, "inp": inp}
                    proc_rows.append(ref)

                    def _rm(r=ref) -> None:
                        """ rm.
                        
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
                        if r in proc_rows:
                            proc_rows.remove(r)

                    ui.button("✕", on_click=_rm).props("flat dense").classes("text-red-400")

        ui.button("+ Add Tool", on_click=_add_tool).props("flat dense").classes("text-indigo-600 text-sm")
        _add_tool()
        ui.button("+ Add Process", on_click=_add_proc).props("flat dense").classes("text-indigo-600 text-sm")
        _add_proc()

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _save() -> None:
                """ save.
                
                Returns
                -------
                Any
                    Function result.
                
                """
                if not path_input.value.strip():
                    notify_error("File path is required")
                    return
                tools = [r["inp"].value.strip() for r in tool_rows if r["inp"].value.strip()]
                procs = [r["inp"].value.strip() for r in proc_rows if r["inp"].value.strip()]
                extra: dict | None = None
                if tools or procs:
                    extra = {}
                    if tools:
                        extra["tools"] = tools
                    if procs:
                        extra["processes"] = procs
                step_key = None
                if step_select.value != "(job level)":
                    for k, lbl in _STEP_LABELS.items():
                        if lbl == step_select.value:
                            step_key = k
                            break
                try:
                    fid = Q.ingest_file(
                        path_input.value.strip(),
                        file_use=use_select.value,
                        format_name=fmt_select.value,
                        format_version=ver_input.value.strip(),
                        extra_metadata=extra,
                    )
                    Q.link_file_to_job(fid, "lp_ebraille", job_id, step_key=step_key)
                    Q.log_event(
                        "lp_ebraille", job_id, "INGEST", "SUCCESS",
                        step_key=step_key,
                        file_object_id=fid,
                        detail=f"Ingested {Path(path_input.value.strip()).name}",
                    )
                    notify_success("File ingested")
                    dlg.close()
                    on_done()
                except FileNotFoundError as exc:
                    notify_error(str(exc))
                except Exception as exc:
                    notify_error(f"Error: {exc}")

            ui.button("Ingest", on_click=_save).classes("bg-indigo-600 text-white")

    dlg.open()


def _metadata_dialog(job_id: int, on_done) -> None:
    """ metadata dialog.
    
    Parameters
    ----------
    job_id : Any
        job_id parameter.
    
    on_done : Any
        on_done parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    existing_meta = Q.list_job_metadata("lp_ebraille", job_id)
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
                        Q.set_job_metadata("lp_ebraille", job_id, key, v)
                    else:
                        Q.delete_job_metadata("lp_ebraille", job_id, key)

                for key in non_dc_keys:
                    Q.delete_job_metadata("lp_ebraille", job_id, key)
                for row in extra_rows:
                    k = (row["key"].value or "").strip()
                    v = (row["value"].value or "").strip()
                    if k and v and k in non_dc_keys:
                        Q.set_job_metadata("lp_ebraille", job_id, k, v)

                notify_success("Metadata saved")
                dlg.close()
                on_done()

            ui.button("Save All", on_click=_save_all).classes("bg-blue-600 text-white")

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
    jid = job["id"]

    def _refresh() -> None:
        """ refresh.
        
        Returns
        -------
        Any
            Function result.
        
        """
        j2 = Q.get_lp_job(jid)
        if j2:
            _render(j2)

    def _render(j: dict) -> None:
        """ render.
        
        Parameters
        ----------
        j : Any
            j parameter.
        
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
                ui.label(j["title"]).classes("text-2xl font-bold text-slate-800 flex-1")
                priority_badge(j.get("priority", "normal"))

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
                        Q.update_lp_job(jid, **data)
                        notify_success("Updated")
                        _refresh()

                    _job_dialog(_do, existing=j)

                ui.button("Edit", on_click=_edit).props("flat").classes("text-blue-600")

            with ui.row().classes("gap-6 text-sm text-slate-500 mb-6 flex-wrap"):
                ui.label(f"Type: {j.get('job_type', '').replace('_', ' ').title()}")
                ui.label(f"Requester: {j.get('requester') or '—'}")
                ui.label(f"Due: {j.get('due_date') or '—'}")
                ui.label(f"Created: {str(j.get('created_at', ''))[:10]}")

            with ui.row().classes("gap-4 flex-wrap items-start"):
                # Steps
                with ui.card().classes(
                    "flex-1 min-w-72 p-5 rounded-xl border border-slate-200"
                ):
                    ui.label("Workflow Steps").classes("font-semibold text-slate-700 mb-3")
                    done_count = sum(j.get(s, 0) for s in _STEPS)
                    progress_bar(done_count, len(_STEPS))
                    ui.element("div").classes("h-3")

                    for step in _STEPS:
                        is_done = bool(j.get(step, 0))
                        with ui.row().classes(
                            "items-center gap-3 py-2 border-b border-slate-50 last:border-0"
                        ):
                            with ui.column().classes("flex-1 gap-0"):
                                ui.label(_STEP_LABELS[step]).classes(
                                    "text-sm font-medium text-slate-700"
                                )
                                sf = [
                                    f for f in Q.list_files_for_job("lp_ebraille", jid)
                                    if f.get("step_key") == step
                                ]
                                if sf:
                                    ui.label(f"{len(sf)} file(s)").classes(
                                        "text-xs text-indigo-500"
                                    )
                            if is_done:
                                def _rev(s: str = step) -> None:
                                    """ rev.
                                    
                                    Parameters
                                    ----------
                                    s : Any
                                        s parameter.
                                    
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
                                        Q.revert_step("lp_ebraille", jid, s)
                                        notify_success(f"Reverted {s}")
                                        _refresh()

                                    confirm_dialog(f"Revert '{_STEP_LABELS[s]}'?", _do)

                                ui.badge("✓ Done").classes(
                                    "bg-green-100 text-green-700 text-xs rounded px-2 cursor-pointer"
                                ).on("click", _rev)
                            else:
                                def _comp(s: str = step) -> None:
                                    """ comp.
                                    
                                    Parameters
                                    ----------
                                    s : Any
                                        s parameter.
                                    
                                    Returns
                                    -------
                                    Any
                                        Function result.
                                    
                                    """
                                    Q.complete_step("lp_ebraille", jid, s)
                                    notify_success(f"Completed {s}")
                                    _refresh()

                                ui.button("Mark Done", on_click=_comp).props(
                                    "flat dense"
                                ).classes("text-blue-600 text-xs")

                # Files
                with ui.card().classes(
                    "flex-1 min-w-80 p-5 rounded-xl border border-slate-200"
                ):
                    with ui.row().classes("items-center mb-3"):
                        ui.label("Files").classes("font-semibold text-slate-700 flex-1")
                        ui.button(
                            "+ Attach File",
                            on_click=lambda: _ingest_dialog(jid, _refresh),
                        ).props("flat dense").classes("text-indigo-600 text-sm")

                    files = Q.list_files_for_job("lp_ebraille", jid)
                    if not files:
                        ui.label("No files attached yet.").classes("text-slate-400 text-sm")
                    else:
                        for f in files:
                            with ui.row().classes(
                                "items-center gap-3 py-2 border-b border-slate-50 last:border-0"
                            ):
                                with ui.column().classes("flex-1 gap-0 min-w-0"):
                                    ui.label(f["original_name"]).classes(
                                        "text-sm text-slate-700 truncate"
                                    )
                                    with ui.row().classes("gap-2 flex-wrap"):
                                        file_use_badge(f.get("file_use", "ORIGINAL"))
                                        if f.get("format_name"):
                                            ui.badge(f["format_name"]).classes(
                                                "text-xs bg-slate-100 text-slate-600 rounded px-1"
                                            )

                                def _df(lid: int = f["link_id"]) -> None:
                                    """ df.
                                    
                                    Parameters
                                    ----------
                                    lid : Any
                                        lid parameter.
                                    
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
                                        Q.unlink_file_from_job(lid)
                                        notify_success("Unlinked")
                                        _refresh()

                                    confirm_dialog("Unlink this file?", _do)

                                ui.button("✕", on_click=_df).props("flat dense").classes(
                                    "text-red-400 text-xs"
                                )

                # Metadata
                with ui.card().classes(
                    "flex-1 min-w-64 p-5 rounded-xl border border-slate-200"
                ):
                    with ui.row().classes("items-center mb-3"):
                        ui.label("Descriptive Metadata").classes(
                            "font-semibold text-slate-700 flex-1"
                        )
                        ui.button(
                            "Edit",
                            on_click=lambda: _metadata_dialog(jid, _refresh),
                        ).props("flat dense").classes("text-blue-600 text-sm")

                    meta = Q.list_job_metadata("lp_ebraille", jid)
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

            # Event log
            with ui.card().classes("mt-4 p-5 rounded-xl border border-slate-200"):
                with ui.row().classes("items-center mb-3"):
                    ui.label("Event Log").classes("font-semibold text-slate-700 flex-1")

                    def _note() -> None:
                        """ note.
                        
                        Returns
                        -------
                        Any
                            Function result.
                        
                        """
                        with ui.dialog() as nd, ui.card().classes("p-5 gap-3 w-96"):
                            ui.label("Add Note").classes("font-semibold text-slate-800")
                            nt = ui.textarea("Note").classes("w-full").props("rows=3")
                            ag = ui.input("Agent", value="user").classes("w-full")
                            with ui.row().classes("justify-end gap-2"):
                                ui.button("Cancel", on_click=nd.close).props("flat")

                                def _sn() -> None:
                                    """ sn.
                                    
                                    Returns
                                    -------
                                    Any
                                        Function result.
                                    
                                    """
                                    Q.log_event(
                                        "lp_ebraille", jid, "NOTE", "SUCCESS",
                                        agent=ag.value, detail=nt.value,
                                    )
                                    nd.close()
                                    _refresh()

                                ui.button("Save", on_click=_sn).classes(
                                    "bg-slate-700 text-white"
                                )
                        nd.open()

                    ui.button("+ Add Note", on_click=_note).props("flat dense").classes(
                        "text-slate-600 text-sm"
                    )

                events = Q.list_events_for_job("lp_ebraille", jid)
                if not events:
                    ui.label("No events.").classes("text-slate-400 text-sm")
                else:
                    for ev in events:
                        oc = ev.get("event_outcome", "SUCCESS")
                        clr = OUTCOME_COLORS.get(oc, "text-slate-700")
                        with ui.row().classes(
                            "items-start gap-3 py-2 border-b border-slate-50 last:border-0"
                        ):
                            ui.label(str(ev.get("event_datetime", ""))[:19]).classes(
                                "text-xs text-slate-400 font-mono w-36 shrink-0"
                            )
                            with ui.column().classes("flex-1 gap-0"):
                                with ui.row().classes("gap-2"):
                                    ui.badge(ev["event_type"]).classes(
                                        "text-xs bg-slate-100 text-slate-700 rounded px-1"
                                    )
                                    if ev.get("step_key"):
                                        ui.badge(
                                            _STEP_LABELS.get(ev["step_key"], ev["step_key"])
                                        ).classes(
                                            "text-xs bg-blue-50 text-blue-700 rounded px-1"
                                        )
                                if ev.get("detail"):
                                    ui.label(ev["detail"]).classes(f"text-sm {clr}")

    _render(job)


def _lp_jobs_page(
    content_area: ui.element,
    job_type_filter: str | None,
    page_title: str,
    description: str,
    accent_class: str,
) -> None:
    """ lp jobs page.
    
    Parameters
    ----------
    content_area : Any
        content_area parameter.
    
    job_type_filter : Any
        job_type_filter parameter.
    
    page_title : Any
        page_title parameter.
    
    description : Any
        description parameter.
    
    accent_class : Any
        accent_class parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    content_area.clear()
    with content_area:
        with ui.row().classes("items-center mb-4"):
            section_header(page_title, description)
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
                    Q.add_lp_job(**data)
                    notify_success("Job created")
                    _lp_jobs_page(
                        content_area,
                        job_type_filter,
                        page_title,
                        description,
                        accent_class,
                    )

                _job_dialog(
                    _do,
                    forced_job_type=job_type_filter,
                    title_override=f"New {page_title[:-5] if page_title.endswith(' Jobs') else page_title}",
                )

            ui.button("+ New Job", on_click=_new).classes(
                f"{accent_class} text-white rounded-lg px-4 py-2"
            )

        jobs = Q.list_lp_jobs(job_type_filter)
        if not jobs:
            with ui.card().classes(
                "p-10 text-center border border-slate-200 rounded-xl w-full"
            ):
                ui.label(f"No {page_title.lower()} yet.").classes("text-slate-400 text-lg")
            return

        for job in jobs:
            done = sum(job.get(s, 0) for s in _STEPS)
            with ui.card().classes(
                "p-4 rounded-xl border border-slate-200 hover:border-green-300 "
                "hover:shadow-md transition-all mb-3"
            ):
                with ui.row().classes("items-start gap-3"):
                    with ui.column().classes("flex-1 gap-1 min-w-0"):
                        with ui.row().classes("items-center gap-2"):
                            ui.label(job["title"]).classes(
                                "font-semibold text-slate-800 text-base truncate"
                            )
                            priority_badge(job.get("priority", "normal"))
                            ui.badge(
                                job.get("job_type", "").replace("_", " ").title()
                            ).classes("text-xs bg-green-50 text-green-700 rounded px-2")
                        with ui.row().classes("gap-4 text-xs text-slate-500 flex-wrap"):
                            if job.get("requester"):
                                ui.label(f"→ {job['requester']}")
                            if job.get("due_date"):
                                ui.label(f"Due: {job['due_date']}")
                        progress_bar(done, len(_STEPS))
                        with ui.row().classes("gap-1 flex-wrap mt-1"):
                            for s in _STEPS:
                                status_chip(
                                    _STEP_LABELS[s].split(". ")[1], bool(job.get(s, 0))
                                )

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
                            _job_detail(
                                j, content_area,
                                lambda: _lp_jobs_page(
                                    content_area,
                                    job_type_filter,
                                    page_title,
                                    description,
                                    accent_class,
                                ),
                            )

                        ui.button("View", on_click=_view).props("flat dense").classes(
                            "text-green-600 text-sm"
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
                                Q.delete_lp_job(j["id"])
                                notify_success("Deleted")
                                _lp_jobs_page(
                                    content_area,
                                    job_type_filter,
                                    page_title,
                                    description,
                                    accent_class,
                                )

                            confirm_dialog(f"Delete '{j['title']}'?", _do)

                        ui.button("Delete", on_click=_del).props("flat dense").classes(
                            "text-red-400 text-sm"
                        )


def large_print_jobs_page(content_area: ui.element) -> None:
    """Large print jobs page.
    
    Parameters
    ----------
    content_area : Any
        content_area parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    _lp_jobs_page(
        content_area,
        "large_print",
        "Large Print Jobs",
        "Large print production tracking",
        "bg-green-600",
    )


def ebraille_jobs_page(content_area: ui.element) -> None:
    """Ebraille jobs page.
    
    Parameters
    ----------
    content_area : Any
        content_area parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    _lp_jobs_page(
        content_area,
        "ebraille",
        "eBraille Jobs",
        "eBraille production tracking",
        "bg-emerald-600",
    )


def epub3_daisy_jobs_page(content_area: ui.element) -> None:
    """Epub3 daisy jobs page.
    
    Parameters
    ----------
    content_area : Any
        content_area parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    _lp_jobs_page(
        content_area,
        "epub3_daisy",
        "EPUB3 / DAISY Jobs",
        "EPUB3 and DAISY production tracking",
        "bg-teal-600",
    )


def lp_ebraille_page(content_area: ui.element) -> None:
    """Lp ebraille page.
    
    Parameters
    ----------
    content_area : Any
        content_area parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    _lp_jobs_page(
        content_area,
        None,
        "Large Print / eBraille Jobs",
        "Large print and eBraille production tracking",
        "bg-green-600",
    )
