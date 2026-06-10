"""
File Ingestion page — preservation-aware ingest of accessibility-production assets.

Computes SHA-256, stores in job_files/, creates file_object record, and logs a
PREMIS INGEST event.
"""

from __future__ import annotations

from pathlib import Path

from nicegui import events, ui

from ..db import queries as Q
from .components import notify_error, notify_success, section_header

SUPPORTED_TYPES = [
    "DOCX", "PDF", "EPUB", "BRF", "PEF", "TXT", "HTML",
    "STL", "3MF", "GCODE", "Images", "Other",
]
FILE_USES = ["ORIGINAL", "SOURCE", "DERIVATIVE", "INTERMEDIATE", "REFERENCE"]


def ingestion_page(content_area: ui.element) -> None:
    """Render the file ingestion page."""
    content_area.clear()
    with content_area:
        section_header(
            "File Ingestion",
            "Ingest accessibility-production assets with preservation metadata",
        )

        with ui.row().classes("gap-6 flex-wrap items-start w-full"):

            # ── Upload / path form ────────────────────────────────────────────
            with ui.card().classes("flex-1 min-w-80 p-5 rounded-xl border border-slate-200"):
                ui.label("Ingest by File Path").classes(
                    "font-semibold text-slate-700 mb-3"
                )
                ui.label(
                    "Enter the full path to a file already on this machine."
                ).classes("text-sm text-slate-400 mb-3")

                path_inp = ui.input(
                    "File Path*", placeholder="/path/to/document.brf"
                ).classes("w-full")
                fmt_sel = ui.select(
                    SUPPORTED_TYPES, label="Format*", value="BRF"
                ).classes("w-full")
                use_sel = ui.select(
                    FILE_USES, label="File Use*", value="ORIGINAL"
                ).classes("w-full")
                enc_inp = ui.input(
                    "Encoding / Code Table",
                    placeholder="e.g. UEB, Nemeth, EBAE",
                ).classes("w-full")
                ver_inp = ui.input(
                    "Format Version", placeholder="e.g. 2.0"
                ).classes("w-full")

                # ── Artifact / project metadata ───────────────────────────────
                ui.separator().classes("my-3")
                ui.label("Artifact Location (required)").classes(
                    "text-xs font-semibold text-slate-500 uppercase tracking-wider"
                )
                ui.label(
                    "The file will be copied to artifacts/<Project Title>/ and named "
                    "using the fields below (e.g. FrAn_LegacyJr_Grade7_Science.brf)."
                ).classes("text-xs text-slate-400 mb-1")
                project_title_inp = ui.input(
                    "Project Title*", placeholder="e.g. Spring 2026 Braille Production"
                ).classes("w-full")
                student_inp = ui.input(
                    "Student Initials",
                    placeholder="e.g. FrAn  (First two of first + first two of last)",
                ).classes("w-full")
                school_inp = ui.input(
                    "School Name",
                    placeholder="e.g. LegacyJr  (abbreviated, no spaces)",
                ).classes("w-full")
                grade_inp = ui.input(
                    "Grade Level",
                    placeholder="e.g. 7",
                ).classes("w-full")
                subject_inp = ui.input(
                    "Subject",
                    placeholder="e.g. Science",
                ).classes("w-full")
                ui.separator().classes("my-3")
                ui.label("Tools & Processes").classes(
                    "text-xs font-semibold text-slate-500 uppercase tracking-wider"
                )
                ui.label(
                    'Record the tool(s) and process(es) applied at this step — '
                    'e.g. tool: "brailleblaster", process: "digitize".  '
                    'Multiple tools and processes are allowed.'
                ).classes("text-xs text-slate-400 mb-1")

                tool_rows: list[dict] = []
                proc_rows: list[dict] = []

                ui.label("Tools").classes("text-xs font-medium text-slate-500 mt-1")
                tool_col = ui.column().classes("w-full gap-1")

                def _add_tool() -> None:
                    """ add tool.
                    
                    Returns
                    -------
                    Any
                        Function result.
                    
                    """
                    with tool_col:
                        with ui.row().classes("w-full gap-1 items-center") as row:
                            inp = ui.input(placeholder='e.g. brailleblaster').classes(
                                "flex-1 text-sm"
                            )
                            ref: dict = {"inp": inp, "row": row}
                            tool_rows.append(ref)
                            def _rm_tool(r=ref) -> None:
                                """ rm tool.
                                
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
                            ui.button(icon="close", on_click=_rm_tool).props(
                                "flat dense round size=xs"
                            ).classes("text-slate-400")

                ui.button("+ Add Tool", on_click=_add_tool).props("flat dense").classes(
                    "text-xs text-indigo-600 self-start mt-1"
                )
                _add_tool()

                ui.label("Processes").classes("text-xs font-medium text-slate-500 mt-2")
                proc_col = ui.column().classes("w-full gap-1")

                def _add_proc() -> None:
                    """ add proc.
                    
                    Returns
                    -------
                    Any
                        Function result.
                    
                    """
                    with proc_col:
                        with ui.row().classes("w-full gap-1 items-center") as row:
                            inp = ui.input(
                                placeholder='e.g. digitize  (one process per row)'
                            ).classes("flex-1 text-sm")
                            ref = {"inp": inp, "row": row}
                            proc_rows.append(ref)
                            def _rm_proc(r=ref) -> None:
                                """ rm proc.
                                
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
                            ui.button(icon="close", on_click=_rm_proc).props(
                                "flat dense round size=xs"
                            ).classes("text-slate-400")

                ui.button("+ Add Process", on_click=_add_proc).props("flat dense").classes(
                    "text-xs text-indigo-600 self-start mt-1"
                )
                _add_proc()

                ui.separator().classes("my-3")
                ui.label("Link to Job (optional)").classes(
                    "text-xs font-semibold text-slate-500 uppercase tracking-wider mt-2"
                )
                job_type_sel = ui.select(
                    ["(none)", "braille", "lp_ebraille", "print"],
                    label="Job Type",
                    value="(none)",
                ).classes("w-full")
                job_id_inp = ui.input(
                    "Job ID", placeholder="numeric ID"
                ).classes("w-full")

                result_card: list[ui.element] = []

                def _ingest() -> None:
                    """ ingest.
                    
                    Returns
                    -------
                    Any
                        Function result.
                    
                    """
                    src = path_inp.value.strip()
                    if not src:
                        notify_error("File path is required")
                        return
                    if not Path(src).exists():
                        notify_error(f"File not found: {src}")
                        return
                    if not project_title_inp.value.strip():
                        notify_error("Project Title is required for artifact storage")
                        return

                    for el in result_card:
                        el.delete()
                    result_card.clear()

                    try:
                        _tools = [r["inp"].value.strip() for r in tool_rows if r["inp"].value.strip()]
                        _procs = [r["inp"].value.strip() for r in proc_rows if r["inp"].value.strip()]
                        _extra: dict = {}
                        if _tools:
                            _extra["tools"] = _tools
                        if _procs:
                            _extra["processes"] = _procs

                        file_id = Q.ingest_file(
                            source_path=src,
                            file_use=use_sel.value,
                            format_name=fmt_sel.value,
                            format_version=ver_inp.value.strip(),
                            encoding=enc_inp.value.strip(),
                            project_title=project_title_inp.value.strip(),
                            student_initials=student_inp.value.strip(),
                            school_name=school_inp.value.strip(),
                            grade_level=grade_inp.value.strip(),
                            subject=subject_inp.value.strip(),
                            extra_metadata=_extra or None,
                        )

                        jtype = job_type_sel.value
                        jid_raw = job_id_inp.value.strip()
                        if jtype != "(none)" and jid_raw.isdigit():
                            jid = int(jid_raw)
                            Q.link_file_to_job(file_id, jtype, jid)
                            Q.log_event(
                                jtype, jid, "INGEST", "SUCCESS",
                                file_object_id=file_id,
                                agent="user",
                                detail=f"Ingested {Path(src).name} as {use_sel.value}",
                            )

                        fo = Q.get_file_object(file_id)
                        notify_success(f"Ingested: {Path(src).name}")

                        card = ui.card().classes(
                            "mt-3 p-4 rounded-xl border border-green-200 bg-green-50 w-full"
                        )
                        result_card.append(card)
                        with card:
                            ui.label("✅ File ingested successfully").classes(
                                "font-semibold text-green-700 mb-2"
                            )
                            if fo:
                                for label, val in [
                                    ("File ID", fo["id"]),
                                    ("UUID", fo["uuid"]),
                                    ("Size", f"{fo.get('size_bytes', 0):,} bytes"),
                                    ("SHA-256", fo.get("checksum_sha256", "—")),
                                    ("MIME", fo.get("mime_type", "—")),
                                    ("Use", fo.get("file_use", "—")),
                                    ("Stored at", fo.get("stored_path", "—")),
                                ]:
                                    with ui.row().classes("gap-2"):
                                        ui.label(f"{label}:").classes(
                                            "text-xs text-slate-500 w-16 shrink-0"
                                        )
                                        ui.label(str(val)).classes(
                                            "text-xs font-mono text-slate-700 break-all"
                                        )

                    except Exception as exc:
                        notify_error(f"Ingest error: {exc}")

                ui.button("Ingest File", on_click=_ingest).classes(
                    "bg-indigo-600 text-white rounded-lg px-4 py-2 mt-3 w-full"
                )

            # ── Upload panel ──────────────────────────────────────────────────
            with ui.card().classes("flex-1 min-w-80 p-5 rounded-xl border border-slate-200"):
                ui.label("Upload File").classes("font-semibold text-slate-700 mb-1")
                ui.label(
                    "Upload a file from your browser. It will be staged temporarily then "
                    "moved into artifacts/<Project Title>/ with the filename convention below."
                ).classes("text-sm text-slate-400 mb-3")

                upload_fmt = ui.select(
                    SUPPORTED_TYPES, label="Format", value="PDF"
                ).classes("w-full")
                upload_use = ui.select(
                    FILE_USES, label="File Use", value="ORIGINAL"
                ).classes("w-full")

                # ── Artifact metadata ────────────────────────────────────────
                ui.separator().classes("my-3")
                ui.label("Artifact Location (required)").classes(
                    "text-xs font-semibold text-slate-500 uppercase tracking-wider"
                )
                ui.label(
                    "File will be saved as: StudentInitials_SchoolName_GradeN_Subject.ext"
                ).classes("text-xs text-slate-400 mb-1")
                up_project_inp = ui.input(
                    "Project Title*", placeholder="e.g. Spring 2026 Braille Production"
                ).classes("w-full")
                up_student_inp = ui.input(
                    "Student Initials", placeholder="e.g. FrAn"
                ).classes("w-full")
                up_school_inp = ui.input(
                    "School Name", placeholder="e.g. LegacyJr"
                ).classes("w-full")
                up_grade_inp = ui.input(
                    "Grade Level", placeholder="e.g. 7"
                ).classes("w-full")
                up_subject_inp = ui.input(
                    "Subject", placeholder="e.g. Science"
                ).classes("w-full")

                ui.separator().classes("my-3")
                ui.label("Tools & Processes").classes(
                    "text-xs font-semibold text-slate-500 uppercase tracking-wider"
                )
                ui.label(
                    'Record the tool(s) and process(es) applied at this step — '
                    'e.g. tool: "brailleblaster", process: "OCR".  '
                    'Multiple tools and processes are allowed.'
                ).classes("text-xs text-slate-400 mb-1")

                up_tool_rows: list[dict] = []
                up_proc_rows: list[dict] = []

                ui.label("Tools").classes("text-xs font-medium text-slate-500 mt-1")
                up_tool_col = ui.column().classes("w-full gap-1")

                def _up_add_tool() -> None:
                    """ up add tool.
                    
                    Returns
                    -------
                    Any
                        Function result.
                    
                    """
                    with up_tool_col:
                        with ui.row().classes("w-full gap-1 items-center") as row:
                            inp = ui.input(placeholder='e.g. brailleblaster').classes(
                                "flex-1 text-sm"
                            )
                            ref: dict = {"inp": inp, "row": row}
                            up_tool_rows.append(ref)
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
                                if r in up_tool_rows:
                                    up_tool_rows.remove(r)
                            ui.button(icon="close", on_click=_rm).props(
                                "flat dense round size=xs"
                            ).classes("text-slate-400")

                ui.button("+ Add Tool", on_click=_up_add_tool).props("flat dense").classes(
                    "text-xs text-indigo-600 self-start mt-1"
                )
                _up_add_tool()

                ui.label("Processes").classes("text-xs font-medium text-slate-500 mt-2")
                up_proc_col = ui.column().classes("w-full gap-1")

                def _up_add_proc() -> None:
                    """ up add proc.
                    
                    Returns
                    -------
                    Any
                        Function result.
                    
                    """
                    with up_proc_col:
                        with ui.row().classes("w-full gap-1 items-center") as row:
                            inp = ui.input(
                                placeholder='e.g. OCR  (one process per row)'
                            ).classes("flex-1 text-sm")
                            ref = {"inp": inp, "row": row}
                            up_proc_rows.append(ref)
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
                                if r in up_proc_rows:
                                    up_proc_rows.remove(r)
                            ui.button(icon="close", on_click=_rm).props(
                                "flat dense round size=xs"
                            ).classes("text-slate-400")

                ui.button("+ Add Process", on_click=_up_add_proc).props("flat dense").classes(
                    "text-xs text-indigo-600 self-start mt-1"
                )
                _up_add_proc()
                ui.separator().classes("my-3")

                uploads_dir = Q.FILES_DIR

                def _handle_upload(event: events.UploadEventArguments) -> None:
                    """ handle upload.
                    
                    Parameters
                    ----------
                    event : Any
                        event parameter.
                    
                    Returns
                    -------
                    Any
                        Function result.
                    
                    """
                    if not up_project_inp.value.strip():
                        notify_error("Project Title is required for artifact storage")
                        return
                    # Stage the upload temporarily in job_files/, then ingest to artifacts/
                    stage = uploads_dir / event.name
                    stage.write_bytes(event.content.read())
                    try:
                        _up_tools = [r["inp"].value.strip() for r in up_tool_rows if r["inp"].value.strip()]
                        _up_procs = [r["inp"].value.strip() for r in up_proc_rows if r["inp"].value.strip()]
                        _up_extra: dict = {}
                        if _up_tools:
                            _up_extra["tools"] = _up_tools
                        if _up_procs:
                            _up_extra["processes"] = _up_procs

                        file_id = Q.ingest_file(
                            source_path=str(stage),
                            file_use=upload_use.value,
                            format_name=upload_fmt.value,
                            project_title=up_project_inp.value.strip(),
                            student_initials=up_student_inp.value.strip(),
                            school_name=up_school_inp.value.strip(),
                            grade_level=up_grade_inp.value.strip(),
                            subject=up_subject_inp.value.strip(),
                            extra_metadata=_up_extra or None,
                        )
                        # Remove the temporary staged copy
                        stage.unlink(missing_ok=True)
                        fo = Q.get_file_object(file_id)
                        notify_success(f"Uploaded and ingested: {event.name}")
                        if fo:
                            notify_success(f"Saved to: {fo.get('stored_path', '—')}")
                    except Exception as exc:
                        notify_error(f"Error: {exc}")

                ui.upload(on_upload=_handle_upload).classes("w-full").props(
                    "accept=.pdf,.docx,.epub,.brf,.pef,.txt,.html,.stl,.3mf,.gcode,.png,.jpg"
                )

        # ── Recent ingestions ──────────────────────────────────────────────────
        ui.label("Recent Ingestions").classes(
            "text-sm font-semibold text-slate-500 uppercase tracking-wider mt-8 mb-2"
        )
        recent = Q.list_file_objects()[:20]
        if not recent:
            ui.label("No files ingested yet.").classes("text-slate-400 text-sm")
        else:
            with ui.card().classes("w-full rounded-xl border border-slate-200 overflow-hidden"):
                with ui.row().classes(
                    "px-4 py-2 bg-slate-50 text-xs font-semibold text-slate-500 "
                    "uppercase tracking-wider border-b"
                ):
                    ui.label("File Name").classes("flex-1")
                    ui.label("Use").classes("w-28")
                    ui.label("Format").classes("w-20")
                    ui.label("Size").classes("w-20 text-right")
                    ui.label("Ingested").classes("w-32")

                for f in recent:
                    sz = f.get("size_bytes") or 0
                    sz_str = (
                        f"{sz // 1_048_576} MB"
                        if sz >= 1_048_576
                        else f"{sz // 1024} KB"
                        if sz >= 1024
                        else f"{sz} B"
                    )
                    with ui.row().classes(
                        "items-center px-4 py-2 border-b border-slate-50 last:border-0 gap-2"
                    ):
                        ui.label(f["original_name"]).classes(
                            "flex-1 text-sm text-slate-700 truncate"
                        )
                        ui.label(f.get("file_use") or "—").classes(
                            "w-28 text-xs text-slate-500"
                        )
                        ui.label(f.get("format_name") or "—").classes(
                            "w-20 text-xs text-slate-500"
                        )
                        ui.label(sz_str).classes(
                            "w-20 text-right text-xs text-slate-500"
                        )
                        ui.label(str(f.get("created_at", ""))[:10]).classes(
                            "w-32 text-xs text-slate-400"
                        )
