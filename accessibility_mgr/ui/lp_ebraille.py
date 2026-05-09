"""Large Print / eBraille jobs panel — mirrors braille_jobs structure."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from nicegui import ui

import db.queries as Q
from ui.components import (
    confirm_dialog, file_use_badge, notify_error, notify_success,
    OUTCOME_COLORS, priority_badge, progress_bar, section_header, status_chip,
)

_STEPS = ["digitized", "formatted", "converted", "proofread", "delivered"]
_STEP_LABELS = {
    "digitized":  "1. Digitized",
    "formatted":  "2. Formatted",
    "converted":  "3. eBraille / LP",
    "proofread":  "4. Proofread",
    "delivered":  "5. Delivered",
}
_LP_FORMATS = ["PDF", "DOCX", "ODT", "EPUB", "HTML", "TXT", "BRF", "EBRF", "Other"]
_FILE_USES = ["MASTER", "DERIVATIVE", "INTERMEDIATE", "SOURCE", "REFERENCE"]


def _job_dialog(on_save, existing: Optional[dict] = None) -> None:
    title = "Edit LP/eBraille Job" if existing else "New LP/eBraille Job"
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[520px] max-w-full"):
        ui.label(title).classes("text-xl font-bold text-slate-800")

        t_input = ui.input("Title*", value=existing.get("title","") if existing else "").classes("w-full")
        types    = [r["label"] for r in Q.list_material_categories("lp_type")]
        type_vals= [r["value"] for r in Q.list_material_categories("lp_type")]
        cur_type = existing.get("job_type","large_print") if existing else "large_print"
        try: cur_label = types[type_vals.index(cur_type)]
        except ValueError: cur_label = types[0] if types else "Large Print"
        jt_select = ui.select(types, label="Job Type*", value=cur_label).classes("w-full")

        with ui.row().classes("gap-4 w-full"):
            req_input   = ui.input("Requester", value=existing.get("requester","") if existing else "").classes("flex-1")
            rdate_input = ui.input("Request Date (YYYY-MM-DD)", value=existing.get("request_date","") if existing else "").classes("flex-1")
        with ui.row().classes("gap-4 w-full"):
            due_input  = ui.input("Due Date (YYYY-MM-DD)", value=existing.get("due_date","") if existing else "").classes("flex-1")
            pris = [r["label"] for r in Q.list_material_categories("priority")]
            pri_vals = [r["value"] for r in Q.list_material_categories("priority")]
            cur_pri = existing.get("priority","normal") if existing else "normal"
            try: cur_pri_label = pris[pri_vals.index(cur_pri)]
            except ValueError: cur_pri_label = "Normal"
            pri_select = ui.select(pris, label="Priority", value=cur_pri_label).classes("flex-1")

        notes_input = ui.textarea("Notes", value=existing.get("notes","") if existing else "").classes("w-full").props("rows=3")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")
            def _save():
                if not t_input.value.strip():
                    notify_error("Title is required")
                    return
                try:
                    jt_idx = types.index(jt_select.value)
                    jt_val = type_vals[jt_idx]
                except (ValueError, IndexError):
                    jt_val = "large_print"
                try:
                    pi_idx = pris.index(pri_select.value)
                    pi_val = pri_vals[pi_idx]
                except (ValueError, IndexError):
                    pi_val = "normal"
                on_save({
                    "title": t_input.value.strip(),
                    "job_type": jt_val,
                    "requester": req_input.value.strip(),
                    "request_date": rdate_input.value.strip() or None,
                    "due_date": due_input.value.strip() or None,
                    "priority": pi_val,
                    "notes": notes_input.value.strip(),
                })
                dlg.close()
            ui.button("Save", on_click=_save).classes("bg-blue-600 text-white")
    dlg.open()


def _ingest_dialog(job_id: int, on_done) -> None:
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[560px] max-w-full"):
        ui.label("Attach File to Job").classes("text-xl font-bold text-slate-800")
        path_input  = ui.input("File Path*").classes("w-full")
        step_opts   = ["(job level)"] + [_STEP_LABELS[s] for s in _STEPS]
        step_select = ui.select(step_opts, label="Workflow Step", value="(job level)").classes("w-full")
        use_select  = ui.select(_FILE_USES, label="File Use*", value="MASTER").classes("w-full")
        fmt_select  = ui.select(_LP_FORMATS, label="Format", value="PDF").classes("w-full")
        ver_input   = ui.input("Format Version").classes("w-full")
        meta_input  = ui.textarea("Extra Metadata (JSON)").classes("w-full").props("rows=3")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")
            def _save():
                extra = None
                if meta_input.value.strip():
                    try: extra = json.loads(meta_input.value.strip())
                    except json.JSONDecodeError:
                        notify_error("Extra metadata must be valid JSON")
                        return
                step_key = None
                if step_select.value != "(job level)":
                    for k, lbl in _STEP_LABELS.items():
                        if lbl == step_select.value:
                            step_key = k
                            break
                try:
                    fid = Q.ingest_file(path_input.value.strip(), file_use=use_select.value,
                                        format_name=fmt_select.value,
                                        format_version=ver_input.value.strip(),
                                        extra_metadata=extra)
                    Q.link_file_to_job(fid, "lp_ebraille", job_id, step_key=step_key)
                    Q.log_event("lp_ebraille", job_id, "INGEST", "SUCCESS", step_key=step_key,
                                file_object_id=fid,
                                detail=f"Ingested {Path(path_input.value.strip()).name}")
                    notify_success("File ingested")
                    dlg.close()
                    on_done()
                except FileNotFoundError as e:
                    notify_error(str(e))
                except Exception as e:
                    notify_error(f"Error: {e}")
            ui.button("Ingest", on_click=_save).classes("bg-indigo-600 text-white")
    dlg.open()


def _job_detail(job: dict, content_area: ui.element, refresh_cb) -> None:
    jid = job["id"]

    def _refresh():
        j2 = Q.get_lp_job(jid)
        if j2:
            _render(j2)

    def _render(j: dict):
        content_area.clear()
        with content_area:
            with ui.row().classes("items-center gap-3 mb-1"):
                ui.button("← Back", on_click=refresh_cb).props("flat").classes("text-blue-600 text-sm")
                ui.label(j["title"]).classes("text-2xl font-bold text-slate-800 flex-1")
                priority_badge(j.get("priority","normal"))
                def _edit():
                    def _do(data): Q.update_lp_job(jid, **data); notify_success("Updated"); _refresh()
                    _job_dialog(_do, existing=j)
                ui.button("Edit", on_click=_edit).props("flat").classes("text-blue-600")

            with ui.row().classes("gap-6 text-sm text-slate-500 mb-6 flex-wrap"):
                ui.label(f"Type: {j.get('job_type','').replace('_',' ').title()}")
                ui.label(f"Requester: {j.get('requester') or '—'}")
                ui.label(f"Due: {j.get('due_date') or '—'}")
                ui.label(f"Created: {str(j.get('created_at',''))[:10]}")

            with ui.row().classes("gap-4 flex-wrap items-start"):
                with ui.card().classes("flex-1 min-w-72 p-5 rounded-xl border border-slate-200"):
                    ui.label("Workflow Steps").classes("font-semibold text-slate-700 mb-3")
                    done_count = sum(j.get(s,0) for s in _STEPS)
                    progress_bar(done_count, len(_STEPS))
                    ui.element("div").classes("h-3")
                    for step in _STEPS:
                        is_done = bool(j.get(step, 0))
                        with ui.row().classes("items-center gap-3 py-2 border-b border-slate-50 last:border-0"):
                            with ui.column().classes("flex-1 gap-0"):
                                ui.label(_STEP_LABELS[step]).classes("text-sm font-medium text-slate-700")
                                sf = [f for f in Q.list_files_for_job("lp_ebraille", jid) if f.get("step_key") == step]
                                if sf: ui.label(f"{len(sf)} file(s)").classes("text-xs text-indigo-500")
                            if is_done:
                                def _rev(s=step):
                                    def _do(): Q.revert_step("lp_ebraille", jid, s); notify_success(f"Reverted {s}"); _refresh()
                                    confirm_dialog(f"Revert '{_STEP_LABELS[s]}'?", _do, "Revert Step")
                                ui.badge("✓ Done").classes("bg-green-100 text-green-700 text-xs rounded px-2 cursor-pointer").on("click",_rev)
                            else:
                                def _comp(s=step):
                                    Q.complete_step("lp_ebraille", jid, s); notify_success(f"Completed {s}"); _refresh()
                                ui.button("Mark Done", on_click=_comp).props("flat dense").classes("text-blue-600 text-xs")

                with ui.card().classes("flex-1 min-w-80 p-5 rounded-xl border border-slate-200"):
                    with ui.row().classes("items-center mb-3"):
                        ui.label("Files").classes("font-semibold text-slate-700 flex-1")
                        ui.button("+ Attach File", on_click=lambda: _ingest_dialog(jid, _refresh)).props("flat dense").classes("text-indigo-600 text-sm")
                    files = Q.list_files_for_job("lp_ebraille", jid)
                    if not files:
                        ui.label("No files attached yet").classes("text-slate-400 text-sm")
                    else:
                        for f in files:
                            with ui.row().classes("items-center gap-3 py-2 border-b border-slate-50 last:border-0"):
                                with ui.column().classes("flex-1 gap-0 min-w-0"):
                                    ui.label(f["original_name"]).classes("text-sm text-slate-700 truncate")
                                    with ui.row().classes("gap-2 flex-wrap"):
                                        file_use_badge(f.get("file_use","MASTER"))
                                        if f.get("format_name"):
                                            ui.badge(f["format_name"]).classes("text-xs bg-slate-100 text-slate-600 rounded px-1")
                                def _df(lid=f["link_id"]):
                                    def _do(): Q.unlink_file_from_job(lid); notify_success("Unlinked"); _refresh()
                                    confirm_dialog("Unlink this file?", _do)
                                ui.button("✕", on_click=_df).props("flat dense").classes("text-red-400 text-xs")

            with ui.card().classes("mt-4 p-5 rounded-xl border border-slate-200"):
                with ui.row().classes("items-center mb-3"):
                    ui.label("Event Log").classes("font-semibold text-slate-700 flex-1")
                    def _note():
                        with ui.dialog() as nd, ui.card().classes("p-5 gap-3 w-96"):
                            ui.label("Add Note").classes("font-semibold text-slate-800")
                            nt = ui.textarea("Note").classes("w-full").props("rows=3")
                            ag = ui.input("Agent", value="user").classes("w-full")
                            with ui.row().classes("justify-end gap-2"):
                                ui.button("Cancel", on_click=nd.close).props("flat")
                                def _sn(): Q.log_event("lp_ebraille",jid,"NOTE","SUCCESS",agent=ag.value,detail=nt.value); nd.close(); _refresh()
                                ui.button("Save", on_click=_sn).classes("bg-slate-700 text-white")
                        nd.open()
                    ui.button("+ Add Note", on_click=_note).props("flat dense").classes("text-slate-600 text-sm")
                events = Q.list_events_for_job("lp_ebraille", jid)
                if not events:
                    ui.label("No events").classes("text-slate-400 text-sm")
                else:
                    for ev in events:
                        with ui.row().classes("items-start gap-3 py-2 border-b border-slate-50 last:border-0"):
                            ui.label(str(ev.get("event_datetime",""))[:19]).classes("text-xs text-slate-400 font-mono w-36 shrink-0")
                            with ui.column().classes("flex-1 gap-0"):
                                with ui.row().classes("gap-2"):
                                    ui.badge(ev["event_type"]).classes("text-xs bg-slate-100 text-slate-700 rounded px-1")
                                    if ev.get("step_key"):
                                        ui.badge(_STEP_LABELS.get(ev["step_key"],ev["step_key"])).classes("text-xs bg-blue-50 text-blue-700 rounded px-1")
                                if ev.get("detail"):
                                    ui.label(ev["detail"]).classes(f"text-sm {OUTCOME_COLORS.get(ev.get('event_outcome','SUCCESS'),'text-slate-700')}")

    _render(job)


def lp_ebraille_page(content_area: ui.element) -> None:
    content_area.clear()
    with content_area:
        with ui.row().classes("items-center mb-4"):
            section_header("LP / eBraille Jobs", "Large print and eBraille production tracking")
            ui.element("div").classes("flex-1")
            def _new():
                def _do(data): Q.add_lp_job(**data); notify_success("Job created"); lp_ebraille_page(content_area)
                _job_dialog(_do)
            ui.button("+ New Job", on_click=_new).classes("bg-green-600 text-white rounded-lg px-4 py-2")

        jobs = Q.list_lp_jobs()
        if not jobs:
            with ui.card().classes("p-10 text-center border border-slate-200 rounded-xl w-full"):
                ui.label("No LP/eBraille jobs yet").classes("text-slate-400 text-lg")
            return

        for job in jobs:
            steps = _STEPS
            done = sum(job.get(s,0) for s in steps)
            with ui.card().classes("p-4 rounded-xl border border-slate-200 hover:border-green-300 cursor-pointer hover:shadow-md transition-all mb-3"):
                with ui.row().classes("items-start gap-3"):
                    with ui.column().classes("flex-1 gap-1 min-w-0"):
                        with ui.row().classes("items-center gap-2"):
                            ui.label(job["title"]).classes("font-semibold text-slate-800 text-base truncate")
                            priority_badge(job.get("priority","normal"))
                            ui.badge(job.get("job_type","").replace("_"," ").title()).classes("text-xs bg-green-50 text-green-700 rounded px-2")
                        with ui.row().classes("gap-4 text-xs text-slate-500 flex-wrap"):
                            if job.get("requester"): ui.label(f"→ {job['requester']}")
                            if job.get("due_date"):  ui.label(f"Due: {job['due_date']}")
                        progress_bar(done, len(steps))
                        with ui.row().classes("gap-1 flex-wrap mt-1"):
                            for s in steps:
                                status_chip(_STEP_LABELS[s].split(". ")[1], bool(job.get(s,0)))
                    with ui.column().classes("gap-1 shrink-0"):
                        def _view(j=job):
                            _job_detail(j, content_area, lambda: lp_ebraille_page(content_area))
                        ui.button("View", on_click=_view).props("flat dense").classes("text-green-600 text-sm")
                        def _del(j=job):
                            def _do(): Q.delete_lp_job(j["id"]); notify_success("Deleted"); lp_ebraille_page(content_area)
                            confirm_dialog(f"Delete '{j['title']}'?", _do)
                        ui.button("Delete", on_click=_del).props("flat dense").classes("text-red-400 text-sm")
