"""
Search page — full-text search across jobs, files, metadata, and event log.

Changes applied (see fix_specs.json):
  FIX-009  Replaced in-memory Python filtering with Q.search_all() which uses
           parameterised SQL LIKE queries — no more per-job DB round-trips.
  FIX-014  Event log content, agent names, and file checksums are now searchable.
"""

from __future__ import annotations

from nicegui import ui

from ..db import queries as Q
from .components import section_header


def search_page(content_area: ui.element) -> None:
    """Render the Search page."""
    content_area.clear()
    with content_area:
        section_header("Search", "Find jobs, files, metadata, and events across the system")

        with ui.row().classes("gap-3 items-center w-full"):
            query_inp = ui.input(
                placeholder="Title, requester, filename, metadata value, SHA-256 hash…"
            ).classes("flex-1").props("outlined clearable")
            ui.button("Search", on_click=lambda: _execute()).classes(
                "bg-blue-600 text-white rounded-lg px-4 py-2"
            )

        results_area = ui.column().classes("w-full gap-4 mt-4")

        def _execute() -> None:
            q = (query_inp.value or "").strip()
            if not q:
                results_area.clear()
                return

            results_area.clear()
            # FIX-009: single call to SQL-backed search function
            data = Q.search_all(q)

            total = sum(len(v) for v in data.values())

            with results_area:
                ui.label(f"{total} result(s) for \u201c{q}\u201d").classes(
                    "text-slate-500 text-sm"
                )

                if not total:
                    ui.label("No matches found.").classes("text-slate-400 text-sm mt-2")
                    return

                def _section(title: str, items: list, render_fn) -> None:
                    if not items:
                        return
                    ui.label(title).classes(
                        "text-sm font-semibold text-slate-500 uppercase tracking-wider mt-4 mb-2"
                    )
                    with ui.card().classes(
                        "w-full rounded-xl border border-slate-200 overflow-hidden"
                    ):
                        for item in items:
                            render_fn(item)

                # ── Braille jobs ──────────────────────────────────────────────
                def _braille_row(j: dict) -> None:
                    with ui.row().classes(
                        "items-center px-4 py-3 border-b border-slate-50 last:border-0 gap-3"
                    ):
                        with ui.column().classes("flex-1 gap-0"):
                            ui.label(j["title"]).classes("text-sm font-medium text-slate-700")
                            ui.label(
                                f"{j.get('braille_type', '').capitalize()} · "
                                f"{j.get('requester') or '—'} · {j.get('priority', '')}"
                            ).classes("text-xs text-slate-400")
                        ui.label(str(j.get("created_at", ""))[:10]).classes(
                            "text-xs text-slate-400 font-mono"
                        )

                _section("Braille Jobs", data["braille_jobs"], _braille_row)

                # ── LP / eBraille / EPUB3 jobs ────────────────────────────────
                def _lp_row(j: dict) -> None:
                    with ui.row().classes(
                        "items-center px-4 py-3 border-b border-slate-50 last:border-0 gap-3"
                    ):
                        with ui.column().classes("flex-1 gap-0"):
                            ui.label(j["title"]).classes("text-sm font-medium text-slate-700")
                            ui.label(
                                f"{j.get('job_type', '').replace('_', ' ').title()} · "
                                f"{j.get('requester') or '—'}"
                            ).classes("text-xs text-slate-400")
                        ui.label(str(j.get("created_at", ""))[:10]).classes(
                            "text-xs text-slate-400 font-mono"
                        )

                _section("Large Print / eBraille / EPUB3 Jobs", data["lp_jobs"], _lp_row)

                # ── Tactile jobs ──────────────────────────────────────────────
                def _tactile_row(j: dict) -> None:
                    with ui.row().classes(
                        "items-center px-4 py-3 border-b border-slate-50 last:border-0 gap-3"
                    ):
                        with ui.column().classes("flex-1 gap-0"):
                            ui.label(j["title"]).classes("text-sm font-medium text-slate-700")
                            ui.label(
                                f"{j.get('tactile_type', '').replace('_', ' ').title()} · "
                                f"{j.get('requester') or '—'}"
                            ).classes("text-xs text-slate-400")
                        ui.label(str(j.get("created_at", ""))[:10]).classes(
                            "text-xs text-slate-400 font-mono"
                        )

                _section("Tactile Graphics Jobs", data["tactile_jobs"], _tactile_row)

                # ── Print jobs ────────────────────────────────────────────────
                def _print_row(j: dict) -> None:
                    with ui.row().classes(
                        "items-center px-4 py-3 border-b border-slate-50 last:border-0 gap-3"
                    ):
                        ui.label(
                            j.get("object_name") or j.get("file_name") or "—"
                        ).classes("flex-1 text-sm text-slate-700")
                        ui.label(j.get("requester") or "—").classes("text-xs text-slate-400")
                        ui.badge(
                            "✓ OK" if j.get("successful") else "✗ FAIL"
                        ).classes(
                            "text-xs rounded "
                            + ("bg-green-100 text-green-700" if j.get("successful")
                               else "bg-red-100 text-red-700")
                        )

                _section("3-D Print Jobs", data["print_jobs"], _print_row)

                # ── Students ──────────────────────────────────────────────────
                def _student_row(s: dict) -> None:
                    with ui.row().classes(
                        "items-center px-4 py-3 border-b border-slate-50 last:border-0 gap-3"
                    ):
                        ui.label(
                            f"{s.get('last_name', '')}, {s.get('first_name', '')}"
                        ).classes("flex-1 text-sm font-medium text-slate-700")
                        ui.label(s.get("school") or "—").classes("text-xs text-slate-400")
                        ui.label(f"Grade {s.get('grade', '—')}").classes(
                            "text-xs text-slate-400"
                        )

                _section("Students", data["students"], _student_row)

                # ── Files ─────────────────────────────────────────────────────
                def _file_row(f: dict) -> None:
                    with ui.row().classes(
                        "items-center px-4 py-3 border-b border-slate-50 last:border-0 gap-3"
                    ):
                        with ui.column().classes("flex-1 gap-0 min-w-0"):
                            ui.label(f["original_name"]).classes(
                                "text-sm text-slate-700 truncate"
                            )
                            chk = f.get("checksum_sha256") or ""
                            if chk:
                                ui.label(chk[:16] + "…").classes(
                                    "text-xs font-mono text-slate-400"
                                ).tooltip(chk)
                        ui.label(f.get("file_use") or "—").classes("text-xs text-slate-400 w-24")
                        ui.label(f.get("format_name") or "—").classes("text-xs text-slate-400 w-20")
                        ui.label(str(f.get("created_at", ""))[:10]).classes(
                            "text-xs text-slate-400 font-mono w-24"
                        )

                _section("Files", data["files"], _file_row)

                # ── Metadata ──────────────────────────────────────────────────
                def _meta_row(m: dict) -> None:
                    with ui.row().classes(
                        "items-center px-4 py-3 border-b border-slate-50 last:border-0 gap-3"
                    ):
                        ui.label(
                            f"{m['job_type']} #{m['job_id']}"
                        ).classes("text-xs text-slate-400 w-28 shrink-0")
                        ui.label(m["meta_key"]).classes(
                            "text-xs font-mono text-slate-500 w-44 shrink-0"
                        )
                        ui.label(m["meta_value"]).classes("text-sm text-slate-700 flex-1")

                _section("Metadata", data["metadata"], _meta_row)

                # ── Event log (FIX-014) ───────────────────────────────────────
                def _event_row(ev: dict) -> None:
                    outcome_color = {
                        "SUCCESS": "text-green-600",
                        "FAILURE": "text-red-600",
                        "WARNING": "text-amber-600",
                    }.get(ev.get("event_type", ""), "text-slate-600")
                    with ui.row().classes(
                        "items-start px-4 py-3 border-b border-slate-50 last:border-0 gap-3"
                    ):
                        ui.label(str(ev.get("event_datetime", ""))[:19]).classes(
                            "text-xs text-slate-400 font-mono w-36 shrink-0"
                        )
                        ui.label(
                            f"{ev.get('job_type', '')} #{ev.get('job_id', '')}"
                        ).classes("text-xs text-slate-400 w-24 shrink-0")
                        ui.badge(ev.get("event_type", "")).classes(
                            "text-xs bg-slate-100 text-slate-700 rounded px-1 shrink-0"
                        )
                        ui.label(ev.get("agent") or "system").classes(
                            "text-xs text-slate-400 italic w-20 shrink-0"
                        )
                        ui.label(ev.get("detail") or "").classes(
                            f"text-sm {outcome_color} flex-1 break-words"
                        )

                _section("Event Log", data["events"], _event_row)

        query_inp.on("keydown.enter", lambda _: _execute())
