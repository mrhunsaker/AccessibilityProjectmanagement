"""Print Jobs panel — log and manage 3-D print jobs."""

from __future__ import annotations

import sqlite3
from typing import Optional

from nicegui import ui

from ..db import queries as Q
from .metadata_options import (
    get_dublin_core_examples,
    get_dublin_core_keys,
    get_non_dc_allowed_keys,
    get_option_groups,
)
from .components import confirm_dialog, notify_error, notify_success, section_header


def _metadata_dialog(print_job_id: int, on_done) -> None:
    """ metadata dialog.
    
    Parameters
    ----------
    print_job_id : Any
        print_job_id parameter.
    
    on_done : Any
        on_done parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    existing_meta = Q.list_job_metadata("print", print_job_id)
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
                        Q.set_job_metadata("print", print_job_id, key, v)
                    else:
                        Q.delete_job_metadata("print", print_job_id, key)

                for key in non_dc_keys:
                    Q.delete_job_metadata("print", print_job_id, key)
                for row in extra_rows:
                    k = (row["key"].value or "").strip()
                    v = (row["value"].value or "").strip()
                    if k and v and k in non_dc_keys:
                        Q.set_job_metadata("print", print_job_id, k, v)

                notify_success("Metadata saved")
                dlg.close()
                on_done()

            ui.button("Save All", on_click=_save_all).classes("bg-blue-600 text-white")

    dlg.open()


def _print_job_dialog(on_save, existing: Optional[dict] = None) -> None:
    """ print job dialog.
    
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
    is_edit = existing is not None
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[560px] max-w-full"):
        ui.label("Edit Print Job" if is_edit else "Log Print Job").classes(
            "text-xl font-bold text-slate-800"
        )

        printers = Q.list_printers()
        pnames = [p["name"] for p in printers]
        pids = [p["id"] for p in printers]
        cur_p = existing.get("printer_name", "") if is_edit else (pnames[0] if pnames else "")
        pr_sel = ui.select(pnames or ["(no printers)"], label="Printer*", value=cur_p).classes(
            "w-full"
        )

        filaments = Q.list_filaments()
        fdescs = ["(none)"] + [
            f"{f['brand']} {f['color']} {f['filament_type']}" for f in filaments
        ]
        fids: list[Optional[int]] = [None] + [f["id"] for f in filaments]
        cur_fd = existing.get("filament_desc", "(none)") if is_edit else "(none)"
        fil_sel = ui.select(fdescs, label="Filament Used", value=cur_fd).classes("w-full")

        with ui.row().classes("gap-4 w-full"):
            obj_name = ui.input(
                "Object Name", value=existing.get("object_name", "") if is_edit else ""
            ).classes("flex-1")
            used_g = ui.number(
                "Filament Used (g)",
                value=existing.get("filament_used_g", 0) if is_edit else 0,
                min=0,
            ).classes("flex-1")

        with ui.row().classes("gap-4 w-full"):
            req = ui.input(
                "Requester", value=existing.get("requester", "") if is_edit else ""
            ).classes("flex-1")
            rdate = ui.input(
                "Request Date (YYYY-MM-DD)",
                value=existing.get("request_date", "") if is_edit else "",
            ).classes("flex-1")

        file_path = ui.input(
            "Attach File Path (optional)", placeholder="/path/to/model.3mf"
        ).classes("w-full")

        success_chk = ui.checkbox(
            "Successful", value=bool(existing.get("successful", 1)) if is_edit else True
        )
        fail_reason = ui.input(
            "Failure Reason", value=existing.get("failure_reason", "") if is_edit else ""
        ).classes("w-full")
        notes = ui.textarea(
            "Notes", value=existing.get("notes", "") if is_edit else ""
        ).classes("w-full").props("rows=2")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _save() -> None:
                """ save.
                
                Returns
                -------
                Any
                    Function result.
                
                """
                if not pnames:
                    notify_error("No printers configured. Add one in Admin Settings first.")
                    return
                try:
                    pr_id = pids[pnames.index(pr_sel.value)]
                except (ValueError, IndexError):
                    notify_error("Select a printer")
                    return
                try:
                    f_id = fids[fdescs.index(fil_sel.value)]
                except (ValueError, IndexError):
                    f_id = None
                on_save(
                    dict(
                        printer_id=pr_id,
                        filament_id=f_id,
                        filament_used_g=float(used_g.value or 0),
                        file_source_path=file_path.value.strip() or None,
                        successful=1 if success_chk.value else 0,
                        failure_reason=fail_reason.value.strip() or None,
                        object_name=obj_name.value.strip(),
                        requester=req.value.strip(),
                        request_date=rdate.value.strip() or None,
                        notes=notes.value.strip(),
                    )
                )
                dlg.close()

            ui.button("Save", on_click=_save).classes("bg-blue-600 text-white")

    dlg.open()


def print_jobs_page(content_area: ui.element) -> None:
    """Print jobs page.
    
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
                "3-D Print Jobs",
                "Log every print run with filament tracking and file attachment",
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
                    try:
                        Q.add_print_job(**data)
                        notify_success("Print job logged")
                        print_jobs_page(content_area)
                    except Exception as exc:
                        notify_error(f"Error: {exc}")

                _print_job_dialog(_do)

            ui.button("+ Log Print Job", on_click=_new).classes(
                "bg-amber-600 text-white rounded-lg px-4 py-2"
            )

        jobs = Q.list_print_jobs()
        if not jobs:
            with ui.card().classes(
                "p-10 text-center border border-slate-200 rounded-xl w-full"
            ):
                ui.label("No print jobs yet.").classes("text-slate-400 text-lg")
                ui.label("Click '+ Log Print Job' to record your first print run.").classes(
                    "text-slate-400 text-sm mt-1"
                )
            return

        with ui.card().classes("w-full rounded-xl border border-slate-200 overflow-hidden"):
            with ui.row().classes(
                "gap-2 px-4 py-2 bg-slate-50 text-xs font-semibold text-slate-500 "
                "uppercase tracking-wider border-b"
            ):
                ui.label("Object").classes("flex-1 min-w-40")
                ui.label("Printer").classes("w-40")
                ui.label("Filament").classes("w-48")
                ui.label("Used (g)").classes("w-20 text-right")
                ui.label("Result").classes("w-24 text-center")
                ui.label("Requester").classes("w-32")
                ui.label("Date").classes("w-28")
                ui.label("").classes("w-20")

            for job in jobs:
                with ui.row().classes(
                    "items-center gap-2 px-4 py-3 border-b border-slate-50 "
                    "last:border-0 hover:bg-slate-50"
                ):
                    with ui.column().classes("flex-1 min-w-40 gap-0"):
                        ui.label(
                            job.get("object_name") or job.get("file_name") or "—"
                        ).classes("text-sm text-slate-700 font-medium truncate")
                        if job.get("file_name"):
                            ui.label(f"📎 {job['file_name']}").classes(
                                "text-xs text-indigo-500 truncate"
                            )
                    ui.label(job.get("printer_name") or "—").classes(
                        "w-40 text-sm text-slate-500 truncate"
                    )
                    ui.label(job.get("filament_desc") or "—").classes(
                        "w-48 text-sm text-slate-500 truncate"
                    )
                    ui.label(f"{job.get('filament_used_g', 0):,.0f}").classes(
                        "w-20 text-right text-sm text-slate-700"
                    )
                    if job.get("successful"):
                        ui.badge("✓ OK").classes(
                            "w-24 text-center bg-green-100 text-green-700 rounded text-xs"
                        )
                    else:
                        with ui.element("div").classes("w-24"):
                            ui.badge("✗ FAIL").classes(
                                "w-full text-center bg-red-100 text-red-700 rounded text-xs"
                            )
                    ui.label(job.get("requester") or "—").classes(
                        "w-32 text-sm text-slate-500 truncate"
                    )
                    ui.label(str(job.get("printed_at", ""))[:10]).classes(
                        "w-28 text-xs text-slate-400"
                    )
                    with ui.row().classes("w-20 gap-1 justify-end"):
                        def _meta(j: dict = job) -> None:
                            """ meta.
                            
                            Parameters
                            ----------
                            j : Any
                                j parameter.
                            
                            Returns
                            -------
                            Any
                                Function result.
                            
                            """
                            _metadata_dialog(j["id"], lambda: print_jobs_page(content_area))

                        ui.button("Meta", on_click=_meta).props("flat dense").classes(
                            "text-indigo-600 text-xs"
                        )

                        def _edit(j: dict = job) -> None:
                            """ edit.
                            
                            Parameters
                            ----------
                            j : Any
                                j parameter.
                            
                            Returns
                            -------
                            Any
                                Function result.
                            
                            """
                            def _do(data: dict) -> None:
                                # Recalculate filament delta on edit
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
                                old_grams = float(j.get("filament_used_g") or 0)
                                new_grams = float(data.get("filament_used_g") or 0)
                                delta = new_grams - old_grams
                                fid = data.get("filament_id")
                                if fid and delta != 0:
                                    Q.deduct_filament(fid, delta)
                                edit_fields = {
                                    k: v for k, v in data.items()
                                    if k not in {"file_source_path"}
                                }
                                Q.update_print_job(j["id"], **edit_fields)
                                notify_success("Updated")
                                print_jobs_page(content_area)

                            _print_job_dialog(_do, existing=j)

                        ui.button("Edit", on_click=_edit).props("flat dense").classes(
                            "text-blue-600 text-xs"
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
                                Q.delete_print_job(j["id"])
                                notify_success("Deleted")
                                print_jobs_page(content_area)

                            confirm_dialog("Delete this print job?", _do)

                        ui.button("Del", on_click=_del).props("flat dense").classes(
                            "text-red-400 text-xs"
                        )
