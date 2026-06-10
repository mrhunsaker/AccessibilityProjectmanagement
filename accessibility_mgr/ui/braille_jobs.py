"""
Braille Jobs panel — full workflow tracking with file ingestion,
Dublin Core metadata, PREMIS event log, and step management.

Changes applied (see fix_specs.json):
  FIX-003  _save_all in metadata dialog now calls Q.log_event (persisted to DB).
  FIX-008  _ingest_dialog pre-populates project context from job metadata so
           files land in artifacts/<Project Title>/ not job_files/<uuid>.<ext>.
  FIX-016  Delivered step opens delivery confirmation dialog instead of direct toggle.
"""

from __future__ import annotations

import csv
import tempfile
from datetime import date
from pathlib import Path
from typing import Optional

from nicegui import ui

from ..db import queries as Q
from .components import (
    confirm_dialog,
    file_use_badge,
    notify_error,
    notify_success,
    priority_badge,
    progress_bar,
    section_header,
    status_chip,
    validate_iso_date,
)
from .delivery_dialog import open_delivery_dialog
from .job_components import export_job_summary, open_metadata_dialog, render_event_log

_STEPS = ["digitized", "formatted", "brailled", "proofread", "delivered"]
_STEP_LABELS = {
    "digitized": "1. Digitized",
    "formatted": "2. Formatted",
    "brailled":  "3. Brailled",
    "proofread": "4. Proofread",
    "delivered": "5. Delivered",
}
_BRAILLE_FORMATS = [
    "BRF", "BRL", "BRA", "EBRF", "BES", "PDF", "DOCX",
    "ODT", "TXT", "XML", "HTML", "EPUB", "MUS", "Other",
]
_FILE_USES = ["ORIGINAL", "DERIVATIVE", "INTERMEDIATE", "SOURCE", "REFERENCE"]


def _is_overdue(job: dict) -> bool:
    due_date = (job.get("due_date") or "").strip()
    if not due_date:
        return False
    if int(job.get("delivered") or 0) == 1:
        return False
    try:
        return date.fromisoformat(due_date) < date.today()
    except ValueError:
        return False


# ── Job form dialog ───────────────────────────────────────────────────────────

def _job_dialog(on_save, existing: Optional[dict] = None) -> None:
    title = "Edit Braille Job" if existing else "New Braille Job"
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[520px] max-w-full"):
        ui.label(title).classes("text-xl font-bold text-slate-800")

        t_input = ui.input(
            "Title*", value=existing.get("title", "") if existing else ""
        ).classes("w-full")

        types = [r["label"] for r in Q.list_material_categories("braille_type")]
        type_vals = [r["value"] for r in Q.list_material_categories("braille_type")]
        cur_type = existing.get("braille_type", "literary") if existing else "literary"
        try:
            cur_label = types[type_vals.index(cur_type)]
        except ValueError:
            cur_label = types[0] if types else "Literary"
        bt_select = ui.select(types, label="Braille Type*", value=cur_label).classes("w-full")

        embossers = Q.list_embossers()
        embosser_labels = [
            f"{e['name']} ({(e.get('paper_type') or 'unknown').replace('_', ' ')})"
            for e in embossers
        ]
        embosser_ids = [e["id"] for e in embossers]
        cur_embosser_id = existing.get("embosser_id") if existing else None
        if cur_embosser_id in embosser_ids:
            cur_embosser_label = embosser_labels[embosser_ids.index(cur_embosser_id)]
        else:
            cur_embosser_label = embosser_labels[0] if embosser_labels else "(no embossers configured)"
        embosser_select = ui.select(
            embosser_labels or ["(no embossers configured)"],
            label="Embosser",
            value=cur_embosser_label,
        ).classes("w-full")

        # Student selector
        students = Q.list_students()
        student_labels = ["(none)"] + [
            f"{s['last_name']}, {s['first_name']} — {s.get('school', '')}"
            for s in students
        ]
        student_ids: list[Optional[int]] = [None] + [s["id"] for s in students]
        cur_sid = existing.get("student_id") if existing else None
        cur_slbl = (
            student_labels[student_ids.index(cur_sid)]
            if cur_sid in student_ids else "(none)"
        )
        student_sel = ui.select(
            student_labels, label="Student", value=cur_slbl
        ).classes("w-full")

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
            pri_select = ui.select(pris, label="Priority", value=cur_pri_label).classes("flex-1")

        notes_input = ui.textarea(
            "Notes", value=existing.get("notes", "") if existing else ""
        ).classes("w-full").props("rows=3")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _save() -> None:
                if not t_input.value.strip():
                    notify_error("Title is required")
                    return
                request_date = rdate_input.value.strip()
                due_date = due_input.value.strip()
                if request_date and not validate_iso_date(request_date, "Request Date"):
                    return
                if due_date and not validate_iso_date(due_date, "Due Date"):
                    return
                try:
                    bt_val = type_vals[types.index(bt_select.value)]
                except (ValueError, IndexError):
                    bt_val = "literary"
                try:
                    pi_val = pri_vals[pris.index(pri_select.value)]
                except (ValueError, IndexError):
                    pi_val = "normal"
                embosser_id = None
                if embossers:
                    try:
                        embosser_id = embosser_ids[embosser_labels.index(embosser_select.value)]
                    except (ValueError, IndexError):
                        embosser_id = None
                try:
                    sid = student_ids[student_labels.index(student_sel.value)]
                except (ValueError, IndexError):
                    sid = None
                on_save({
                    "title":        t_input.value.strip(),
                    "braille_type": bt_val,
                    "embosser_id":  embosser_id,
                    "requester":    req_input.value.strip(),
                    "request_date": request_date or None,
                    "due_date":     due_date or None,
                    "priority":     pi_val,
                    "notes":        notes_input.value.strip(),
                    "student_id":   sid,
                })
                dlg.close()

            ui.button("Save", on_click=_save).classes("bg-blue-600 text-white")

    dlg.open()


# ── File ingest dialog ────────────────────────────────────────────────────────

def _ingest_dialog(job_id: int, on_done, existing_meta: Optional[dict] = None) -> None:
    """Attach a file to a braille job.

    FIX-008: project context is pre-populated from the job's existing metadata
    so files land in artifacts/<Project Title>/ instead of job_files/<uuid>.<ext>.
    """
    meta = existing_meta or {}
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[560px] max-w-full"):
        ui.label("Attach File to Job").classes("text-xl font-bold text-slate-800")
        ui.label("Enter the full path of the file on this machine.").classes(
            "text-slate-500 text-sm"
        )

        path_input = ui.input("File Path*").classes("w-full")
        step_opts = ["(job level)"] + [_STEP_LABELS[s] for s in _STEPS]
        step_select = ui.select(
            step_opts, label="Workflow Step", value="(job level)"
        ).classes("w-full")
        use_select = ui.select(_FILE_USES, label="File Use*", value="ORIGINAL").classes("w-full")
        fmt_select = ui.select(_BRAILLE_FORMATS, label="Format", value="BRF").classes("w-full")
        ver_input = ui.input("Format Version", placeholder="e.g. 2.0").classes("w-full")
        enc_input = ui.input(
            "Encoding / Code Table", placeholder="e.g. UEB, Nemeth, EBAE"
        ).classes("w-full")

        # FIX-008: project context pre-populated from job metadata
        ui.separator().classes("my-2")
        ui.label("Artifact Location").classes(
            "text-xs font-semibold text-slate-500 uppercase tracking-wider"
        )
        ui.label(
            "File saved as: StudentInitials_SchoolName_GradeN_Subject.ext"
        ).classes("text-xs text-slate-400 mb-1")
        project_inp = ui.input(
            "Project Title*", value=meta.get("dc:title", "")
        ).classes("w-full")
        student_inp = ui.input("Student Initials", value="").classes("w-full")
        school_inp = ui.input(
            "School Name", value=meta.get("dc:coverage", "")
        ).classes("w-full")
        grade_inp = ui.input(
            "Grade Level", value=meta.get("grade_level", "")
        ).classes("w-full")
        subject_inp = ui.input(
            "Subject", value=meta.get("dc:subject", "")
        ).classes("w-full")

        ui.separator().classes("my-2")
        ui.label("Tools & Processes").classes(
            "text-xs font-semibold text-slate-500 uppercase tracking-wider"
        )
        ui.label(
            'Record tool(s) and process(es), e.g. tool: "brailleblaster", process: "OCR".'
        ).classes("text-xs text-slate-400")

        tool_rows: list[dict] = []
        proc_rows: list[dict] = []
        tool_box = ui.column().classes("w-full gap-1")
        proc_box = ui.column().classes("w-full gap-1")

        def _add_tool() -> None:
            with tool_box:
                with ui.row().classes("w-full gap-1 items-center") as row:
                    inp = ui.input("Tool", placeholder="e.g. brailleblaster").classes("flex-1")
                    ref = {"row": row, "inp": inp}
                    tool_rows.append(ref)

                    def _rm(r=ref) -> None:
                        r["row"].delete()
                        if r in tool_rows:
                            tool_rows.remove(r)

                    ui.button("✕", on_click=_rm).props("flat dense").classes("text-red-400")

        def _add_proc() -> None:
            with proc_box:
                with ui.row().classes("w-full gap-1 items-center") as row:
                    inp = ui.input("Process", placeholder="e.g. digitize").classes("flex-1")
                    ref = {"row": row, "inp": inp}
                    proc_rows.append(ref)

                    def _rm(r=ref) -> None:
                        r["row"].delete()
                        if r in proc_rows:
                            proc_rows.remove(r)

                    ui.button("✕", on_click=_rm).props("flat dense").classes("text-red-400")

        ui.button("+ Add Tool", on_click=_add_tool).props("flat dense").classes(
            "text-indigo-600 text-sm"
        )
        _add_tool()
        ui.button("+ Add Process", on_click=_add_proc).props("flat dense").classes(
            "text-indigo-600 text-sm"
        )
        _add_proc()

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _save() -> None:
                if not path_input.value.strip():
                    notify_error("File path is required")
                    return
                tools = [r["inp"].value.strip() for r in tool_rows if r["inp"].value.strip()]
                procs = [r["inp"].value.strip() for r in proc_rows if r["inp"].value.strip()]
                extra: Optional[dict] = None
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
                        encoding=enc_input.value.strip(),
                        extra_metadata=extra,
                        # FIX-008: pass project context
                        project_title=project_inp.value.strip(),
                        student_initials=student_inp.value.strip(),
                        school_name=school_inp.value.strip(),
                        grade_level=grade_inp.value.strip(),
                        subject=subject_inp.value.strip(),
                    )
                    Q.link_file_to_job(fid, "braille", job_id, step_key=step_key)
                    Q.log_event(
                        "braille", job_id, "INGEST", "SUCCESS",
                        step_key=step_key,
                        file_object_id=fid,
                        detail=f"Ingested {Path(path_input.value.strip()).name} as {use_select.value}",
                    )
                    notify_success("File ingested and linked")
                    dlg.close()
                    on_done()
                except FileNotFoundError as exc:
                    notify_error(str(exc))
                except Exception as exc:
                    notify_error(f"Error: {exc}")

            ui.button("Ingest", on_click=_save).classes("bg-indigo-600 text-white")

    dlg.open()


# ── Metadata dialog ───────────────────────────────────────────────────────────

def _metadata_dialog(job_id: int, job_type: str, on_done) -> None:
    open_metadata_dialog(job_type, job_id, on_done)


# ── Job detail view ───────────────────────────────────────────────────────────

def _job_detail(job: dict, content_area: ui.element, refresh_cb) -> None:
    jid = job["id"]

    def _refresh() -> None:
        j2 = Q.get_braille_job(jid)
        if j2:
            _render_detail(j2)

    def _render_detail(j: dict) -> None:
        cur_meta = Q.list_job_metadata("braille", jid)
        content_area.clear()
        with content_area:
            with ui.row().classes("items-center gap-3 mb-1"):
                ui.button("← Back", on_click=refresh_cb).props("flat").classes(
                    "text-blue-600 text-sm"
                )
                ui.label(j["title"]).classes("text-2xl font-bold text-slate-800 flex-1")
                priority_badge(j.get("priority", "normal"))

                def _edit() -> None:
                    def _do(data: dict) -> None:
                        Q.update_braille_job(jid, **data)
                        notify_success("Job updated")
                        _refresh()
                    _job_dialog(_do, existing=j)

                ui.button("Edit", on_click=_edit).props("flat").classes("text-blue-600")
                ui.button(
                    "Export Summary",
                    on_click=lambda: export_job_summary(
                        job_type="braille",
                        job=j,
                        step_order=_STEPS,
                        step_labels=_STEP_LABELS,
                    ),
                ).props("flat").classes("text-indigo-600")

            with ui.row().classes("gap-6 text-sm text-slate-500 mb-6 flex-wrap"):
                ui.label(f"Type: {j.get('braille_type', '').capitalize()}")
                ui.label(f"Embosser: {j.get('embosser_name') or '—'}")
                ui.label(f"Requester: {j.get('requester') or '—'}")
                ui.label(f"Requested: {j.get('request_date') or '—'}")
                ui.label(f"Due: {j.get('due_date') or '—'}")
                ui.label(f"Created: {str(j.get('created_at', ''))[:10]}")
                if j.get("delivery_date"):
                    ui.label(
                        f"Delivered: {j['delivery_date']} via "
                        f"{j.get('delivery_method', '—')} to "
                        f"{j.get('delivery_recipient', '—')}"
                    ).classes("text-green-600")

            with ui.row().classes("gap-4 flex-wrap items-start"):

                # ── Workflow steps ────────────────────────────────────────────
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
                                step_files = [
                                    f for f in Q.list_files_for_job("braille", jid)
                                    if f.get("step_key") == step
                                ]
                                if step_files:
                                    ui.label(f"{len(step_files)} file(s)").classes(
                                        "text-xs text-indigo-500"
                                    )
                            if is_done:
                                def _revert(s: str = step) -> None:
                                    def _do() -> None:
                                        Q.revert_step("braille", jid, s)
                                        notify_success(f"Reverted: {s}")
                                        _refresh()
                                    confirm_dialog(
                                        f"Revert step '{_STEP_LABELS[s]}'?", _do, "Revert Step"
                                    )

                                ui.badge("✓ Done").classes(
                                    "bg-green-100 text-green-700 text-xs rounded px-2 cursor-pointer"
                                ).on("click", _revert)
                            else:
                                def _complete(s: str = step) -> None:
                                    # FIX-016: delivered step opens dialog
                                    if s == "delivered":
                                        open_delivery_dialog("braille", jid, _refresh)
                                    else:
                                        Q.complete_step("braille", jid, s)
                                        notify_success(f"Completed: {s}")
                                        _refresh()

                                ui.button("Mark Done", on_click=_complete).props(
                                    "flat dense"
                                ).classes("text-blue-600 text-xs")

                # ── Files ─────────────────────────────────────────────────────
                with ui.card().classes(
                    "flex-1 min-w-80 p-5 rounded-xl border border-slate-200"
                ):
                    with ui.row().classes("items-center mb-3"):
                        ui.label("Files").classes("font-semibold text-slate-700 flex-1")
                        ui.button(
                            "+ Attach File",
                            on_click=lambda: _ingest_dialog(jid, _refresh, cur_meta),
                        ).props("flat dense").classes("text-indigo-600 text-sm")

                    files = Q.list_files_for_job("braille", jid)
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
                                        if f.get("step_key"):
                                            ui.badge(
                                                _STEP_LABELS.get(f["step_key"], f["step_key"])
                                            ).classes(
                                                "text-xs bg-blue-50 text-blue-700 rounded px-1"
                                            )
                                        sz = f.get("size_bytes")
                                        if sz:
                                            ui.label(
                                                f"{sz // 1024}KB"
                                                if sz < 1_000_000
                                                else f"{sz // 1_048_576}MB"
                                            ).classes("text-xs text-slate-400")

                                def _del_file(link_id: int = f["link_id"]) -> None:
                                    def _do() -> None:
                                        Q.unlink_file_from_job(link_id)
                                        notify_success("File unlinked")
                                        _refresh()
                                    confirm_dialog("Unlink this file from the job?", _do)

                                ui.button("✕", on_click=_del_file).props(
                                    "flat dense"
                                ).classes("text-red-400 text-xs")

                # ── Metadata ──────────────────────────────────────────────────
                with ui.card().classes(
                    "flex-1 min-w-64 p-5 rounded-xl border border-slate-200"
                ):
                    with ui.row().classes("items-center mb-3"):
                        ui.label("Descriptive Metadata").classes(
                            "font-semibold text-slate-700 flex-1"
                        )
                        ui.button(
                            "Edit",
                            on_click=lambda: _metadata_dialog(jid, "braille", _refresh),
                        ).props("flat dense").classes("text-blue-600 text-sm")

                    meta = Q.list_job_metadata("braille", jid)
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

            if j.get("notes"):
                with ui.card().classes(
                    "mt-4 p-4 rounded-xl border border-slate-200 bg-amber-50"
                ):
                    ui.label("Notes").classes("text-sm font-semibold text-amber-800 mb-1")
                    ui.label(j["notes"]).classes("text-sm text-amber-700")

            # ── Event log ─────────────────────────────────────────────────────
            with ui.card().classes("mt-4 p-5 rounded-xl border border-slate-200"):
                render_event_log(
                    job_type="braille",
                    job_id=jid,
                    step_labels=_STEP_LABELS,
                    on_done=_refresh,
                    subtitle="PREMIS-style history",
                    step_badge_classes="text-xs bg-blue-50 text-blue-700 rounded px-1",
                )

    _render_detail(job)


# ── Main list view ────────────────────────────────────────────────────────────

def braille_jobs_page(content_area: ui.element) -> None:
    page_size = 50
    state = {"page": 1, "selected_ids": set()}

    content_area.clear()
    with content_area:
        with ui.row().classes("items-center mb-4"):
            section_header(
                "Braille Jobs", "Track transcription from digitizing through delivery"
            )
            ui.element("div").classes("flex-1")

            def _new() -> None:
                def _do(data: dict) -> None:
                    Q.add_braille_job(**data)
                    notify_success("Job created")
                    braille_jobs_page(content_area)
                _job_dialog(_do)

            ui.keyboard(
                on_key=lambda e: _new()
                if getattr(e, "action", "") == "keydown"
                and str(getattr(e, "key", "")).lower() == "n"
                else None
            )

            ui.button("+ New Job", on_click=_new).classes(
                "bg-blue-600 text-white rounded-lg px-4 py-2"
            )

        with ui.row().classes("gap-3 mb-4 flex-wrap"):
            filter_input = ui.input(
                placeholder="Search title or requester…"
            ).classes("w-64").props("outlined dense clearable")
            type_labels = [r["label"] for r in Q.list_material_categories("braille_type")]
            type_vals = [r["value"] for r in Q.list_material_categories("braille_type")]
            type_filter = ui.select(
                ["All Types"] + type_labels, value="All Types", label="Type"
            ).classes("w-40").props("outlined dense")
            pri_labels = [r["label"] for r in Q.list_material_categories("priority")]
            pri_vals = [r["value"] for r in Q.list_material_categories("priority")]
            pri_filter = ui.select(
                ["All Priorities"] + pri_labels, value="All Priorities", label="Priority"
            ).classes("w-44").props("outlined dense")

        pager_row = ui.row().classes("items-center gap-2 mb-3")
        bulk_row = ui.row().classes("items-center gap-2 mb-3")
        job_grid = ui.element("div").classes("grid gap-3 w-full")

        def _toggle_selected(job_id: int, selected: bool) -> None:
            if selected:
                state["selected_ids"].add(job_id)
            else:
                state["selected_ids"].discard(job_id)
            _render_grid()

        def _render_bulk_actions(filtered_jobs: list[dict]) -> None:
            bulk_row.clear()
            selected = [j for j in filtered_jobs if j["id"] in state["selected_ids"]]
            if not selected:
                return

            with bulk_row:
                ui.badge(f"{len(selected)} selected").classes(
                    "bg-blue-100 text-blue-700 rounded px-2"
                )

                def _delete_selected() -> None:
                    ids = [j["id"] for j in selected]

                    def _do() -> None:
                        for sid in ids:
                            Q.delete_braille_job(sid)
                        state["selected_ids"].difference_update(ids)
                        notify_success(f"Deleted {len(ids)} job(s)")
                        braille_jobs_page(content_area)

                    confirm_dialog(f"Delete {len(ids)} selected job(s)?", _do, "Bulk Delete")

                def _export_selected() -> None:
                    with tempfile.NamedTemporaryFile(
                        mode="w",
                        newline="",
                        suffix=".csv",
                        delete=False,
                        encoding="utf-8",
                    ) as tmp:
                        writer = csv.DictWriter(
                            tmp,
                            fieldnames=[
                                "id",
                                "title",
                                "braille_type",
                                "requester",
                                "priority",
                                "due_date",
                                "delivery_date",
                            ],
                        )
                        writer.writeheader()
                        for row in selected:
                            writer.writerow(
                                {
                                    "id": row.get("id"),
                                    "title": row.get("title", ""),
                                    "braille_type": row.get("braille_type", ""),
                                    "requester": row.get("requester", ""),
                                    "priority": row.get("priority", ""),
                                    "due_date": row.get("due_date", ""),
                                    "delivery_date": row.get("delivery_date", ""),
                                }
                            )
                    ui.download(tmp.name, filename="braille_jobs_selected.csv")

                def _mark_delivered() -> None:
                    for row in selected:
                        Q.record_delivery(
                            "braille",
                            row["id"],
                            delivery_method="bulk_action",
                            delivery_recipient="Operations",
                            delivery_notes="Marked delivered via bulk action",
                        )
                    state["selected_ids"].difference_update(r["id"] for r in selected)
                    notify_success(f"Marked {len(selected)} job(s) delivered")
                    braille_jobs_page(content_area)

                ui.button("Delete Selected", on_click=_delete_selected).props("flat dense").classes(
                    "text-red-500"
                )
                ui.button("Export Selected (CSV)", on_click=_export_selected).props(
                    "flat dense"
                ).classes("text-indigo-600")
                ui.button("Mark Selected Delivered", on_click=_mark_delivered).props(
                    "flat dense"
                ).classes("text-green-600")

        def _render_grid() -> None:
            rows = Q.list_braille_jobs(
                limit=page_size + 1,
                offset=(state["page"] - 1) * page_size,
            )
            has_next = len(rows) > page_size
            jobs = rows[:page_size]

            pager_row.clear()
            with pager_row:
                ui.button("Prev", on_click=lambda: _set_page(state["page"] - 1)).props(
                    "flat dense"
                ).classes("text-slate-600").props("disable" if state["page"] <= 1 else "")
                ui.label(f"Page {state['page']}").classes("text-sm text-slate-500")
                ui.button("Next", on_click=lambda: _set_page(state["page"] + 1)).props(
                    "flat dense"
                ).classes("text-slate-600").props("disable" if not has_next else "")

            job_grid.clear()
            search = filter_input.value.lower() if filter_input.value else ""
            filtered = jobs
            if search:
                filtered = [
                    j for j in filtered
                    if search in j["title"].lower()
                    or search in (j.get("requester") or "").lower()
                ]
            if type_filter.value != "All Types":
                try:
                    tv = type_vals[type_labels.index(type_filter.value)]
                    filtered = [j for j in filtered if j.get("braille_type") == tv]
                except (ValueError, IndexError):
                    pass
            if pri_filter.value != "All Priorities":
                try:
                    pv = pri_vals[pri_labels.index(pri_filter.value)]
                    filtered = [j for j in filtered if j.get("priority") == pv]
                except (ValueError, IndexError):
                    pass

            _render_bulk_actions(filtered)

            with job_grid:
                if not filtered:
                    ui.label("No matching jobs.").classes(
                        "text-slate-400 col-span-full text-center py-8"
                    )
                    return

                for job in filtered:
                    done = sum(job.get(s, 0) for s in _STEPS)
                    with ui.card().classes(
                        "p-4 rounded-xl border border-slate-200 hover:border-blue-300 "
                        "hover:shadow-md transition-all"
                    ):
                        with ui.row().classes("items-start gap-3"):
                            ui.checkbox(
                                value=job["id"] in state["selected_ids"],
                                on_change=lambda e, jid=job["id"]: _toggle_selected(
                                    jid, bool(e.value)
                                ),
                            ).props("dense")
                            with ui.column().classes("flex-1 gap-1 min-w-0"):
                                with ui.row().classes("items-center gap-2"):
                                    ui.label(job["title"]).classes(
                                        "font-semibold text-slate-800 text-base truncate"
                                    )
                                    priority_badge(job.get("priority", "normal"))
                                    if job.get("delivery_date"):
                                        ui.badge("✓ Delivered").classes(
                                            "text-xs bg-green-100 text-green-700 rounded px-2"
                                        )
                                with ui.row().classes("gap-4 text-xs text-slate-500 flex-wrap"):
                                    ui.label(job.get("braille_type", "").capitalize())
                                    if job.get("embosser_name"):
                                        ui.label(f"Embosser: {job['embosser_name']}")
                                    if job.get("requester"):
                                        ui.label(f"→ {job['requester']}")
                                    if job.get("due_date"):
                                        ui.label(f"Due: {job['due_date']}").classes(
                                            "text-red-600 font-semibold"
                                            if _is_overdue(job)
                                            else "text-slate-500"
                                        )
                                progress_bar(done, len(_STEPS))
                                with ui.row().classes("gap-1 flex-wrap mt-1"):
                                    for s in _STEPS:
                                        status_chip(
                                            _STEP_LABELS[s].split(". ")[1],
                                            bool(job.get(s, 0)),
                                        )

                            with ui.column().classes("gap-1 shrink-0"):
                                def _view(j: dict = job) -> None:
                                    _job_detail(
                                        j, content_area,
                                        lambda: braille_jobs_page(content_area),
                                    )

                                ui.button("View", on_click=_view).props(
                                    "flat dense"
                                ).classes("text-blue-600 text-sm")

                                def _del(j: dict = job) -> None:
                                    def _do() -> None:
                                        Q.delete_braille_job(j["id"])
                                        state["selected_ids"].discard(j["id"])
                                        notify_success("Job deleted")
                                        braille_jobs_page(content_area)
                                    confirm_dialog(f"Delete '{j['title']}'?", _do)

                                ui.button("Delete", on_click=_del).props(
                                    "flat dense"
                                ).classes("text-red-400 text-sm")

        def _set_page(page: int) -> None:
            state["page"] = max(1, page)
            _render_grid()

        filter_input.on("update:model-value", lambda _: _set_page(1))
        type_filter.on("update:model-value", lambda _: _set_page(1))
        pri_filter.on("update:model-value", lambda _: _set_page(1))
        _render_grid()
