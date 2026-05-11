"""
Admin panel — manage material categories, workflow steps, and printers.

All data is persisted to SQLite via db.queries.
"""

from __future__ import annotations

from typing import Optional

from nicegui import ui

from ..db import queries as Q
from .components import confirm_dialog, notify_error, notify_success, section_header

SECTIONS = [
    ("paper_type",    "Paper Types"),
    ("elec_cat",      "Electronics Categories"),
    ("elec_unit",     "Electronics Units"),
    ("braille_type",  "Braille Types"),
    ("tactile_type",  "Tactile Graphics Types"),
    ("lp_type",       "Large Print / eBraille Types"),
    ("filament_type", "Filament Types"),
    ("diameter_mm",   "Filament Diameters"),
    ("priority",      "Job Priorities"),
    ("file_use",      "File Use Categories"),
]


# ── Material categories ───────────────────────────────────────────────────────

def _category_section(section_key: str, section_label: str, container: ui.element) -> None:
    container.clear()
    with container:
        items = Q.list_material_categories(section=section_key, active_only=False)

        with ui.row().classes("items-center mb-3"):
            ui.label(section_label).classes("text-base font-semibold text-slate-700 flex-1")

            def _add() -> None:
                _add_category_dialog(section_key, section_label, lambda: _category_section(
                    section_key, section_label, container
                ))

            ui.button("+ Add", on_click=_add).classes(
                "bg-blue-600 text-white text-sm rounded-lg px-3 py-1"
            )

        if not items:
            ui.label("No items. Click '+ Add' to create one.").classes(
                "text-slate-400 text-sm"
            )
            return

        with ui.card().classes("w-full rounded-xl border border-slate-200 overflow-hidden"):
            with ui.row().classes(
                "px-4 py-2 bg-slate-50 text-xs font-semibold text-slate-500 "
                "uppercase tracking-wider border-b"
            ):
                ui.label("Label").classes("flex-1")
                ui.label("Value").classes("w-40")
                ui.label("Order").classes("w-16 text-center")
                ui.label("Active").classes("w-16 text-center")
                ui.label("").classes("w-28")

            for item in items:
                active = bool(item.get("active", 1))
                row_bg = "" if active else "bg-slate-50 opacity-60"
                with ui.row().classes(
                    f"items-center px-4 py-2 border-b border-slate-50 last:border-0 gap-2 {row_bg}"
                ):
                    ui.label(item["label"]).classes("flex-1 text-sm text-slate-700")
                    ui.label(item["value"]).classes(
                        "w-40 text-xs font-mono text-slate-400"
                    )
                    ui.label(str(item.get("sort_order", 0))).classes(
                        "w-16 text-center text-sm text-slate-500"
                    )
                    ui.badge("✓" if active else "—").classes(
                        f"w-16 text-center text-xs rounded "
                        f"{'bg-green-100 text-green-700' if active else 'bg-slate-100 text-slate-400'}"
                    )
                    with ui.row().classes("w-28 gap-1 justify-end"):
                        def _toggle(it: dict = item, a: bool = active) -> None:
                            Q.set_material_category_active(it["id"], 0 if a else 1)
                            _category_section(section_key, section_label, container)

                        lbl = "Deactivate" if active else "Activate"
                        ui.button(lbl, on_click=_toggle).props("flat dense").classes(
                            "text-xs text-slate-500"
                        )

                        def _del(it: dict = item) -> None:
                            def _do() -> None:
                                Q.set_material_category_active(it["id"], 0)
                                _category_section(section_key, section_label, container)

                            confirm_dialog(
                                f"Deactivate '{it['label']}'? "
                                "(it will no longer appear in dropdowns)",
                                _do,
                            )

                        ui.button("✕", on_click=_del).props("flat dense").classes(
                            "text-red-400 text-xs"
                        )


def _add_category_dialog(section_key: str, section_label: str, refresh_cb) -> None:
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[420px] max-w-full"):
        ui.label(f"Add: {section_label}").classes("text-xl font-bold text-slate-800")

        label_inp = ui.input("Display Label*").classes("w-full")
        value_inp = ui.input("Value (slug, no spaces)*").classes("w-full")
        order_inp = ui.number("Sort Order", value=0, min=0).classes("w-full")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _save() -> None:
                lbl = label_inp.value.strip()
                val = value_inp.value.strip().replace(" ", "_")
                if not lbl or not val:
                    notify_error("Label and Value are required")
                    return
                try:
                    Q.add_material_category(
                        section=section_key,
                        value=val,
                        label=lbl,
                        sort_order=int(order_inp.value or 0),
                    )
                    notify_success(f"Added '{lbl}'")
                    dlg.close()
                    refresh_cb()
                except Exception as exc:
                    notify_error(f"Error: {exc}")

            ui.button("Save", on_click=_save).classes("bg-blue-600 text-white")

    dlg.open()


# ── Workflow steps ────────────────────────────────────────────────────────────

def _workflow_steps_section(container: ui.element) -> None:
    container.clear()
    with container:
        all_steps = Q.list_workflow_steps(active_only=False)
        by_type: dict[str, list] = {}
        for s in all_steps:
            by_type.setdefault(s["job_type"], []).append(s)

        with ui.row().classes("items-center mb-3"):
            ui.label("Workflow Steps").classes("text-base font-semibold text-slate-700 flex-1")

            def _add() -> None:
                _add_step_dialog(lambda: _workflow_steps_section(container))

            ui.button("+ Add Step", on_click=_add).classes(
                "bg-blue-600 text-white text-sm rounded-lg px-3 py-1"
            )

        for job_type, steps in by_type.items():
            ui.label(job_type.replace("_", " ").title()).classes(
                "text-xs font-semibold text-slate-400 uppercase tracking-wider mt-4 mb-1"
            )
            with ui.card().classes("w-full rounded-xl border border-slate-200 overflow-hidden"):
                with ui.row().classes(
                    "px-4 py-2 bg-slate-50 text-xs font-semibold text-slate-500 "
                    "uppercase tracking-wider border-b"
                ):
                    ui.label("Label").classes("flex-1")
                    ui.label("Key").classes("w-32")
                    ui.label("Order").classes("w-16 text-center")
                    ui.label("Active").classes("w-16 text-center")
                    ui.label("").classes("w-24")

                for step in steps:
                    active = bool(step.get("active", 1))
                    row_bg = "" if active else "bg-slate-50 opacity-60"
                    with ui.row().classes(
                        f"items-center px-4 py-2 border-b border-slate-50 "
                        f"last:border-0 gap-2 {row_bg}"
                    ):
                        ui.label(step["label"]).classes("flex-1 text-sm text-slate-700")
                        ui.label(step["step_key"]).classes(
                            "w-32 text-xs font-mono text-slate-400"
                        )
                        ui.label(str(step.get("sort_order", 0))).classes(
                            "w-16 text-center text-sm text-slate-500"
                        )
                        ui.badge("✓" if active else "—").classes(
                            f"w-16 text-center text-xs rounded "
                            f"{'bg-green-100 text-green-700' if active else 'bg-slate-100 text-slate-400'}"
                        )
                        with ui.row().classes("w-24 gap-1 justify-end"):
                            def _tog(s: dict = step, a: bool = active) -> None:
                                Q.set_workflow_step_active(s["id"], 0 if a else 1)
                                _workflow_steps_section(container)

                            ui.button(
                                "Deactivate" if active else "Activate", on_click=_tog
                            ).props("flat dense").classes("text-xs text-slate-500")


def _add_step_dialog(refresh_cb) -> None:
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[440px] max-w-full"):
        ui.label("Add Workflow Step").classes("text-xl font-bold text-slate-800")

        jt_opts = ["braille", "lp_ebraille", "tactile", "print"]
        jt_sel = ui.select(jt_opts, label="Job Type*", value="braille").classes("w-full")
        key_inp = ui.input("Step Key* (snake_case)").classes("w-full")
        lbl_inp = ui.input("Label*").classes("w-full")
        desc_inp = ui.textarea("Description").classes("w-full").props("rows=2")
        ord_inp = ui.number("Sort Order", value=0, min=0).classes("w-full")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _save() -> None:
                k = key_inp.value.strip().replace(" ", "_").lower()
                lbl = lbl_inp.value.strip()
                if not k or not lbl:
                    notify_error("Key and Label are required")
                    return
                try:
                    Q.add_workflow_step(
                        job_type=jt_sel.value,
                        step_key=k,
                        label=lbl,
                        description=desc_inp.value.strip(),
                        sort_order=int(ord_inp.value or 0),
                    )
                    notify_success(f"Added step '{lbl}'")
                    dlg.close()
                    refresh_cb()
                except Exception as exc:
                    notify_error(f"Error: {exc}")

            ui.button("Save", on_click=_save).classes("bg-blue-600 text-white")

    dlg.open()


# ── Printers ──────────────────────────────────────────────────────────────────

def _printers_section(container: ui.element) -> None:
    container.clear()
    with container:
        printers = Q.list_printers()

        with ui.row().classes("items-center mb-3"):
            ui.label("Printers").classes("text-base font-semibold text-slate-700 flex-1")

            def _add() -> None:
                _add_printer_dialog(lambda: _printers_section(container))

            ui.button("+ Add Printer", on_click=_add).classes(
                "bg-blue-600 text-white text-sm rounded-lg px-3 py-1"
            )

        if not printers:
            ui.label("No printers configured.").classes("text-slate-400 text-sm")
            return

        with ui.card().classes("w-full rounded-xl border border-slate-200 overflow-hidden"):
            with ui.row().classes(
                "px-4 py-2 bg-slate-50 text-xs font-semibold text-slate-500 "
                "uppercase tracking-wider border-b"
            ):
                ui.label("Name").classes("flex-1")
                ui.label("Model").classes("w-40")
                ui.label("").classes("w-32")

            for p in printers:
                with ui.row().classes(
                    "items-center px-4 py-2 border-b border-slate-50 last:border-0 gap-2"
                ):
                    ui.label(p["name"]).classes("flex-1 text-sm text-slate-700")
                    ui.label(p.get("model") or "—").classes(
                        "w-40 text-sm text-slate-400"
                    )
                    with ui.row().classes("w-32 gap-1 justify-end"):
                        def _edit(pr: dict = p) -> None:
                            _edit_printer_dialog(pr, lambda: _printers_section(container))

                        ui.button("Edit", on_click=_edit).props("flat dense").classes(
                            "text-blue-600 text-xs"
                        )

                        def _del(pr: dict = p) -> None:
                            import sqlite3

                            def _do() -> None:
                                try:
                                    Q.delete_printer(pr["id"])
                                    notify_success("Printer deleted")
                                    _printers_section(container)
                                except sqlite3.IntegrityError:
                                    notify_error(
                                        "Cannot delete: this printer has associated print jobs. "
                                        "Delete those jobs first."
                                    )

                            confirm_dialog(f"Delete printer '{pr['name']}'?", _do)

                        ui.button("✕", on_click=_del).props("flat dense").classes(
                            "text-red-400 text-xs"
                        )


def _add_printer_dialog(refresh_cb) -> None:
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[400px] max-w-full"):
        ui.label("Add Printer").classes("text-xl font-bold text-slate-800")
        name_inp = ui.input("Printer Name*").classes("w-full")
        model_inp = ui.input("Model").classes("w-full")
        notes_inp = ui.textarea("Notes").classes("w-full").props("rows=2")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _save() -> None:
                nm = name_inp.value.strip()
                if not nm:
                    notify_error("Printer Name is required")
                    return
                try:
                    Q.add_printer(nm, model_inp.value.strip(), notes_inp.value.strip())
                    notify_success(f"Added printer '{nm}'")
                    dlg.close()
                    refresh_cb()
                except Exception as exc:
                    notify_error(f"Error: {exc}")

            ui.button("Save", on_click=_save).classes("bg-blue-600 text-white")

    dlg.open()


def _edit_printer_dialog(printer: dict, refresh_cb) -> None:
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[400px] max-w-full"):
        ui.label("Edit Printer").classes("text-xl font-bold text-slate-800")
        name_inp = ui.input("Printer Name*", value=printer.get("name", "")).classes("w-full")
        model_inp = ui.input("Model", value=printer.get("model") or "").classes("w-full")
        notes_inp = ui.textarea("Notes", value=printer.get("notes") or "").classes(
            "w-full"
        ).props("rows=2")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _save() -> None:
                nm = name_inp.value.strip()
                if not nm:
                    notify_error("Printer Name is required")
                    return
                try:
                    Q.update_printer(
                        printer["id"],
                        name=nm,
                        model=model_inp.value.strip(),
                        notes=notes_inp.value.strip(),
                    )
                    notify_success("Printer updated")
                    dlg.close()
                    refresh_cb()
                except Exception as exc:
                    notify_error(f"Error: {exc}")

            ui.button("Save", on_click=_save).classes("bg-blue-600 text-white")

    dlg.open()


def _embossers_section(container: ui.element) -> None:
    container.clear()
    with container:
        embossers = Q.list_embossers()
        with ui.row().classes("items-center mb-3"):
            ui.label("Embossers").classes("text-base font-semibold text-slate-700 flex-1")

            def _add() -> None:
                _add_embosser_dialog(lambda: _embossers_section(container))

            ui.button("+ Add Embosser", on_click=_add).classes(
                "bg-blue-600 text-white text-sm rounded-lg px-3 py-1"
            )

        if not embossers:
            ui.label("No embossers configured.").classes("text-slate-400 text-sm")
            return

        with ui.card().classes("w-full rounded-xl border border-slate-200 overflow-hidden"):
            with ui.row().classes(
                "px-4 py-2 bg-slate-50 text-xs font-semibold text-slate-500 "
                "uppercase tracking-wider border-b"
            ):
                ui.label("Name").classes("flex-1")
                ui.label("Model").classes("w-36")
                ui.label("Paper Feed").classes("w-40")
                ui.label("").classes("w-32")

            for emb in embossers:
                with ui.row().classes(
                    "items-center px-4 py-2 border-b border-slate-50 last:border-0 gap-2"
                ):
                    ui.label(emb["name"]).classes("flex-1 text-sm text-slate-700")
                    ui.label(emb.get("model") or "—").classes("w-36 text-sm text-slate-400")
                    ui.label((emb.get("paper_type") or "—").replace("_", " ").title()).classes(
                        "w-40 text-sm text-slate-500"
                    )
                    with ui.row().classes("w-32 gap-1 justify-end"):
                        def _edit(em: dict = emb) -> None:
                            _edit_embosser_dialog(em, lambda: _embossers_section(container))

                        ui.button("Edit", on_click=_edit).props("flat dense").classes(
                            "text-blue-600 text-xs"
                        )

                        def _del(em: dict = emb) -> None:
                            import sqlite3

                            def _do() -> None:
                                try:
                                    Q.delete_embosser(em["id"])
                                    notify_success("Embosser deleted")
                                    _embossers_section(container)
                                except sqlite3.IntegrityError:
                                    notify_error(
                                        "Cannot delete: this embosser is assigned to braille jobs."
                                    )

                            confirm_dialog(f"Delete embosser '{em['name']}'?", _do)

                        ui.button("✕", on_click=_del).props("flat dense").classes(
                            "text-red-400 text-xs"
                        )


def _add_embosser_dialog(refresh_cb) -> None:
    paper_types = Q.list_material_categories("paper_type")
    paper_labels = [p["label"] for p in paper_types]
    paper_values = [p["value"] for p in paper_types]

    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[420px] max-w-full"):
        ui.label("Add Embosser").classes("text-xl font-bold text-slate-800")
        name_inp = ui.input("Embosser Name*").classes("w-full")
        model_inp = ui.input("Model").classes("w-full")
        paper_sel = ui.select(
            paper_labels or ["(no paper types)"],
            label="Paper Feed Type",
            value=paper_labels[0] if paper_labels else "(no paper types)",
        ).classes("w-full")
        notes_inp = ui.textarea("Notes").classes("w-full").props("rows=2")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _save() -> None:
                name = name_inp.value.strip()
                if not name:
                    notify_error("Embosser Name is required")
                    return
                paper_type = ""
                if paper_types:
                    try:
                        paper_type = paper_values[paper_labels.index(paper_sel.value)]
                    except (ValueError, IndexError):
                        paper_type = ""
                Q.add_embosser(name, model_inp.value.strip(), paper_type, notes_inp.value.strip())
                notify_success(f"Added embosser '{name}'")
                dlg.close()
                refresh_cb()

            ui.button("Save", on_click=_save).classes("bg-blue-600 text-white")

    dlg.open()


def _edit_embosser_dialog(embosser: dict, refresh_cb) -> None:
    paper_types = Q.list_material_categories("paper_type")
    paper_labels = [p["label"] for p in paper_types]
    paper_values = [p["value"] for p in paper_types]
    current_value = embosser.get("paper_type") or ""
    current_label = paper_labels[paper_values.index(current_value)] if current_value in paper_values else (paper_labels[0] if paper_labels else "")

    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[420px] max-w-full"):
        ui.label("Edit Embosser").classes("text-xl font-bold text-slate-800")
        name_inp = ui.input("Embosser Name*", value=embosser.get("name", "")).classes("w-full")
        model_inp = ui.input("Model", value=embosser.get("model") or "").classes("w-full")
        paper_sel = ui.select(paper_labels or ["(no paper types)"], label="Paper Feed Type", value=current_label).classes("w-full")
        notes_inp = ui.textarea("Notes", value=embosser.get("notes") or "").classes("w-full").props("rows=2")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _save() -> None:
                name = name_inp.value.strip()
                if not name:
                    notify_error("Embosser Name is required")
                    return
                paper_type = ""
                if paper_types:
                    try:
                        paper_type = paper_values[paper_labels.index(paper_sel.value)]
                    except (ValueError, IndexError):
                        paper_type = current_value
                Q.update_embosser(
                    embosser["id"],
                    name=name,
                    model=model_inp.value.strip(),
                    paper_type=paper_type,
                    notes=notes_inp.value.strip(),
                )
                notify_success("Embosser updated")
                dlg.close()
                refresh_cb()

            ui.button("Save", on_click=_save).classes("bg-blue-600 text-white")

    dlg.open()


# ── Main admin page ───────────────────────────────────────────────────────────

def admin_page(content_area: ui.element) -> None:
    """Render the admin settings page."""
    content_area.clear()
    with content_area:
        section_header(
            "Admin Settings",
            "Manage material categories, workflow steps, printers, and embossers",
        )

        with ui.tabs().classes("w-full") as tabs:
            tab_cats = ui.tab("Material Categories")
            tab_steps = ui.tab("Workflow Steps")
            tab_printers = ui.tab("Printers")
            tab_embossers = ui.tab("Embossers")

        with ui.tab_panels(tabs, value=tab_cats).classes("w-full mt-4"):
            with ui.tab_panel(tab_cats):
                # Section selector
                section_labels = [s[1] for s in SECTIONS]
                section_keys = [s[0] for s in SECTIONS]
                sel = ui.select(
                    section_labels,
                    value=section_labels[0],
                    label="Category Section",
                ).classes("w-72 mb-4")

                cat_container = ui.column().classes("w-full")
                _category_section(section_keys[0], section_labels[0], cat_container)

                def _on_section_change(e: object) -> None:
                    try:
                        idx = section_labels.index(sel.value)
                    except ValueError:
                        return
                    _category_section(section_keys[idx], section_labels[idx], cat_container)

                sel.on("update:model-value", _on_section_change)

            with ui.tab_panel(tab_steps):
                step_container = ui.column().classes("w-full")
                _workflow_steps_section(step_container)

            with ui.tab_panel(tab_printers):
                printer_container = ui.column().classes("w-full")
                _printers_section(printer_container)

            with ui.tab_panel(tab_embossers):
                embosser_container = ui.column().classes("w-full")
                _embossers_section(embosser_container)
