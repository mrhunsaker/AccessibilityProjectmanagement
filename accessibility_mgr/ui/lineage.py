"""
Lineage viewer — visualises derivative relationships and provenance chains
using data from the file_object, job_file_link, and metadata_event tables.
"""

from __future__ import annotations

from nicegui import ui

from ..db import queries as Q
from ..services.provenance_registry import ProvenanceRegistry
from .components import section_header


_provenance = ProvenanceRegistry()


# Seed representative provenance events for UI visualization.
_provenance.register_event(
    asset_id=1,
    event_type="metadata_update",
    summary="Accessibility metadata updated",
    metadata={"editor": "operator"},
)

_provenance.register_event(
    asset_id=1,
    event_type="qa_report",
    summary="DAISY Ace QA report generated",
    metadata={"score": 100},
)

_provenance.register_event(
    asset_id=2,
    event_type="pipeline_retry",
    summary="Accessibility pipeline retry requested",
    metadata={"retry_count": 1},
)


def _append_job_edges(
    mermaid_lines: list[str],
    seen_nodes: set[str],
    seen_edges: set[str],
    files: list[dict],
    jobs: dict[int, str],
    job_prefix: str,
    job_label_prefix: str,
    job_type: str,
) -> None:
    """Append Mermaid graph edges for a job collection."""

    for file_obj in files:
        fid = file_obj["id"]
        fnode = f"F{fid}"

        for jid, jtitle in jobs.items():
            linked_files = Q.list_files_for_job(job_type, jid)

            if not any(linked["id"] == fid for linked in linked_files):
                continue

            jnode = f"{job_prefix}{jid}"
            edge = f"  {jnode} --> {fnode}"
            jlabel = jtitle[:25].replace('"', "")
            job_decl = f'  {jnode}[/"{job_label_prefix}: {jlabel}"/]'

            if jnode not in seen_nodes:
                mermaid_lines.append(job_decl)
                seen_nodes.add(jnode)

            if edge not in seen_edges:
                mermaid_lines.append(edge)
                seen_edges.add(edge)


def lineage_page(content_area: ui.element) -> None:
    """Render the Asset Lineage Viewer."""
    page_size = 50
    state = {"page": 1}

    content_area.clear()

    with content_area:
        section_header(
            "Lineage Viewer",
            "Derivative relationships and provenance chains across all jobs",
        )

        files = Q.list_file_objects(limit=300)

        if not files:
            with ui.card().classes(
                "p-10 text-center border border-slate-200 rounded-xl w-full"
            ):
                ui.label("No files ingested yet.").classes(
                    "text-slate-400 text-lg"
                )
                ui.label(
                    "Attach files to production jobs to see lineage here."
                ).classes("text-slate-400 text-sm mt-1")
            return

        ui.label(f"{len(files)} file(s) in registry").classes(
            "text-sm text-slate-400 mb-4"
        )

        braille_jobs = {
            job["id"]: job["title"] for job in Q.list_braille_jobs(limit=500)
        }

        lp_jobs = {
            job["id"]: job["title"] for job in Q.list_lp_jobs(limit=500)
        }

        tactile_jobs = {
            job["id"]: job["title"]
            for job in Q.list_tactile_jobs(limit=500)
        }

        print_jobs = {
            job["id"]: job.get("object_name", "3-D Print Job")
            for job in Q.list_print_jobs(limit=500)
        }

        mermaid_lines = ["graph TD"]
        seen_nodes: set[str] = set()
        seen_edges: set[str] = set()

        for file_obj in files:
            fnode = f"F{file_obj['id']}"
            label = file_obj["original_name"][:30].replace('"', "")
            use = file_obj.get("file_use", "ORIGINAL")
            shape = f'["{label}\\n{use}"]'
            mermaid_lines.append(f"  {fnode}{shape}")

        _append_job_edges(
            mermaid_lines,
            seen_nodes,
            seen_edges,
            files,
            braille_jobs,
            "BJ",
            "Braille",
            "braille",
        )

        _append_job_edges(
            mermaid_lines,
            seen_nodes,
            seen_edges,
            files,
            lp_jobs,
            "LP",
            "LP",
            "lp_ebraille",
        )

        _append_job_edges(
            mermaid_lines,
            seen_nodes,
            seen_edges,
            files,
            tactile_jobs,
            "TG",
            "Tactile",
            "tactile",
        )

        _append_job_edges(
            mermaid_lines,
            seen_nodes,
            seen_edges,
            files,
            print_jobs,
            "PJ",
            "3-D Print",
            "print",
        )

        if len(mermaid_lines) > 1:
            ui.label("File Registry").classes(
                "p-4 rounded-xl border border-slate-200 w-full mb-6"
            ):

            pager_row = ui.row().classes("items-center gap-2 mb-2")
            file_table = ui.column().classes("w-full")

            def _render_file_page() -> None:
                rows = Q.list_file_objects(
                    limit=page_size + 1,
                    offset=(state["page"] - 1) * page_size,
                )
                has_next = len(rows) > page_size
                page_rows = rows[:page_size]

                pager_row.clear()
                with pager_row:
                    ui.button("Prev", on_click=lambda: _set_page(state["page"] - 1)).props(
                        "flat dense"
                    ).classes("text-slate-600").props("disable" if state["page"] <= 1 else "")
                    ui.label(f"Page {state['page']}").classes("text-sm text-slate-500")
                    ui.button("Next", on_click=lambda: _set_page(state["page"] + 1)).props(
                        "flat dense"
                    ).classes("text-slate-600").props("disable" if not has_next else "")

                file_table.clear()
                with file_table:
                    with ui.card().classes(
                        "w-full rounded-xl border border-slate-200 overflow-hidden"
                    ):
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

                        for file_obj in page_rows:
                            size = file_obj.get("size_bytes") or 0
                            size_str = (
                                f"{size // 1_048_576} MB"
                                if size >= 1_048_576
                                else f"{size // 1024} KB"
                                if size >= 1024
                                else f"{size} B"
                            )

                            checksum = str(file_obj.get("checksum_sha256") or "—")
                            checksum_short = checksum[:12] + "…" if len(checksum) > 12 else checksum

                            with ui.row().classes(
                                "items-center px-4 py-2 border-b border-slate-50 last:border-0 gap-2"
                            ):
                                with ui.column().classes("flex-1 gap-0 min-w-0"):
                                    ui.label(file_obj["original_name"]).classes(
                                        "text-sm text-slate-700 truncate"
                                    )
                                    ui.label(file_obj.get("mime_type") or "").classes(
                                        "text-xs text-slate-400"
                                    )

                                ui.label(file_obj.get("file_use") or "—").classes(
                                    "w-28 text-xs text-slate-500"
                                )
                                ui.label(file_obj.get("format_name") or "—").classes(
                                    "w-20 text-xs text-slate-500"
                                )
                                ui.label(size_str).classes("w-20 text-right text-xs text-slate-500")
                                ui.label(checksum_short).classes(
                                    "w-40 text-xs text-slate-500 font-mono"
                                )
                                ui.label(str(file_obj.get("created_at") or "")[:10]).classes(
                                    "w-32 text-xs text-slate-500"
                                )

            def _set_page(page: int) -> None:
                state["page"] = max(1, page)
                _render_file_page()

            _render_file_page()

            for file_obj in files:
                size = file_obj.get("size_bytes") or 0

                size_str = (
                    f"{size // 1_048_576} MB"
                    if size >= 1_048_576
                    else f"{size // 1024} KB"
                    if size >= 1024
                    else f"{size} B"
                )

                checksum = str(file_obj.get("checksum_sha256") or "—")
                checksum_short = (
                    checksum[:12] + "…"
                    if len(checksum) > 12
                    else checksum
                )

                with ui.row().classes(
                    "items-center px-4 py-2 border-b border-slate-50 last:border-0 gap-2"
                ):
                    with ui.column().classes("flex-1 gap-0 min-w-0"):
                        ui.label(file_obj["original_name"]).classes(
                            "text-sm text-slate-700 truncate"
                        )
                        ui.label(file_obj.get("mime_type") or "").classes(
                            "text-xs text-slate-400"
                        )

                    ui.label(file_obj.get("file_use") or "—").classes(
                        "w-28 text-xs text-slate-500"
                    )
                    ui.label(file_obj.get("format_name") or "—").classes(
                        "w-20 text-xs text-slate-500"
                    )
                    ui.label(size_str).classes(
                        "w-20 text-right text-xs text-slate-500"
                    )
                    ui.label(checksum_short).classes(
                        "w-40 text-xs font-mono text-slate-400 truncate"
                    ).tooltip(checksum)
                    ui.label(str(file_obj.get("created_at", ""))[:10]).classes(
                        "w-32 text-xs text-slate-400"
                    )
