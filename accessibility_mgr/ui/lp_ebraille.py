"""
LP / eBraille / EPUB3-DAISY jobs panel.

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

_STEPS = ["digitized", "formatted", "converted", "proofread", "delivered"]
_STEP_LABELS = {
    "digitized": "1. Digitized",
    "formatted": "2. Formatted",
    "converted": "3. eBraille / LP",
    "proofread": "4. Proofread",
    "delivered": "5. Delivered",
}
_LP_FORMATS = [
    "PDF", "DOCX", "ODT", "EPUB", "EPUB3", "DAISY", "HTML", "TXT",
    "BRF", "EBRF", "Other",
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

def _job_dialog(
    on_save,
    existing: Optional[dict] = None,
    forced_job_type: str | None = None,
    title_override: str | None = None,
) -> None:
    title = title_override or (
        "Edit Large Print / eBraille Job" if existing else "New Large Print / eBraille Job"
    )
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[520px] max-w-full"):
        ui.label(title).classes("text-xl font-bold text-slate-800")

        t_input = ui.input(
            "Title*", value=existing.get("title", "") if existing else ""
        ).classes("w-full")

        types = [r["label"] for r in Q.list_material_categories("lp_type")]
        type_vals = [r["value"] for r in Q.list_material_categories("lp_type")]
        cur_type = forced_job_type or (
            existing.get("job_type", "large_print") if existing else "large_print"
        )
        try:
            cur_label = types[type_vals.index(cur_type)]
        except ValueError:
            cur_label = types[0] if types else "Large Print"

        if forced_job_type:
            ui.input("Job Type", value=cur_label).props("readonly").classes("w-full")
            jt_select = None
        else:
            jt_select = ui.select(types, label="Job Type*", value=cur_label).classes("w-full")

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
                try:
                    sid = student_ids[student_labels.index(student_sel.value)]
                except (ValueError, IndexError):
                    sid = None
                on_save({
                    "title":        t_input.value.strip(),
                    "job_type":     jt_val,
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
    """Attach a file to an LP/eBraille job.

    FIX-008: project context is pre-populated from the job's existing metadata.
    """
    meta = existing_meta or {}
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
            'Record tool(s) and process(es), e.g. tool: "ace by daisy", process: "EPUB validation".'
        ).classes("text-xs text-slate-400")

        tool_rows: list[dict] = []
        proc_rows: list[dict] = []
        tool_box = ui.column().classes("w-full gap-1")
        proc_box = ui.column().classes("w-full gap-1")

        def _add_tool() -> None:
            with tool_box:
                with ui.row().classes("w-full gap-1 items-center") as row:
                    inp = ui.input("Tool", placeholder="e.g. ace by daisy").classes("flex-1")
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
                    inp = ui.input("Process", placeholder="e.g. daisy conversion").classes(
                        "flex-1"
                    )
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
                        extra_metadata=extra,
                        # FIX-008: pass project context
                        project_title=project_inp.value.strip(),
                        student_initials=student_inp.value.strip(),
                        school_name=school_inp.value.strip(),
                        grade_level=grade_inp.value.strip(),
                        subject=subject_inp.value.strip(),
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


# ── Metadata dialog ───────────────────────────────────────────────────────────

def _metadata_dialog(job_id: int, on_done) -> None:
    open_metadata_dialog("lp_ebraille", job_id, on_done)


# ── Job detail view ───────────────────────────────────────────────────────────

def _job_detail(job: dict, content_area: ui.element, refresh_cb) -> None:
    jid = job["id"]

    def _refresh() -> None:
        j2 = Q.get_lp_job(jid)
        if j2:
            _render(j2)

    def _render(j: dict) -> None:
        cur_meta = Q.list_job_metadata("lp_ebraille", jid)
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
                        Q.update_lp_job(jid, **data)
                        notify_success("Updated")
                        _refresh()
                    _job_dialog(_do, existing=j)

                ui.button("Edit", on_click=_edit).props("flat").classes("text-blue-600")
                ui.button(
                    "Export Summary",
                    on_click=lambda: export_job_summary(
                        job_type="lp_ebraille",
                        job=j,
                        step_order=_STEPS,
                        step_labels=_STEP_LABELS,
                    ),
                ).props("flat").classes("text-indigo-600")

            with ui.row().classes("gap-6 text-sm text-slate-500 mb-6 flex-wrap"):
                ui.label(f"Type: {j.get('job_type', '').replace('_', ' ').title()}")
                ui.label(f"Requester: {j.get('requester') or '—'}")
                ui.label(f"Due: {j.get('due_date') or '—'}")
                ui.label(f"Created: {str(j.get('created_at', ''))[:10]}")
                if j.get("delivery_date"):
                    ui.label(
                        f"Delivered: {j['delivery_date']} via "
                        f"{j.get('delivery_method', '—')} to "
                        f"{j.get('delivery_recipient', '—')}"
                    ).classes("text-green-600")

            with ui.row().classes("gap-4 flex-wrap items-start"):

                # ── Steps ─────────────────────────────────────────────────────
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
                                    def _do() -> None:
                                        Q.revert_step("lp_ebraille", jid, s)
                                        notify_success(f"Reverted {s}")
                                        _refresh()
                                    confirm_dialog(f"Revert '{_STEP_LABELS[s]}'?", _do)

                                ui.badge("✓ Done").classes(
                                    "bg-green-100 text-green-700 text-xs rounded px-2 cursor-pointer"
                                ).on("click", _rev)
                            else:
                                def _comp(s: str = step) -> None:
                                    # FIX-016
                                    if s == "delivered":
                                        open_delivery_dialog("lp_ebraille", jid, _refresh)
                                    else:
                                        Q.complete_step("lp_ebraille", jid, s)
                                        notify_success(f"Completed {s}")
                                        _refresh()

                                ui.button("Mark Done", on_click=_comp).props(
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
                                    def _do() -> None:
                                        Q.unlink_file_from_job(lid)
                                        notify_success("Unlinked")
                                        _refresh()
                                    confirm_dialog("Unlink this file?", _do)

                                ui.button("✕", on_click=_df).props("flat dense").classes(
                                    "text-red-400 text-xs"
                                )

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

            # ── Event log ─────────────────────────────────────────────────────
            with ui.card().classes("mt-4 p-5 rounded-xl border border-slate-200"):
                render_event_log(
                    job_type="lp_ebraille",
                    job_id=jid,
                    step_labels=_STEP_LABELS,
                    on_done=_refresh,
                    title="Event Log",
                    step_badge_classes="text-xs bg-blue-50 text-blue-700 rounded px-1",
                )

    _render(job)


# ── Shared list renderer ──────────────────────────────────────────────────────

def _lp_jobs_page(
    content_area: ui.element,
    job_type_filter: str | None,
    page_title: str,
    description: str,
    accent_class: str,
) -> None:
    page_size = 50
    state = {"page": 1, "selected_ids": set()}

    content_area.clear()
    with content_area:
        with ui.row().classes("items-center mb-4"):
            section_header(page_title, description)
            ui.element("div").classes("flex-1")

            def _new() -> None:
                def _do(data: dict) -> None:
                    Q.add_lp_job(**data)
                    notify_success("Job created")
                    _lp_jobs_page(
                        content_area, job_type_filter, page_title, description, accent_class
                    )
                _job_dialog(
                    _do,
                    forced_job_type=job_type_filter,
                    title_override=f"New {page_title[:-5] if page_title.endswith(' Jobs') else page_title}",
                )

            ui.keyboard(
                on_key=lambda e: _new()
                if getattr(e, "action", "") == "keydown"
                and str(getattr(e, "key", "")).lower() == "n"
                else None
            )

            ui.button("+ New Job", on_click=_new).classes(
                f"{accent_class} text-white rounded-lg px-4 py-2"
            )

        pager_row = ui.row().classes("items-center gap-2 mb-3")
        bulk_row = ui.row().classes("items-center gap-2 mb-3")
        list_container = ui.column().classes("w-full")

        def _toggle_selected(job_id: int, selected: bool) -> None:
            if selected:
                state["selected_ids"].add(job_id)
            else:
                state["selected_ids"].discard(job_id)
            _render_page()

        def _render_bulk_actions(current_jobs: list[dict]) -> None:
            bulk_row.clear()
            selected = [j for j in current_jobs if j["id"] in state["selected_ids"]]
            if not selected:
                return

            with bulk_row:
                ui.badge(f"{len(selected)} selected").classes(
                    "bg-green-100 text-green-700 rounded px-2"
                )

                def _delete_selected() -> None:
                    ids = [j["id"] for j in selected]

                    def _do() -> None:
                        for sid in ids:
                            Q.delete_lp_job(sid)
                        state["selected_ids"].difference_update(ids)
                        notify_success(f"Deleted {len(ids)} job(s)")
                        _lp_jobs_page(
                            content_area,
                            job_type_filter,
                            page_title,
                            description,
                            accent_class,
                        )

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
                                "job_type",
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
                                    "job_type": row.get("job_type", ""),
                                    "requester": row.get("requester", ""),
                                    "priority": row.get("priority", ""),
                                    "due_date": row.get("due_date", ""),
                                    "delivery_date": row.get("delivery_date", ""),
                                }
                            )
                    ui.download(tmp.name, filename="lp_ebraille_jobs_selected.csv")

                def _mark_delivered() -> None:
                    for row in selected:
                        Q.record_delivery(
                            "lp_ebraille",
                            row["id"],
                            delivery_method="bulk_action",
                            delivery_recipient="Operations",
                            delivery_notes="Marked delivered via bulk action",
                        )
                    state["selected_ids"].difference_update(r["id"] for r in selected)
                    notify_success(f"Marked {len(selected)} job(s) delivered")
                    _lp_jobs_page(
                        content_area,
                        job_type_filter,
                        page_title,
                        description,
                        accent_class,
                    )

                ui.button("Delete Selected", on_click=_delete_selected).props("flat dense").classes(
                    "text-red-500"
                )
                ui.button("Export Selected (CSV)", on_click=_export_selected).props(
                    "flat dense"
                ).classes("text-indigo-600")
                ui.button("Mark Selected Delivered", on_click=_mark_delivered).props(
                    "flat dense"
                ).classes("text-green-600")

        def _render_page() -> None:
            rows = Q.list_lp_jobs(
                job_type_filter,
                limit=page_size + 1,
                offset=(state["page"] - 1) * page_size,
            )
            has_next = len(rows) > page_size
            jobs = rows[:page_size]
            _render_bulk_actions(jobs)

            pager_row.clear()
            with pager_row:
                ui.button("Prev", on_click=lambda: _set_page(state["page"] - 1)).props(
                    "flat dense"
                ).classes("text-slate-600").props("disable" if state["page"] <= 1 else "")
                ui.label(f"Page {state['page']}").classes("text-sm text-slate-500")
                ui.button("Next", on_click=lambda: _set_page(state["page"] + 1)).props(
                    "flat dense"
                ).classes("text-slate-600").props("disable" if not has_next else "")

            list_container.clear()
            with list_container:
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
                                    ui.badge(
                                        job.get("job_type", "").replace("_", " ").title()
                                    ).classes("text-xs bg-green-50 text-green-700 rounded px-2")
                                    if job.get("delivery_date"):
                                        ui.badge("✓ Delivered").classes(
                                            "text-xs bg-green-100 text-green-700 rounded px-2"
                                        )
                                with ui.row().classes("gap-4 text-xs text-slate-500 flex-wrap"):
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
                                            _STEP_LABELS[s].split(". ")[1], bool(job.get(s, 0))
                                        )

                            with ui.column().classes("gap-1 shrink-0"):
                                def _view(j: dict = job) -> None:
                                    _job_detail(
                                        j,
                                        content_area,
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
                                    def _do() -> None:
                                        Q.delete_lp_job(j["id"])
                                        state["selected_ids"].discard(j["id"])
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

        def _set_page(page: int) -> None:
            state["page"] = max(1, page)
            _render_page()

        _render_page()


def large_print_jobs_page(content_area: ui.element) -> None:
    _lp_jobs_page(
        content_area, "large_print", "Large Print Jobs",
        "Large print production tracking", "bg-green-600",
    )


def ebraille_jobs_page(content_area: ui.element) -> None:
    _lp_jobs_page(
        content_area, "ebraille", "eBraille Jobs",
        "eBraille production tracking", "bg-emerald-600",
    )


def epub3_daisy_jobs_page(content_area: ui.element) -> None:
    _lp_jobs_page(
        content_area, "epub3_daisy", "EPUB3 / DAISY Jobs",
        "EPUB3 and DAISY production tracking", "bg-teal-600",
    )


def lp_ebraille_page(content_area: ui.element) -> None:
    _lp_jobs_page(
        content_area, None, "Large Print / eBraille Jobs",
        "Large print and eBraille production tracking", "bg-green-600",
    )
