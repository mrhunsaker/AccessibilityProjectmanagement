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
from .delivery_dialog import open_delivery_dialog

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
                    "request_date": rdate_input.value.strip() or None,
                    "due_date":     due_input.value.strip() or None,
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
    existing_meta = Q.list_job_metadata(job_type, job_id)
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
            with ui.dialog() as od, ui.card().classes(
                "p-5 gap-3 w-[720px] max-w-full max-h-[85vh] overflow-y-auto"
            ):
                ui.label("Potential Metadata Options").classes(
                    "text-lg font-bold text-slate-800"
                )
                ui.label(
                    "Use Admin Settings → Metadata Options to add or remove allowed keys."
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
                    ui.label(dc_examples.get(key, "")).classes("text-[11px] text-slate-400")
                    meta_rows[key] = inp

        ui.separator()
        ui.label("Additional Allowed Fields").classes("text-sm font-medium text-slate-600")
        ui.label("Choose keys from the approved eBraille and METS/PREMIS list.").classes(
            "text-xs text-slate-400"
        )

        extra_rows: list[dict[str, ui.element]] = []
        extra_box = ui.column().classes("w-full gap-2")

        def _add_extra_row(initial_key: str = "", initial_val: str = "") -> None:
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
                saved_keys: list[str] = []
                for key, inp in meta_rows.items():
                    v = inp.value.strip()
                    if v:
                        Q.set_job_metadata(job_type, job_id, key, v)
                        saved_keys.append(key)
                    else:
                        Q.delete_job_metadata(job_type, job_id, key)

                for key in non_dc_keys:
                    Q.delete_job_metadata(job_type, job_id, key)
                for row in extra_rows:
                    k = (row["key"].value or "").strip()
                    v = (row["value"].value or "").strip()
                    if k and v and k in non_dc_keys:
                        Q.set_job_metadata(job_type, job_id, k, v)
                        saved_keys.append(k)

                # FIX-003: persist audit to DB
                Q.log_event(
                    job_type, job_id, "METADATA_UPDATE", "SUCCESS",
                    agent="user",
                    detail=f"Metadata updated: {len(saved_keys)} field(s)",
                    extra_metadata={"updated_keys": saved_keys},
                )
                notify_success("Metadata saved")
                dlg.close()
                on_done()

            ui.button("Save All", on_click=_save_all).classes("bg-blue-600 text-white")

    dlg.open()


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
                with ui.row().classes("items-center mb-3"):
                    ui.label("Provenance / Event Log").classes(
                        "font-semibold text-slate-700 flex-1"
                    )
                    ui.label("PREMIS-style history").classes("text-xs text-slate-400")

                    def _add_note() -> None:
                        with ui.dialog() as nd, ui.card().classes("p-5 gap-3 w-96"):
                            ui.label("Add Note Event").classes("font-semibold text-slate-800")
                            note_txt = ui.textarea("Note").classes("w-full").props("rows=3")
                            agent_txt = ui.input("Agent/Author", value="user").classes("w-full")
                            with ui.row().classes("justify-end gap-2"):
                                ui.button("Cancel", on_click=nd.close).props("flat")

                                def _save_note() -> None:
                                    Q.log_event(
                                        "braille", jid, "NOTE", "SUCCESS",
                                        agent=agent_txt.value.strip() or "user",
                                        detail=note_txt.value.strip(),
                                    )
                                    nd.close()
                                    _refresh()

                                ui.button("Save", on_click=_save_note).classes(
                                    "bg-slate-700 text-white"
                                )
                        nd.open()

                    ui.button("+ Add Note", on_click=_add_note).props(
                        "flat dense"
                    ).classes("text-slate-600 text-sm")

                events = Q.list_events_for_job("braille", jid)
                if not events:
                    ui.label("No events recorded.").classes("text-slate-400 text-sm")
                else:
                    for ev in events:
                        oc = ev.get("event_outcome", "SUCCESS")
                        clr = OUTCOME_COLORS.get(oc, "text-slate-700")
                        with ui.row().classes(
                            "items-start gap-3 py-2 border-b border-slate-50 last:border-0"
                        ):
                            with ui.column().classes("gap-0 w-36 shrink-0"):
                                ui.label(str(ev.get("event_datetime", ""))[:19]).classes(
                                    "text-xs text-slate-400 font-mono"
                                )
                                ui.label(ev.get("agent", "system")).classes(
                                    "text-xs text-slate-400 italic"
                                )
                            with ui.column().classes("flex-1 gap-0"):
                                with ui.row().classes("gap-2 items-center"):
                                    ui.badge(ev["event_type"]).classes(
                                        "text-xs bg-slate-100 text-slate-700 rounded px-1"
                                    )
                                    if ev.get("step_key"):
                                        ui.badge(
                                            _STEP_LABELS.get(ev["step_key"], ev["step_key"])
                                        ).classes(
                                            "text-xs bg-blue-50 text-blue-700 rounded px-1"
                                        )
                                    if ev.get("file_name"):
                                        ui.badge(ev["file_name"]).classes(
                                            "text-xs bg-indigo-50 text-indigo-700 rounded px-1"
                                        )
                                if ev.get("detail"):
                                    ui.label(ev["detail"]).classes(f"text-sm {clr}")

    _render_detail(job)


# ── Main list view ────────────────────────────────────────────────────────────

def braille_jobs_page(content_area: ui.element) -> None:
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

            ui.button("+ New Job", on_click=_new).classes(
                "bg-blue-600 text-white rounded-lg px-4 py-2"
            )

        jobs = Q.list_braille_jobs()
        if not jobs:
            with ui.card().classes(
                "p-10 text-center border border-slate-200 rounded-xl w-full"
            ):
                ui.label("No braille jobs yet.").classes("text-slate-400 text-lg")
                ui.label(
                    "Click '+ New Job' to create your first braille transcription job."
                ).classes("text-slate-400 text-sm mt-1")
            return

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

        job_grid = ui.element("div").classes("grid gap-3 w-full")

        def _render_grid() -> None:
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
                                        ui.label(f"Due: {job['due_date']}")
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
                                        notify_success("Job deleted")
                                        braille_jobs_page(content_area)
                                    confirm_dialog(f"Delete '{j['title']}'?", _do)

                                ui.button("Delete", on_click=_del).props(
                                    "flat dense"
                                ).classes("text-red-400 text-sm")

        filter_input.on("update:model-value", lambda _: _render_grid())
        type_filter.on("update:model-value", lambda _: _render_grid())
        pri_filter.on("update:model-value", lambda _: _render_grid())
        _render_grid()
