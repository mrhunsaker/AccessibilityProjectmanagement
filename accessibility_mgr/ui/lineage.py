"""
Lineage viewer — visualises derivative relationships and provenance chains
using data from the file_object, job_file_link, and metadata_event tables.
"""

from __future__ import annotations

from nicegui import ui

from ..db import queries as Q
from .components import section_header


def lineage_page(content_area: ui.element) -> None:
    """Render the Asset Lineage Viewer."""
    content_area.clear()
    with content_area:
        section_header(
            "Lineage Viewer",
            "Derivative relationships and provenance chains across all jobs",
        )

        # ── File registry summary ─────────────────────────────────────────────
        files = Q.list_file_objects()

        if not files:
            with ui.card().classes("p-10 text-center border border-slate-200 rounded-xl w-full"):
                ui.label("No files ingested yet.").classes("text-slate-400 text-lg")
                ui.label(
                    "Attach files to braille or LP jobs to see lineage here."
                ).classes("text-slate-400 text-sm mt-1")
            return

        ui.label(f"{len(files)} file(s) in registry").classes(
            "text-sm text-slate-400 mb-4"
        )

        # ── Mermaid DAG from job-file links ───────────────────────────────────
        braille_jobs = {j["id"]: j["title"] for j in Q.list_braille_jobs()}
        lp_jobs = {j["id"]: j["title"] for j in Q.list_lp_jobs()}

        mermaid_lines = ["graph TD"]
        seen_edges: set[str] = set()

        # Build nodes for each file
        for f in files:
            fnode = f"F{f['id']}"
            label = f["original_name"][:30].replace('"', "")
            use = f.get("file_use", "ORIGINAL")
            shape = f'["{label}\\n{use}"]'
            mermaid_lines.append(f"  {fnode}{shape}")


        # Re-approach: get all links by scanning files
        for f in files:
            fid = f["id"]
            fnode = f"F{fid}"
            # Check braille jobs
            for jid, jtitle in braille_jobs.items():
                jfiles = Q.list_files_for_job("braille", jid)
                if any(jf["id"] == fid for jf in jfiles):
                    jnode = f"BJ{jid}"
                    edge = f"  {jnode} --> {fnode}"
                    jlabel = jtitle[:25].replace('"', "")
                    job_decl = f'  {jnode}[/"Braille: {jlabel}"/]'
                    if jnode not in seen_edges:
                        mermaid_lines.append(job_decl)
                        seen_edges.add(jnode)
                    if edge not in seen_edges:
                        mermaid_lines.append(edge)
                        seen_edges.add(edge)
            # Check lp jobs
            for jid, jtitle in lp_jobs.items():
                jfiles = Q.list_files_for_job("lp_ebraille", jid)
                if any(jf["id"] == fid for jf in jfiles):
                    jnode = f"LP{jid}"
                    edge = f"  {jnode} --> {fnode}"
                    jlabel = jtitle[:25].replace('"', "")
                    job_decl = f'  {jnode}[/"LP: {jlabel}"/]'
                    if jnode not in seen_edges:
                        mermaid_lines.append(job_decl)
                        seen_edges.add(jnode)
                    if edge not in seen_edges:
                        mermaid_lines.append(edge)
                        seen_edges.add(edge)

        if len(mermaid_lines) > 1:
            with ui.card().classes("p-4 rounded-xl border border-slate-200 w-full mb-6"):
                ui.label("Provenance Graph").classes(
                    "font-semibold text-slate-700 mb-3"
                )
                try:
                    ui.mermaid("\n".join(mermaid_lines))
                except Exception:
                    ui.label("Graph could not be rendered.").classes(
                        "text-slate-400 text-sm"
                    )

        # ── File detail list ──────────────────────────────────────────────────
        ui.label("File Registry").classes(
            "text-sm font-semibold text-slate-500 uppercase tracking-wider mb-2"
        )
        with ui.card().classes("w-full rounded-xl border border-slate-200 overflow-hidden"):
            with ui.row().classes(
                "px-4 py-2 bg-slate-50 text-xs font-semibold text-slate-500 "
                "uppercase tracking-wider border-b"
            ):
                ui.label("File Name").classes("flex-1")
                ui.label("Use").classes("w-28")
                ui.label("Format").classes("w-20")
                ui.label("Size").classes("w-20 text-right")
                ui.label("SHA-256").classes("w-40")
                ui.label("Ingested").classes("w-32")

            for f in files:
                sz = f.get("size_bytes") or 0
                sz_str = (
                    f"{sz // 1_048_576} MB"
                    if sz >= 1_048_576
                    else f"{sz // 1024} KB"
                    if sz >= 1024
                    else f"{sz} B"
                )
                chk = str(f.get("checksum_sha256") or "—")
                chk_short = chk[:12] + "…" if len(chk) > 12 else chk

                with ui.row().classes(
                    "items-center px-4 py-2 border-b border-slate-50 last:border-0 gap-2"
                ):
                    with ui.column().classes("flex-1 gap-0 min-w-0"):
                        ui.label(f["original_name"]).classes(
                            "text-sm text-slate-700 truncate"
                        )
                        ui.label(f.get("mime_type") or "").classes(
                            "text-xs text-slate-400"
                        )
                    ui.label(f.get("file_use") or "—").classes(
                        "w-28 text-xs text-slate-500"
                    )
                    ui.label(f.get("format_name") or "—").classes(
                        "w-20 text-xs text-slate-500"
                    )
                    ui.label(sz_str).classes("w-20 text-right text-xs text-slate-500")
                    ui.label(chk_short).classes(
                        "w-40 text-xs font-mono text-slate-400 truncate"
                    ).tooltip(chk)
                    ui.label(str(f.get("created_at", ""))[:10]).classes(
                        "w-32 text-xs text-slate-400"
                    )
