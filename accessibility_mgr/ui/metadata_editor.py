"""
Metadata editor — edit and inspect Dublin Core and custom metadata for any job.
"""

from __future__ import annotations

from nicegui import ui

from ..db import queries as Q
from .components import notify_error, notify_success, section_header

_DC_KEYS = [
    "dc:title", "dc:creator", "dc:subject", "dc:description", "dc:publisher",
    "dc:contributor", "dc:date", "dc:type", "dc:format", "dc:identifier",
    "dc:source", "dc:language", "dc:rights",
    "grade_level", "subject_area", "isbn", "oclc_number", "series", "volume",
    "edition", "transcriber", "proofreader",
]


def _render_editor(job_type: str, job_id: int, container: ui.element) -> None:
    container.clear()
    existing = Q.list_job_metadata(job_type, job_id)

    with container:
        ui.label(f"Editing metadata for {job_type} job #{job_id}").classes(
            "text-sm font-semibold text-slate-600 mb-3"
        )

        inp_map: dict[str, ui.input] = {}

        with ui.grid(columns=2).classes("w-full gap-3"):
            for key in _DC_KEYS:
                with ui.column().classes("gap-0"):
                    inp = ui.input(key, value=existing.get(key, "")).classes(
                        "w-full font-mono text-sm"
                    )
                    inp_map[key] = inp

        # Custom key
        ui.separator().classes("my-4")
        ui.label("Add / update custom field").classes(
            "text-sm font-medium text-slate-600 mb-2"
        )
        with ui.row().classes("gap-3 w-full"):
            ck = ui.input("Key", placeholder="my:field").classes("flex-1")
            cv = ui.input("Value").classes("flex-1")

            def _add_custom() -> None:
                k = ck.value.strip()
                v = cv.value.strip()
                if not k:
                    notify_error("Key is required")
                    return
                Q.set_job_metadata(job_type, job_id, k, v)
                notify_success(f"Set {k}")
                ck.value = ""
                cv.value = ""
                _render_editor(job_type, job_id, container)

            ui.button("Set", on_click=_add_custom).classes(
                "bg-slate-700 text-white rounded-lg px-3"
            )

        # Current custom fields not in DC_KEYS
        custom = {k: v for k, v in existing.items() if k not in _DC_KEYS}
        if custom:
            ui.label("Current custom fields").classes(
                "text-xs font-semibold text-slate-400 uppercase tracking-wider mt-4 mb-2"
            )
            with ui.card().classes("w-full rounded-xl border border-slate-200 overflow-hidden"):
                for k, v in custom.items():
                    with ui.row().classes(
                        "items-center px-4 py-2 border-b border-slate-50 last:border-0 gap-3"
                    ):
                        ui.label(k).classes(
                            "text-xs font-mono text-slate-500 w-40 shrink-0"
                        )
                        ui.label(v).classes("text-sm text-slate-700 flex-1")

                        def _del_custom(key: str = k) -> None:
                            Q.delete_job_metadata(job_type, job_id, key)
                            notify_success(f"Deleted {key}")
                            _render_editor(job_type, job_id, container)

                        ui.button("✕", on_click=_del_custom).props("flat dense").classes(
                            "text-red-400 text-xs"
                        )

        with ui.row().classes("justify-end gap-3 mt-6"):
            def _save_all() -> None:
                for key, inp in inp_map.items():
                    v = inp.value.strip()
                    if v:
                        Q.set_job_metadata(job_type, job_id, key, v)
                    else:
                        Q.delete_job_metadata(job_type, job_id, key)
                notify_success("Metadata saved")
                _render_editor(job_type, job_id, container)

            ui.button("Save All", on_click=_save_all).classes("bg-blue-600 text-white")


def metadata_editor_page(content_area: ui.element) -> None:
    """Render the metadata editor page."""
    content_area.clear()
    with content_area:
        section_header(
            "Metadata Editor",
            "Edit Dublin Core and custom metadata for any job",
        )

        # Job selector
        braille_jobs = Q.list_braille_jobs()
        lp_jobs = Q.list_lp_jobs()
        tactile_jobs = Q.list_tactile_jobs()

        opts: list[str] = []
        opt_map: dict[str, tuple[str, int]] = {}

        for j in braille_jobs:
            lbl = f"[Braille #{j['id']}] {j['title']}"
            opts.append(lbl)
            opt_map[lbl] = ("braille", j["id"])

        for j in lp_jobs:
            lbl = f"[LP #{j['id']}] {j['title']}"
            opts.append(lbl)
            opt_map[lbl] = ("lp_ebraille", j["id"])

        for j in tactile_jobs:
            lbl = f"[Tactile #{j['id']}] {j['title']}"
            opts.append(lbl)
            opt_map[lbl] = ("tactile", j["id"])

        if not opts:
            ui.label(
                "No jobs found. Create a braille, large print, eBraille, tactile graphics, or 3D print job first."
            ).classes("text-slate-400 text-sm")
            return

        job_sel = ui.select(opts, label="Select Job", value=opts[0]).classes("w-full max-w-xl")
        editor_container = ui.column().classes("w-full mt-4")

        jtype0, jid0 = opt_map[opts[0]]
        _render_editor(jtype0, jid0, editor_container)

        def _on_job_change(_: object) -> None:
            val = job_sel.value
            if val in opt_map:
                jt, ji = opt_map[val]
                _render_editor(jt, ji, editor_container)

        job_sel.on("update:model-value", _on_job_change)
