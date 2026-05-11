"""
Search page — full-text search across jobs, files, and metadata.
"""

from __future__ import annotations

from nicegui import ui

import db.queries as Q
from ui.components import section_header


def _match(text: str, query: str) -> bool:
    return query.lower() in (text or "").lower()


def search_page(content_area: ui.element) -> None:
    """Render the Search page."""
    content_area.clear()
    with content_area:
        section_header("Search", "Find jobs, files, and metadata across the system")

        query_inp = ui.input(
            placeholder="Search by title, requester, filename, metadata value…"
        ).classes("w-full").props("outlined clearable")

        results_area = ui.column().classes("w-full gap-4 mt-4")

        def _execute() -> None:
            q = query_inp.value.strip()
            if not q:
                results_area.clear()
                return

            results_area.clear()
            with results_area:
                # Braille jobs
                braille_hits = [
                    j for j in Q.list_braille_jobs()
                    if _match(j.get("title", ""), q)
                    or _match(j.get("requester", ""), q)
                    or _match(j.get("notes", ""), q)
                ]
                # LP jobs
                lp_hits = [
                    j for j in Q.list_lp_jobs()
                    if _match(j.get("title", ""), q)
                    or _match(j.get("requester", ""), q)
                    or _match(j.get("notes", ""), q)
                ]
                tactile_hits = [
                    j for j in Q.list_tactile_jobs()
                    if _match(j.get("title", ""), q)
                    or _match(j.get("requester", ""), q)
                    or _match(j.get("notes", ""), q)
                ]
                # Print jobs
                print_hits = [
                    j for j in Q.list_print_jobs()
                    if _match(j.get("object_name", ""), q)
                    or _match(j.get("requester", ""), q)
                    or _match(j.get("file_name", ""), q)
                    or _match(j.get("notes", ""), q)
                ]
                # Files
                file_hits = [
                    f for f in Q.list_file_objects()
                    if _match(f.get("original_name", ""), q)
                    or _match(f.get("format_name", ""), q)
                    or _match(f.get("encoding", ""), q)
                ]
                # Job metadata values
                meta_hits: list[dict] = []
                all_job_ids = (
                    [("braille", j["id"]) for j in Q.list_braille_jobs()]
                    + [("lp_ebraille", j["id"]) for j in Q.list_lp_jobs()]
                    + [("tactile", j["id"]) for j in Q.list_tactile_jobs()]
                )
                for jtype, jid in all_job_ids:
                    for k, v in Q.list_job_metadata(jtype, jid).items():
                        if _match(k, q) or _match(v, q):
                            meta_hits.append(
                                {"job_type": jtype, "job_id": jid, "key": k, "value": v}
                            )

                total = (
                    len(braille_hits)
                    + len(lp_hits)
                    + len(tactile_hits)
                    + len(print_hits)
                    + len(file_hits)
                    + len(meta_hits)
                )
                ui.label(
                    f"{total} result(s) for \u201c{q}\u201d"
                ).classes("text-slate-500 text-sm")

                if not total:
                    ui.label("No matches found.").classes(
                        "text-slate-400 text-sm mt-2"
                    )
                    return

                def _section(title: str, items: list, render_fn) -> None:
                    if not items:
                        return
                    ui.label(title).classes(
                        "text-sm font-semibold text-slate-500 uppercase tracking-wider mt-4 mb-2"
                    )
                    with ui.card().classes("w-full rounded-xl border border-slate-200 overflow-hidden"):
                        for item in items:
                            render_fn(item)

                def _braille_row(j: dict) -> None:
                    steps = ["digitized", "formatted", "brailled", "proofread", "delivered"]
                    done = sum(j.get(s, 0) for s in steps)
                    with ui.row().classes(
                        "items-center px-4 py-3 border-b border-slate-50 last:border-0 gap-3"
                    ):
                        with ui.column().classes("flex-1 gap-0"):
                            ui.label(j["title"]).classes("text-sm font-medium text-slate-700")
                            ui.label(
                                f"{j.get('braille_type','').capitalize()} · "
                                f"{j.get('requester') or '—'}"
                            ).classes("text-xs text-slate-400")
                        ui.label(f"{done}/5 steps").classes("text-xs text-slate-400")

                def _lp_row(j: dict) -> None:
                    steps = ["digitized", "formatted", "converted", "proofread", "delivered"]
                    done = sum(j.get(s, 0) for s in steps)
                    with ui.row().classes(
                        "items-center px-4 py-3 border-b border-slate-50 last:border-0 gap-3"
                    ):
                        with ui.column().classes("flex-1 gap-0"):
                            ui.label(j["title"]).classes("text-sm font-medium text-slate-700")
                            ui.label(
                                f"{j.get('job_type','').replace('_',' ').title()} · "
                                f"{j.get('requester') or '—'}"
                            ).classes("text-xs text-slate-400")
                        ui.label(f"{done}/5 steps").classes("text-xs text-slate-400")

                def _print_row(j: dict) -> None:
                    with ui.row().classes(
                        "items-center px-4 py-3 border-b border-slate-50 last:border-0 gap-3"
                    ):
                        ui.label(
                            j.get("object_name") or j.get("file_name") or "—"
                        ).classes("flex-1 text-sm text-slate-700")
                        ui.label(j.get("printer_name") or "—").classes(
                            "text-xs text-slate-400"
                        )
                        ui.badge(
                            "✓ OK" if j.get("successful") else "✗ FAIL"
                        ).classes(
                            "text-xs rounded "
                            + ("bg-green-100 text-green-700" if j.get("successful") else "bg-red-100 text-red-700")
                        )

                def _tactile_row(j: dict) -> None:
                    steps = ["designed", "produced", "qa_reviewed", "delivered"]
                    done = sum(j.get(s, 0) for s in steps)
                    with ui.row().classes(
                        "items-center px-4 py-3 border-b border-slate-50 last:border-0 gap-3"
                    ):
                        with ui.column().classes("flex-1 gap-0"):
                            ui.label(j["title"]).classes("text-sm font-medium text-slate-700")
                            ui.label(
                                f"{j.get('tactile_type','').replace('_',' ').title()} · {j.get('requester') or '—'}"
                            ).classes("text-xs text-slate-400")
                        ui.label(f"{done}/4 steps").classes("text-xs text-slate-400")

                def _file_row(f: dict) -> None:
                    with ui.row().classes(
                        "items-center px-4 py-3 border-b border-slate-50 last:border-0 gap-3"
                    ):
                        ui.label(f["original_name"]).classes(
                            "flex-1 text-sm text-slate-700"
                        )
                        ui.label(f.get("file_use") or "—").classes(
                            "text-xs text-slate-400"
                        )
                        ui.label(f.get("format_name") or "—").classes(
                            "text-xs text-slate-400"
                        )

                def _meta_row(m: dict) -> None:
                    with ui.row().classes(
                        "items-center px-4 py-3 border-b border-slate-50 last:border-0 gap-3"
                    ):
                        ui.label(
                            f"{m['job_type']} #{m['job_id']}"
                        ).classes("text-xs text-slate-400 w-28 shrink-0")
                        ui.label(m["key"]).classes(
                            "text-xs font-mono text-slate-500 w-40 shrink-0"
                        )
                        ui.label(m["value"]).classes(
                            "text-sm text-slate-700 flex-1"
                        )

                _section("Braille Jobs", braille_hits, _braille_row)
                _section("Large Print / eBraille Jobs", lp_hits, _lp_row)
                _section("Tactile Graphics Jobs", tactile_hits, _tactile_row)
                _section("Print Jobs", print_hits, _print_row)
                _section("Files", file_hits, _file_row)
                _section("Metadata", meta_hits, _meta_row)

        query_inp.on("keydown.enter", lambda _: _execute())
        ui.button("Search", on_click=_execute).classes(
            "bg-blue-600 text-white rounded-lg px-4 py-2 mt-2"
        )
