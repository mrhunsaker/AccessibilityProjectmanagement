"""Print Jobs panel — log and manage 3-D print jobs."""

from __future__ import annotations

import sqlite3
from typing import Optional

from nicegui import ui

from ..db import queries as Q
from .components import confirm_dialog, notify_error, notify_success, section_header


def _print_job_dialog(on_save, existing: Optional[dict] = None) -> None:
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
    content_area.clear()
    with content_area:
        with ui.row().classes("items-center mb-4"):
            section_header(
                "3-D Print Jobs",
                "Log every print run with filament tracking and file attachment",
            )
            ui.element("div").classes("flex-1")

            def _new() -> None:
                def _do(data: dict) -> None:
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
                        def _edit(j: dict = job) -> None:
                            def _do(data: dict) -> None:
                                # Recalculate filament delta on edit
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
                            def _do() -> None:
                                Q.delete_print_job(j["id"])
                                notify_success("Deleted")
                                print_jobs_page(content_area)

                            confirm_dialog("Delete this print job?", _do)

                        ui.button("Del", on_click=_del).props("flat dense").classes(
                            "text-red-400 text-xs"
                        )
