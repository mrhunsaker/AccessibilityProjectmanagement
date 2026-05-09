"""
Braille Jobs panel.

Supports:
- Create / edit / delete braille jobs with requester, due date, priority
- Per-step completion tracking with event logging
- File ingestion at each workflow step with format/use metadata
- Dublin Core descriptive metadata key-value store
- PREMIS-style event timeline
- Structural map for multi-part documents
"""

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

_STEPS = ["digitized", "formatted", "brailled", "proofread", "delivered"]
_STEP_LABELS = {
    "digitized": "1. Digitized",
    "formatted": "2. Formatted",
    "brailled":  "3. Brailled",
    "proofread": "4. Proofread",
    "delivered": "5. Delivered",
}
_BRAILLE_FORMATS = ["BRF", "BRL", "BRA", "EBRF", "BES", "PDF", "DOCX", "ODT", "TXT", "XML", "HTML", "EPUB", "MUS", "Other"]
_FILE_USES = ["MASTER", "DERIVATIVE", "INTERMEDIATE", "SOURCE", "REFERENCE"]


# ─── Job form dialog ──────────────────────────────────────────────────────────

def _job_dialog(on_save, existing: Optional[dict] = None) -> None:
    title = "Edit Braille Job" if existing else "New Braille Job"
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[520px] max-w-full"):
        ui.label(title).classes("text-xl font-bold text-slate-800")

        t_input  = ui.input("Title*", value=existing.get("title","") if existing else "").classes("w-full")
        types    = [r["label"] for r in Q.list_material_categories("braille_type")]
        type_vals= [r["value"] for r in Q.list_material_categories("braille_type")]
        cur_type = existing.get("braille_type","literary") if existing else "literary"
        try:
            cur_idx = type_vals.index(cur_type)
            cur_label = types[cur_idx]
        except ValueError:
            cur_label = types[0] if types else "Literary"
        bt_select = ui.select(types, label="Braille Type*", value=cur_label).classes("w-full")

        with ui.row().classes("gap-4 w-full"):
            req_input  = ui.input("Requester", value=existing.get("requester","") if existing else "").classes("flex-1")
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
                    bt_idx = types.index(bt_select.value)
                    bt_val = type_vals[bt_idx]
                except (ValueError, IndexError):
                    bt_val = "literary"
                try:
                    pi_idx = pris.index(pri_select.value)
                    pi_val = pri_vals[pi_idx]
                except (ValueError, IndexError):
                    pi_val = "normal"
                on_save({
                    "title":        t_input.value.strip(),
                    "braille_type": bt_val,
                    "requester":    req_input.value.strip(),
                    "request_date": rdate_input.value.strip() or None,
                    "due_date":     due_input.value.strip() or None,
                    "priority":     pi_val,
                    "notes":        notes_input.value.strip(),
                })
                dlg.close()
            ui.button("Save", on_click=_save).classes("bg-blue-600 text-white")
    dlg.open()


# ─── File ingest dialog ───────────────────────────────────────────────────────

def _ingest_dialog(job_id: int, on_done) -> None:
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[560px] max-w-full"):
        ui.label("Attach File to Job").classes("text-xl font-bold text-slate-800")
        ui.label("Enter the full path of the file on this machine to ingest it into the file store.").classes("text-slate-500 text-sm")

        path_input  = ui.input("File Path*").classes("w-full")
        step_opts   = ["(job level)"] + [_STEP_LABELS[s] for s in _STEPS]
        step_select = ui.select(step_opts, label="Workflow Step", value="(job level)").classes("w-full")
        use_select  = ui.select(_FILE_USES, label="File Use*", value="MASTER").classes("w-full")
        fmt_select  = ui.select(_BRAILLE_FORMATS, label="Format", value="BRF").classes("w-full")
        ver_input   = ui.input("Format Version", placeholder="e.g. 2.0").classes("w-full")
        enc_input   = ui.input("Encoding / Code Table", placeholder="e.g. UEB, Nemeth, EBAE").classes("w-full")
        meta_input  = ui.textarea("Extra Metadata (JSON)", placeholder='{"tool":"BrailleBlaster","version":"1.9"}').classes("w-full").props("rows=3")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")
            def _save():
                if not path_input.value.strip():
                    notify_error("File path is required")
                    return
                extra = None
                if meta_input.value.strip():
                    try:
                        extra = json.loads(meta_input.value.strip())
                    except json.JSONDecodeError:
                        notify_error("Extra metadata is not valid JSON")
                        return
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
                        encoding=enc_input.value.strip(),
                        extra_metadata=extra,
                    )
                    Q.link_file_to_job(fid, "braille", job_id, step_key=step_key)
                    Q.log_event("braille", job_id, "INGEST", "SUCCESS", step_key=step_key,
                                file_object_id=fid,
                                detail=f"Ingested {Path(path_input.value.strip()).name} as {use_select.value}")
                    notify_success("File ingested and linked")
                    dlg.close()
                    on_done()
                except FileNotFoundError as e:
                    notify_error(str(e))
                except Exception as e:
                    notify_error(f"Error: {e}")
            ui.button("Ingest", on_click=_save).classes("bg-indigo-600 text-white")
    dlg.open()


# ─── Metadata dialog ──────────────────────────────────────────────────────────

_DC_KEYS = [
    "dc:title", "dc:creator", "dc:subject", "dc:description", "dc:publisher",
    "dc:contributor", "dc:date", "dc:type", "dc:format", "dc:identifier",
    "dc:source", "dc:language", "dc:rights",
    "grade_level", "subject_area", "isbn", "oclc_number", "series", "volume",
    "edition", "transcriber", "proofreader", "embosser", "emboss_date",
]

def _metadata_dialog(job_id: int, job_type: str, on_done) -> None:
    existing_meta = Q.list_job_metadata(job_type, job_id)

    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[600px] max-w-full max-h-screen overflow-y-auto"):
        ui.label("Descriptive Metadata").classes("text-xl font-bold text-slate-800")
        ui.label("Dublin Core and custom fields. Changes are saved immediately.").classes("text-slate-500 text-sm")

        meta_rows: dict[str, ui.input] = {}
        with ui.column().classes("gap-2 w-full"):
            for key in _DC_KEYS:
                with ui.row().classes("items-center gap-2 w-full"):
                    inp = ui.input(key, value=existing_meta.get(key,"")).classes("flex-1 font-mono text-sm")
                    meta_rows[key] = inp

        # Custom key
        ui.separator()
        ui.label("Add custom field").classes("text-sm font-medium text-slate-600")
        with ui.row().classes("gap-2 w-full"):
            custom_key = ui.input("Key", placeholder="my:field").classes("flex-1")
            custom_val = ui.input("Value").classes("flex-1")
            def _add_custom():
                k = custom_key.value.strip()
                v = custom_val.value.strip()
                if k and v:
                    Q.set_job_metadata(job_type, job_id, k, v)
                    notify_success(f"Set {k}")
                    custom_key.value = ""
                    custom_val.value = ""
            ui.button("Add", on_click=_add_custom).classes("bg-slate-700 text-white")

        with ui.row().classes("justify-end gap-3 mt-4"):
            ui.button("Close", on_click=dlg.close).props("flat").classes("text-slate-500")
            def _save_all():
                for key, inp in meta_rows.items():
                    v = inp.value.strip()
                    if v:
                        Q.set_job_metadata(job_type, job_id, key, v)
                    else:
                        Q.delete_job_metadata(job_type, job_id, key)
                notify_success("Metadata saved")
                dlg.close()
                on_done()
            ui.button("Save All", on_click=_save_all).classes("bg-blue-600 text-white")
    dlg.open()


# ─── Job detail panel ─────────────────────────────────────────────────────────

def _job_detail(job: dict, content_area: ui.element, refresh_cb) -> None:
    jid = job["id"]

    def _refresh():
        j2 = Q.get_braille_job(jid)
        if j2:
            _render_detail(j2)

    def _render_detail(j: dict):
        content_area.clear()
        with content_area:
            with ui.row().classes("items-center gap-3 mb-1"):
                ui.button("← Back", on_click=refresh_cb).props("flat").classes("text-blue-600 text-sm")
                ui.label(j["title"]).classes("text-2xl font-bold text-slate-800 flex-1")
                priority_badge(j.get("priority","normal"))
                def _edit():
                    def _do(data):
                        Q.update_braille_job(jid, **data)
                        notify_success("Job updated")
                        _refresh()
                    _job_dialog(_do, existing=j)
                ui.button("Edit", on_click=_edit).props("flat").classes("text-blue-600")

            with ui.row().classes("gap-6 text-sm text-slate-500 mb-6 flex-wrap"):
                ui.label(f"Type: {j.get('braille_type','').capitalize()}")
                ui.label(f"Requester: {j.get('requester') or '—'}")
                ui.label(f"Requested: {j.get('request_date') or '—'}")
                ui.label(f"Due: {j.get('due_date') or '—'}")
                ui.label(f"Created: {str(j.get('created_at',''))[:10]}")

            with ui.row().classes("gap-4 flex-wrap items-start"):

                # ── Workflow steps ─────────────────────────────────────────
                with ui.card().classes("flex-1 min-w-72 p-5 rounded-xl border border-slate-200"):
                    ui.label("Workflow Steps").classes("font-semibold text-slate-700 mb-3")
                    done_count = sum(j.get(s, 0) for s in _STEPS)
                    progress_bar(done_count, len(_STEPS))
                    ui.element("div").classes("h-3")
                    for step in _STEPS:
                        is_done = bool(j.get(step, 0))
                        with ui.row().classes("items-center gap-3 py-2 border-b border-slate-50 last:border-0"):
                            with ui.column().classes("flex-1 gap-0"):
                                ui.label(_STEP_LABELS[step]).classes("text-sm font-medium text-slate-700")
                                step_files = [f for f in Q.list_files_for_job("braille", jid)
                                              if f.get("step_key") == step]
                                if step_files:
                                    ui.label(f"{len(step_files)} file(s)").classes("text-xs text-indigo-500")
                            if is_done:
                                def _revert(s=step):
                                    def _do():
                                        Q.revert_step("braille", jid, s)
                                        notify_success(f"Reverted: {s}")
                                        _refresh()
                                    confirm_dialog(f"Revert step '{_STEP_LABELS[s]}'?", _do, "Revert Step")
                                ui.badge("✓ Done").classes("bg-green-100 text-green-700 text-xs rounded px-2 cursor-pointer").on("click", _revert)
                            else:
                                def _complete(s=step):
                                    Q.complete_step("braille", jid, s)
                                    notify_success(f"Completed: {s}")
                                    _refresh()
                                ui.button("Mark Done", on_click=_complete).props("flat dense").classes("text-blue-600 text-xs")

                # ── Files ─────────────────────────────────────────────────
                with ui.card().classes("flex-1 min-w-80 p-5 rounded-xl border border-slate-200"):
                    with ui.row().classes("items-center mb-3"):
                        ui.label("Files").classes("font-semibold text-slate-700 flex-1")
                        ui.button("+ Attach File", on_click=lambda: _ingest_dialog(jid, _refresh)).props("flat dense").classes("text-indigo-600 text-sm")
                    files = Q.list_files_for_job("braille", jid)
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
                                        if f.get("step_key"):
                                            ui.badge(_STEP_LABELS.get(f["step_key"],f["step_key"])).classes("text-xs bg-blue-50 text-blue-700 rounded px-1")
                                        sz = f.get("size_bytes")
                                        if sz:
                                            ui.label(f"{sz//1024}KB" if sz < 1_000_000 else f"{sz//1_048_576}MB").classes("text-xs text-slate-400")
                                def _del_file(link_id=f["link_id"]):
                                    def _do():
                                        Q.unlink_file_from_job(link_id)
                                        notify_success("File unlinked")
                                        _refresh()
                                    confirm_dialog("Unlink this file from the job?", _do, "Unlink File")
                                ui.button("✕", on_click=_del_file).props("flat dense").classes("text-red-400 text-xs")

                # ── Metadata ──────────────────────────────────────────────
                with ui.card().classes("flex-1 min-w-64 p-5 rounded-xl border border-slate-200"):
                    with ui.row().classes("items-center mb-3"):
                        ui.label("Descriptive Metadata").classes("font-semibold text-slate-700 flex-1")
                        ui.button("Edit", on_click=lambda: _metadata_dialog(jid, "braille", _refresh)).props("flat dense").classes("text-blue-600 text-sm")
                    meta = Q.list_job_metadata("braille", jid)
                    if not meta:
                        ui.label("No metadata yet").classes("text-slate-400 text-sm")
                    else:
                        for k, v in meta.items():
                            with ui.row().classes("gap-2 py-1 border-b border-slate-50 last:border-0"):
                                ui.label(k).classes("text-xs text-slate-400 font-mono w-36 shrink-0")
                                ui.label(v).classes("text-xs text-slate-700 break-all")

            # ── Notes ─────────────────────────────────────────────────────
            if j.get("notes"):
                with ui.card().classes("mt-4 p-4 rounded-xl border border-slate-200 bg-amber-50"):
                    ui.label("Notes").classes("text-sm font-semibold text-amber-800 mb-1")
                    ui.label(j["notes"]).classes("text-sm text-amber-700")

            # ── Event log ─────────────────────────────────────────────────
            with ui.card().classes("mt-4 p-5 rounded-xl border border-slate-200"):
                with ui.row().classes("items-center mb-3"):
                    ui.label("Provenance / Event Log").classes("font-semibold text-slate-700 flex-1")
                    ui.label("PREMIS-style event history").classes("text-xs text-slate-400")

                    # Manual note entry
                    def _add_note():
                        with ui.dialog() as nd, ui.card().classes("p-5 gap-3 w-96"):
                            ui.label("Add Note Event").classes("font-semibold text-slate-800")
                            note_txt = ui.textarea("Note").classes("w-full").props("rows=3")
                            agent_txt = ui.input("Agent/Author", value="user").classes("w-full")
                            with ui.row().classes("justify-end gap-2"):
                                ui.button("Cancel", on_click=nd.close).props("flat")
                                def _save_note():
                                    Q.log_event("braille", jid, "NOTE", "SUCCESS",
                                                agent=agent_txt.value.strip() or "user",
                                                detail=note_txt.value.strip())
                                    nd.close()
                                    _refresh()
                                ui.button("Save", on_click=_save_note).classes("bg-slate-700 text-white")
                        nd.open()
                    ui.button("+ Add Note", on_click=_add_note).props("flat dense").classes("text-slate-600 text-sm")

                events = Q.list_events_for_job("braille", jid)
                if not events:
                    ui.label("No events recorded").classes("text-slate-400 text-sm")
                else:
                    for ev in events:
                        oc = ev.get("event_outcome","SUCCESS")
                        clr = OUTCOME_COLORS.get(oc, "text-slate-700")
                        with ui.row().classes(f"items-start gap-3 py-2 border-b border-slate-50 last:border-0"):
                            with ui.column().classes("gap-0 w-36 shrink-0"):
                                ui.label(str(ev.get("event_datetime",""))[:19]).classes("text-xs text-slate-400 font-mono")
                                ui.label(ev.get("agent","system")).classes("text-xs text-slate-400 italic")
                            with ui.column().classes("flex-1 gap-0"):
                                with ui.row().classes("gap-2 items-center"):
                                    ui.badge(ev["event_type"]).classes("text-xs bg-slate-100 text-slate-700 rounded px-1")
                                    if ev.get("step_key"):
                                        ui.badge(_STEP_LABELS.get(ev["step_key"],ev["step_key"])).classes("text-xs bg-blue-50 text-blue-700 rounded px-1")
                                    if ev.get("file_name"):
                                        ui.badge(ev["file_name"]).classes("text-xs bg-indigo-50 text-indigo-700 rounded px-1")
                                if ev.get("detail"):
                                    ui.label(ev["detail"]).classes(f"text-sm {clr}")

    _render_detail(job)


# ─── Main braille jobs panel ──────────────────────────────────────────────────

def braille_jobs_page(content_area: ui.element) -> None:
    content_area.clear()
    with content_area:
        with ui.row().classes("items-center mb-4"):
            section_header("Braille Jobs", "Track transcription from digitizing through delivery")
            ui.element("div").classes("flex-1")
            def _new():
                def _do(data):
                    Q.add_braille_job(**data)
                    notify_success("Job created")
                    braille_jobs_page(content_area)
                _job_dialog(_do)
            ui.button("+ New Job", on_click=_new).classes("bg-blue-600 text-white rounded-lg px-4 py-2")

        jobs = Q.list_braille_jobs()
        if not jobs:
            with ui.card().classes("p-10 text-center border border-slate-200 rounded-xl w-full"):
                ui.label("No braille jobs yet").classes("text-slate-400 text-lg")
                ui.label("Click '+ New Job' to create your first braille transcription job").classes("text-slate-400 text-sm mt-1")
            return

        # Filter bar
        with ui.row().classes("gap-3 mb-4 flex-wrap"):
            filter_input = ui.input(placeholder="Search title...").classes("w-64").props("outlined dense clearable")
            type_filter = ui.select(
                ["All Types"] + [r["label"] for r in Q.list_material_categories("braille_type")],
                value="All Types", label="Type"
            ).classes("w-40").props("outlined dense")
            pri_filter = ui.select(
                ["All Priorities"] + [r["label"] for r in Q.list_material_categories("priority")],
                value="All Priorities", label="Priority"
            ).classes("w-44").props("outlined dense")

        job_grid = ui.element("div").classes("grid gap-3 w-full")

        def _render_grid():
            job_grid.clear()
            search = filter_input.value.lower() if filter_input.value else ""
            with job_grid:
                filtered = jobs
                if search:
                    filtered = [j for j in filtered if search in j["title"].lower()
                                or search in (j.get("requester") or "").lower()]
                type_vals = [r["value"] for r in Q.list_material_categories("braille_type")]
                type_labels = [r["label"] for r in Q.list_material_categories("braille_type")]
                if type_filter.value != "All Types":
                    try:
                        tv = type_vals[type_labels.index(type_filter.value)]
                        filtered = [j for j in filtered if j.get("braille_type") == tv]
                    except (ValueError, IndexError):
                        pass
                pri_vals = [r["value"] for r in Q.list_material_categories("priority")]
                pri_labels = [r["label"] for r in Q.list_material_categories("priority")]
                if pri_filter.value != "All Priorities":
                    try:
                        pv = pri_vals[pri_labels.index(pri_filter.value)]
                        filtered = [j for j in filtered if j.get("priority") == pv]
                    except (ValueError, IndexError):
                        pass

                if not filtered:
                    ui.label("No matching jobs").classes("text-slate-400 col-span-full text-center py-8")
                    return

                for job in filtered:
                    steps = _STEPS
                    done = sum(job.get(s, 0) for s in steps)
                    with ui.card().classes("p-4 rounded-xl border border-slate-200 hover:border-blue-300 cursor-pointer hover:shadow-md transition-all"):
                        with ui.row().classes("items-start gap-3"):
                            with ui.column().classes("flex-1 gap-1 min-w-0"):
                                with ui.row().classes("items-center gap-2"):
                                    ui.label(job["title"]).classes("font-semibold text-slate-800 text-base truncate")
                                    priority_badge(job.get("priority","normal"))
                                with ui.row().classes("gap-4 text-xs text-slate-500 flex-wrap"):
                                    ui.label(job.get("braille_type","").capitalize())
                                    if job.get("requester"):
                                        ui.label(f"→ {job['requester']}")
                                    if job.get("due_date"):
                                        ui.label(f"Due: {job['due_date']}")
                                progress_bar(done, len(steps))
                                with ui.row().classes("gap-1 flex-wrap mt-1"):
                                    for s in steps:
                                        status_chip(_STEP_LABELS[s].split(". ")[1], bool(job.get(s,0)))

                            with ui.column().classes("gap-1 shrink-0"):
                                def _view(j=job):
                                    _job_detail(j, content_area, lambda: braille_jobs_page(content_area))
                                ui.button("View", on_click=_view).props("flat dense").classes("text-blue-600 text-sm")
                                def _del(j=job):
                                    def _do():
                                        Q.delete_braille_job(j["id"])
                                        notify_success("Job deleted")
                                        braille_jobs_page(content_area)
                                    confirm_dialog(f"Delete '{j['title']}'?", _do, "Delete Job")
                                ui.button("Delete", on_click=_del).props("flat dense").classes("text-red-400 text-sm")

        filter_input.on("update:model-value", lambda _: _render_grid())
        type_filter.on("update:model-value", lambda _: _render_grid())
        pri_filter.on("update:model-value", lambda _: _render_grid())
        _render_grid()
