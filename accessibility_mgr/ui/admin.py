"""
Admin panel — manage material categories, workflow steps, printers, embossers,
metadata options, and database backups.

Changes applied (see fix_specs.json):
  FIX-013  Backups tab added: shows scheduler status, recent backup log,
           and a manual "Run Backup Now" button.
  FIX-017  Metadata key backfill now shows a dry-run preview dialog before
           executing, listing proposed key mappings and skipped keys.
"""

from __future__ import annotations

import threading
from typing import Optional

from nicegui import ui

from ..db import queries as Q
from .metadata_options import (
    METADATA_CATEGORY_SECTIONS,
    get_allowed_metadata_keys,
)
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
    ("delivery_method", "Delivery Methods"),
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
                    ui.label(item["value"]).classes("w-40 text-xs font-mono text-slate-400")
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
                    ui.label(p.get("model") or "—").classes("w-40 text-sm text-slate-400")
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
                                        "Cannot delete: this printer has associated print jobs."
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


# ── Embossers ─────────────────────────────────────────────────────────────────

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
                    ui.label(
                        (emb.get("paper_type") or "—").replace("_", " ").title()
                    ).classes("w-40 text-sm text-slate-500")
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
    current_label = (
        paper_labels[paper_values.index(current_value)]
        if current_value in paper_values
        else (paper_labels[0] if paper_labels else "")
    )

    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[420px] max-w-full"):
        ui.label("Edit Embosser").classes("text-xl font-bold text-slate-800")
        name_inp = ui.input("Embosser Name*", value=embosser.get("name", "")).classes("w-full")
        model_inp = ui.input("Model", value=embosser.get("model") or "").classes("w-full")
        paper_sel = ui.select(
            paper_labels or ["(no paper types)"],
            label="Paper Feed Type",
            value=current_label,
        ).classes("w-full")
        notes_inp = ui.textarea("Notes", value=embosser.get("notes") or "").classes(
            "w-full"
        ).props("rows=2")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _save() -> None:
                name = name_inp.value.strip()
                if not name:
                    notify_error("Embosser Name is required")
                    return
                paper_type = current_value
                if paper_types:
                    try:
                        paper_type = paper_values[paper_labels.index(paper_sel.value)]
                    except (ValueError, IndexError):
                        pass
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


# ── Metadata options (FIX-017: dry-run preview) ───────────────────────────────

def _metadata_options_section(container: ui.element) -> None:
    container.clear()
    with container:
        approved_keys = set(get_allowed_metadata_keys())
        all_keys = Q.list_distinct_metadata_keys()
        unknown_keys = [r for r in all_keys if r.get("meta_key") not in approved_keys]

        with ui.row().classes("items-center mb-3 w-full"):
            ui.label("Metadata Options").classes(
                "text-base font-semibold text-slate-700 flex-1"
            )

            def _run_backfill() -> None:
                # FIX-017: show dry-run preview before executing
                preview = Q.preview_backfill_metadata_keys(list(approved_keys))
                mappings = preview["mappings"]
                skipped = preview["skipped_keys"]
                counts = preview["usage_counts"]

                if not mappings and not skipped:
                    notify_success("No non-approved keys found — nothing to backfill.")
                    return

                with ui.dialog() as prev_dlg, ui.card().classes(
                    "p-6 gap-4 w-[640px] max-w-full max-h-[85vh] overflow-y-auto"
                ):
                    ui.label("Backfill Preview").classes("text-xl font-bold text-slate-800")
                    ui.label(
                        "Review the proposed key renames below. "
                        "Click Confirm to apply or Cancel to abort."
                    ).classes("text-sm text-slate-500 mb-2")

                    if mappings:
                        ui.label("Proposed renames").classes(
                            "text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1"
                        )
                        with ui.card().classes(
                            "w-full rounded-xl border border-slate-200 overflow-hidden mb-3"
                        ):
                            with ui.row().classes(
                                "px-4 py-2 bg-slate-50 text-xs font-semibold text-slate-500 "
                                "uppercase tracking-wider border-b"
                            ):
                                ui.label("Current Key").classes("flex-1")
                                ui.label("→ Approved Key").classes("flex-1")
                                ui.label("Uses").classes("w-16 text-right")
                            for src, tgt in mappings.items():
                                with ui.row().classes(
                                    "items-center px-4 py-2 border-b border-slate-50 last:border-0 gap-2"
                                ):
                                    ui.label(src).classes(
                                        "flex-1 text-xs font-mono text-amber-700"
                                    )
                                    ui.label(tgt).classes(
                                        "flex-1 text-xs font-mono text-green-700"
                                    )
                                    ui.label(str(counts.get(src, "?"))).classes(
                                        "w-16 text-right text-xs text-slate-400"
                                    )

                    if skipped:
                        ui.label(
                            f"{len(skipped)} key(s) could not be matched — they will be left unchanged:"
                        ).classes("text-xs text-amber-600 mt-2 mb-1")
                        with ui.row().classes("gap-2 flex-wrap"):
                            for k in skipped:
                                ui.badge(k).classes(
                                    "text-xs bg-amber-100 text-amber-800 rounded px-2"
                                )

                    with ui.row().classes("justify-end gap-3 mt-4"):
                        ui.button("Cancel", on_click=prev_dlg.close).props("flat").classes(
                            "text-slate-500"
                        )

                        def _confirm() -> None:
                            result = Q.backfill_metadata_keys(list(approved_keys))
                            notify_success(
                                f"Backfill complete: "
                                f"updated {result.get('updated_rows', 0)}, "
                                f"deleted {result.get('deleted_rows', 0)}"
                            )
                            prev_dlg.close()
                            _metadata_options_section(container)

                        ui.button("Confirm Backfill", on_click=_confirm).classes(
                            "bg-amber-600 text-white"
                        )

                prev_dlg.open()

            ui.button("Backfill Typo Keys", on_click=_run_backfill).classes(
                "bg-amber-600 text-white text-sm rounded-lg px-3 py-1"
            )

        ui.label(
            "These keys populate all metadata dropdowns. Changes apply app-wide."
        ).classes("text-xs text-slate-500 mb-2")

        if unknown_keys:
            with ui.card().classes(
                "w-full rounded-xl border border-amber-200 bg-amber-50 p-3 mb-4"
            ):
                ui.label("Detected non-approved keys in existing metadata").classes(
                    "text-xs font-semibold text-amber-700 uppercase tracking-wider mb-2"
                )
                with ui.row().classes("gap-2 flex-wrap"):
                    for item in unknown_keys:
                        ui.badge(f"{item['meta_key']} ({item['usage_count']})").classes(
                            "text-xs bg-amber-100 text-amber-800"
                        )
        else:
            ui.label("No non-approved metadata keys detected.").classes(
                "text-xs text-slate-500 mb-4"
            )

        section_labels = list(METADATA_CATEGORY_SECTIONS.keys())
        sec_sel = ui.select(
            section_labels, value=section_labels[0], label="Metadata Group"
        ).classes("w-72 mb-3")

        list_container = ui.column().classes("w-full")

        def _render_group() -> None:
            list_container.clear()
            group = sec_sel.value
            section = METADATA_CATEGORY_SECTIONS[group]
            items = Q.list_material_categories(section=section, active_only=False)

            with list_container:
                with ui.row().classes("items-center mb-2"):
                    ui.label(group).classes("text-sm font-semibold text-slate-700 flex-1")

                    def _add() -> None:
                        _add_metadata_option_dialog(group, section, _render_group)

                    ui.button("+ Add Key", on_click=_add).classes(
                        "bg-blue-600 text-white text-sm rounded-lg px-3 py-1"
                    )

                with ui.card().classes("w-full rounded-xl border border-slate-200 overflow-hidden"):
                    with ui.row().classes(
                        "px-4 py-2 bg-slate-50 text-xs font-semibold text-slate-500 "
                        "uppercase tracking-wider border-b"
                    ):
                        ui.label("Key").classes("flex-1")
                        ui.label("Label").classes("w-56")
                        ui.label("Order").classes("w-16 text-center")
                        ui.label("Active").classes("w-16 text-center")
                        ui.label("").classes("w-28")

                    for item in items:
                        active = bool(item.get("active", 1))
                        row_bg = "" if active else "bg-slate-50 opacity-60"
                        with ui.row().classes(
                            f"items-center px-4 py-2 border-b border-slate-50 last:border-0 gap-2 {row_bg}"
                        ):
                            ui.label(item["value"]).classes(
                                "flex-1 text-xs font-mono text-slate-600"
                            )
                            ui.label(item["label"]).classes(
                                "w-56 text-sm text-slate-700 truncate"
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
                                    _render_group()

                                ui.button(
                                    "Deactivate" if active else "Activate", on_click=_toggle
                                ).props("flat dense").classes("text-xs text-slate-500")

        sec_sel.on("update:model-value", lambda _: _render_group())
        _render_group()


def _add_metadata_option_dialog(group_label: str, section: str, refresh_cb) -> None:
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[460px] max-w-full"):
        ui.label(f"Add Metadata Key: {group_label}").classes("text-xl font-bold text-slate-800")
        key_inp = ui.input(
            "Metadata Key*", placeholder="e.g. dc:audience or premis:event_detail"
        ).classes("w-full")
        label_inp = ui.input(
            "Display Label", placeholder="defaults to key if empty"
        ).classes("w-full")
        order_inp = ui.number("Sort Order", value=0, min=0).classes("w-full")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _save() -> None:
                key = key_inp.value.strip()
                if not key:
                    notify_error("Metadata key is required")
                    return
                key = key.replace(" ", "_")
                label = label_inp.value.strip() or key
                try:
                    Q.add_material_category(
                        section=section,
                        value=key,
                        label=label,
                        sort_order=int(order_inp.value or 0),
                    )
                    notify_success(f"Added metadata key '{key}'")
                    dlg.close()
                    refresh_cb()
                except Exception as exc:
                    notify_error(f"Error: {exc}")

            ui.button("Save", on_click=_save).classes("bg-blue-600 text-white")

    dlg.open()


# ── Backups (FIX-013) ─────────────────────────────────────────────────────────

def _backup_section(container: ui.element) -> None:
    container.clear()
    with container:
        from ..services.backup_service import BackupService

        status = BackupService.status()

        with ui.card().classes("w-full p-5 rounded-xl border border-slate-200 mb-4"):
            ui.label("Backup Status").classes("text-base font-semibold text-slate-700 mb-3")

            with ui.grid(columns=3).classes("gap-4 w-full"):
                with ui.card().classes("p-4 bg-slate-50 border border-slate-200 rounded-xl"):
                    ui.label("Scheduler").classes("text-xs text-slate-500")
                    active = status.get("scheduler_active", False)
                    ui.badge("Active" if active else "Stopped").classes(
                        f"text-sm font-semibold mt-1 "
                        f"{'bg-green-100 text-green-700' if active else 'bg-red-100 text-red-700'} "
                        f"rounded px-2"
                    )

                with ui.card().classes("p-4 bg-slate-50 border border-slate-200 rounded-xl"):
                    ui.label("Backups Stored").classes("text-xs text-slate-500")
                    ui.label(str(status.get("backup_count", 0))).classes(
                        "text-2xl font-bold text-slate-700 mt-1"
                    )
                    ui.label(f"Max {status.get('retention_limit', 10)} retained").classes(
                        "text-xs text-slate-400"
                    )

                with ui.card().classes("p-4 bg-slate-50 border border-slate-200 rounded-xl"):
                    ui.label("Interval").classes("text-xs text-slate-500")
                    ui.label(f"Every {status.get('interval_days', 7)} days").classes(
                        "text-sm font-semibold text-slate-700 mt-1"
                    )

            ui.label("Latest Backup").classes(
                "text-xs font-semibold text-slate-500 uppercase tracking-wider mt-4 mb-1"
            )
            latest = status.get("latest_backup", "none")
            size = status.get("latest_size_bytes", 0)
            if latest == "none":
                ui.label("No backups yet.").classes("text-sm text-slate-400")
            else:
                ui.label(latest).classes("text-xs font-mono text-slate-600")
                ui.label(
                    f"{size / 1_048_576:.2f} MB" if size >= 1_048_576
                    else f"{size // 1024} KB" if size >= 1024
                    else f"{size} B"
                ).classes("text-xs text-slate-400")

            ui.label(f"Backups directory: {status.get('backups_dir', '')}").classes(
                "text-xs text-slate-400 mt-1"
            )

        # Manual backup button
        backup_status_label = ui.label("").classes("text-sm text-slate-500")

        def _run_backup_now() -> None:
            backup_status_label.set_text("Running backup…")

            def _do() -> None:
                try:
                    path = BackupService.run_backup(trigger="manual")
                    backup_status_label.set_text(f"✅ Backup complete: {path}")
                    _backup_section(container)
                except Exception as exc:
                    backup_status_label.set_text(f"❌ Backup failed: {exc}")

            threading.Thread(target=_do, daemon=True).start()

        ui.button("Run Backup Now", on_click=_run_backup_now).classes(
            "bg-slate-700 text-white rounded-lg px-4 py-2 mb-2"
        )

        # Recent backup log
        ui.label("Recent Backup Log").classes(
            "text-xs font-semibold text-slate-500 uppercase tracking-wider mt-4 mb-2"
        )
        recent = Q.list_backup_log(limit=20)
        if not recent:
            ui.label("No backup log entries yet.").classes("text-slate-400 text-sm")
        else:
            with ui.card().classes("w-full rounded-xl border border-slate-200 overflow-hidden"):
                with ui.row().classes(
                    "px-4 py-2 bg-slate-50 text-xs font-semibold text-slate-500 "
                    "uppercase tracking-wider border-b"
                ):
                    ui.label("Timestamp").classes("w-36")
                    ui.label("Trigger").classes("w-24")
                    ui.label("Status").classes("w-20")
                    ui.label("Size").classes("w-20 text-right")
                    ui.label("Path").classes("flex-1")

                for entry in recent:
                    ok = entry.get("status") == "ok"
                    sz = entry.get("size_bytes") or 0
                    sz_str = (
                        f"{sz / 1_048_576:.2f} MB" if sz >= 1_048_576
                        else f"{sz // 1024} KB" if sz >= 1024
                        else f"{sz} B"
                    )
                    with ui.row().classes(
                        "items-center px-4 py-2 border-b border-slate-50 last:border-0 gap-2"
                    ):
                        ui.label(str(entry.get("created_at", ""))[:19]).classes(
                            "w-36 text-xs font-mono text-slate-400"
                        )
                        ui.label(entry.get("trigger", "—")).classes(
                            "w-24 text-xs text-slate-500"
                        )
                        ui.badge("✓ ok" if ok else "✗ fail").classes(
                            f"w-20 text-center text-xs rounded "
                            f"{'bg-green-100 text-green-700' if ok else 'bg-red-100 text-red-700'}"
                        )
                        ui.label(sz_str).classes("w-20 text-right text-xs text-slate-500")
                        ui.label(entry.get("backup_path", "—")).classes(
                            "flex-1 text-xs font-mono text-slate-400 truncate"
                        )


# ── Main admin page ───────────────────────────────────────────────────────────

def admin_page(content_area: ui.element) -> None:
    """Render the admin settings page."""
    content_area.clear()
    with content_area:
        section_header(
            "Admin Settings",
            "Manage material categories, metadata options, workflow steps, "
            "printers, embossers, and database backups",
        )

        with ui.tabs().classes("w-full") as tabs:
            tab_cats     = ui.tab("Material Categories")
            tab_steps    = ui.tab("Workflow Steps")
            tab_printers = ui.tab("Printers")
            tab_emboss   = ui.tab("Embossers")
            tab_meta     = ui.tab("Metadata Options")
            tab_backups  = ui.tab("Backups")   # FIX-013

        with ui.tab_panels(tabs, value=tab_cats).classes("w-full mt-4"):
            with ui.tab_panel(tab_cats):
                section_labels = [s[1] for s in SECTIONS]
                section_keys   = [s[0] for s in SECTIONS]
                sel = ui.select(
                    section_labels, value=section_labels[0], label="Category Section"
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

            with ui.tab_panel(tab_emboss):
                embosser_container = ui.column().classes("w-full")
                _embossers_section(embosser_container)

            with ui.tab_panel(tab_meta):
                metadata_container = ui.column().classes("w-full")
                _metadata_options_section(metadata_container)

            with ui.tab_panel(tab_backups):   # FIX-013
                backup_container = ui.column().classes("w-full")
                _backup_section(backup_container)
