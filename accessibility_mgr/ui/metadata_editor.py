"""
Metadata editor — edit and inspect Dublin Core and custom metadata for any job.
"""

from __future__ import annotations

from nicegui import ui

from ..db import queries as Q
from .metadata_options import (
    get_dublin_core_examples,
    get_dublin_core_keys,
    get_non_dc_allowed_keys,
    get_option_groups,
)
from .components import notify_success, section_header


def _render_editor(job_type: str, job_id: int, container: ui.element) -> None:
    """ render editor.
    
    Parameters
    ----------
    job_type : Any
        job_type parameter.
    
    job_id : Any
        job_id parameter.
    
    container : Any
        container parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    container.clear()
    existing = Q.list_job_metadata(job_type, job_id)
    option_groups = get_option_groups()
    dc_keys = get_dublin_core_keys()
    dc_examples = get_dublin_core_examples()
    non_dc_keys = get_non_dc_allowed_keys()

    with container:
        ui.label(f"Editing metadata for {job_type} job #{job_id}").classes(
            "text-sm font-semibold text-slate-600 mb-3"
        )

        def _show_options() -> None:
            """ show options.
            
            Returns
            -------
            Any
                Function result.
            
            """
            with ui.dialog() as od, ui.card().classes(
                "p-5 gap-3 w-[720px] max-w-full max-h-[85vh] overflow-y-auto"
            ):
                ui.label("Potential Metadata Options").classes("text-lg font-bold text-slate-800")
                ui.label(
                    "Use Admin Settings -> Metadata Options to add or remove allowed keys."
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
            "text-indigo-600 text-sm self-start mb-1"
        )

        inp_map: dict[str, ui.input] = {}

        with ui.grid(columns=2).classes("w-full gap-3"):
            for key in dc_keys:
                with ui.column().classes("gap-0"):
                    inp = ui.input(key, value=existing.get(key, "")).classes(
                        "w-full font-mono text-sm"
                    )
                    ui.label(dc_examples.get(key, "")).classes(
                        "text-[11px] text-slate-400"
                    )
                    inp_map[key] = inp

        # Additional controlled keys
        ui.separator().classes("my-4")
        ui.label("Additional Allowed Fields").classes(
            "text-sm font-medium text-slate-600 mb-2"
        )
        ui.label(
            "Choose keys from the approved eBraille and METS/PREMIS list."
        ).classes("text-xs text-slate-400 mb-1")

        extra_rows: list[dict[str, ui.element]] = []
        extra_box = ui.column().classes("w-full gap-2")

        def _add_extra_row(initial_key: str = "", initial_val: str = "") -> None:
            """ add extra row.
            
            Parameters
            ----------
            initial_key : Any
                initial_key parameter.
            
            initial_val : Any
                initial_val parameter.
            
            Returns
            -------
            Any
                Function result.
            
            """
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
                        """ remove.
                        
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
                        if r in extra_rows:
                            extra_rows.remove(r)

                    ui.button("✕", on_click=_remove).props("flat dense").classes("text-red-400")

        ui.button("+ Add Field", on_click=lambda: _add_extra_row()).props("flat dense").classes(
            "text-indigo-600 text-sm self-start"
        )

        for key, value in existing.items():
            if key not in dc_keys and key in non_dc_keys:
                _add_extra_row(initial_key=key, initial_val=value)

        with ui.row().classes("justify-end gap-3 mt-6"):
            def _save_all() -> None:
                """ save all.
                
                Returns
                -------
                Any
                    Function result.
                
                """
                for key, inp in inp_map.items():
                    v = inp.value.strip()
                    if v:
                        Q.set_job_metadata(job_type, job_id, key, v)
                    else:
                        Q.delete_job_metadata(job_type, job_id, key)

                for key in non_dc_keys:
                    Q.delete_job_metadata(job_type, job_id, key)
                for row in extra_rows:
                    k = (row["key"].value or "").strip()
                    v = (row["value"].value or "").strip()
                    if k and v and k in non_dc_keys:
                        Q.set_job_metadata(job_type, job_id, k, v)

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
        print_jobs = Q.list_print_jobs()

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

        for j in print_jobs:
            obj = j.get("object_name") or j.get("file_name") or "Untitled"
            lbl = f"[Print #{j['id']}] {obj}"
            opts.append(lbl)
            opt_map[lbl] = ("print", j["id"])

        if not opts:
            ui.label(
                "No jobs found. Create a braille, large print, eBraille, EPUB3/DAISY, tactile graphics, or 3-D print job first."
            ).classes("text-slate-400 text-sm")
            return

        job_sel = ui.select(opts, label="Select Job", value=opts[0]).classes("w-full max-w-xl")
        editor_container = ui.column().classes("w-full mt-4")

        jtype0, jid0 = opt_map[opts[0]]
        _render_editor(jtype0, jid0, editor_container)

        def _on_job_change(_: object) -> None:
            """ on job change.
            
            Parameters
            ----------
            _ : Any
                _ parameter.
            
            Returns
            -------
            Any
                Function result.
            
            """
            val = job_sel.value
            if val in opt_map:
                jt, ji = opt_map[val]
                _render_editor(jt, ji, editor_container)

        job_sel.on("update:model-value", _on_job_change)
