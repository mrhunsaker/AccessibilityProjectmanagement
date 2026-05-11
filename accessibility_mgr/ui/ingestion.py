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

                # Optional job linkage
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
                    src = path_inp.value.strip()
                    if not src:
                        notify_error("File path is required")
                        return
                    if not Path(src).exists():
                        notify_error(f"File not found: {src}")
                        return

                    for el in result_card:
                        el.delete()
                    result_card.clear()

                    try:
                        file_id = Q.ingest_file(
                            source_path=src,
                            file_use=use_sel.value,
                            format_name=fmt_sel.value,
                            format_version=ver_inp.value.strip(),
                            encoding=enc_inp.value.strip(),
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
                    "Upload a file from your browser. It will be saved to the job_files/ "
                    "directory and registered with a checksum."
                ).classes("text-sm text-slate-400 mb-3")

                upload_fmt = ui.select(
                    SUPPORTED_TYPES, label="Format", value="PDF"
                ).classes("w-full")
                upload_use = ui.select(
                    FILE_USES, label="File Use", value="ORIGINAL"
                ).classes("w-full")

                uploads_dir = Q.FILES_DIR

                def _handle_upload(event: events.UploadEventArguments) -> None:
                    dest = uploads_dir / event.name
                    dest.write_bytes(event.content.read())
                    try:
                        file_id = Q.ingest_file(
                            source_path=str(dest),
                            file_use=upload_use.value,
                            format_name=upload_fmt.value,
                        )
                        fo = Q.get_file_object(file_id)
                        notify_success(f"Uploaded and ingested: {event.name}")
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
