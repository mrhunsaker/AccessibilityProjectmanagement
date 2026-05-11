"""
Inventory panels — Filament, Braille Paper, Electronics.

These replace the old models/inventory.py (which was mistakenly used as a UI file)
and the partial ui/inventory.py stub.
"""

from __future__ import annotations

from typing import Optional

from nicegui import ui

import db.queries as Q
from ui.components import (
    confirm_dialog, notify_error, notify_success, section_header,
)


def _text_value(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


# ── Filament ──────────────────────────────────────────────────────────────────

def _filament_dialog(on_save, existing: Optional[dict] = None) -> None:
    is_edit = existing is not None
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[500px] max-w-full"):
        ui.label("Edit Filament" if is_edit else "Add Filament").classes(
            "text-xl font-bold text-slate-800"
        )

        with ui.row().classes("gap-4 w-full"):
            brand = ui.input(
                "Brand*", value=existing.get("brand", "") if is_edit else ""
            ).classes("flex-1")
            color = ui.input(
                "Color*", value=existing.get("color", "") if is_edit else ""
            ).classes("flex-1")

        types = [r["label"] for r in Q.list_material_categories("filament_type")]
        tvals = [r["value"] for r in Q.list_material_categories("filament_type")]
        cur_t = existing.get("filament_type", "PLA") if is_edit else "PLA"
        try:
            cur_tl = types[tvals.index(cur_t)]
        except ValueError:
            cur_tl = types[0] if types else "PLA"
        ft_sel = ui.select(types, label="Type*", value=cur_tl).classes("w-full")

        diams = [r["label"] for r in Q.list_material_categories("diameter_mm")]
        dvals = [r["value"] for r in Q.list_material_categories("diameter_mm")]
        cur_d = str(existing.get("diameter_mm", 1.75)) if is_edit else "1.75"
        try:
            cur_dl = diams[dvals.index(cur_d)]
        except ValueError:
            cur_dl = diams[0] if diams else "1.75 mm"
        diam_sel = ui.select(diams, label="Diameter", value=cur_dl).classes("w-full")

        with ui.row().classes("gap-4 w-full"):
            qty = ui.number(
                "Qty (g)*", value=existing.get("quantity_g", 0) if is_edit else 0, min=0
            ).classes("flex-1")
            cpk = ui.number(
                "Cost/kg ($)", value=existing.get("cost_per_kg") or 0, min=0
            ).classes("flex-1")

        supplier = ui.input(
            "Supplier", value=existing.get("supplier", "") if is_edit else ""
        ).classes("w-full")
        notes = ui.textarea(
            "Notes", value=existing.get("notes", "") if is_edit else ""
        ).classes("w-full").props("rows=2")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _save() -> None:
                if not brand.value.strip() or not color.value.strip():
                    notify_error("Brand and Color are required")
                    return
                try:
                    ft_val = tvals[types.index(ft_sel.value)]
                except (ValueError, IndexError):
                    ft_val = "PLA"
                try:
                    d_val = float(dvals[diams.index(diam_sel.value)])
                except (ValueError, IndexError):
                    d_val = 1.75
                on_save(
                    dict(
                        brand=brand.value.strip(),
                        color=color.value.strip(),
                        filament_type=ft_val,
                        diameter_mm=d_val,
                        quantity_g=float(qty.value or 0),
                        cost_per_kg=float(cpk.value) if cpk.value else None,
                        supplier=supplier.value.strip(),
                        notes=notes.value.strip(),
                    )
                )
                dlg.close()

            ui.button("Save", on_click=_save).classes("bg-blue-600 text-white")

    dlg.open()


def filament_page(content_area: ui.element) -> None:
    content_area.clear()
    with content_area:
        with ui.row().classes("items-center mb-4"):
            section_header("Filament Inventory", "Track 3-D printer filament stock")
            ui.element("div").classes("flex-1")

            def _new() -> None:
                def _do(data: dict) -> None:
                    Q.add_filament(**data)
                    notify_success("Filament added")
                    filament_page(content_area)

                _filament_dialog(_do)

            ui.button("+ Add Filament", on_click=_new).classes(
                "bg-blue-600 text-white rounded-lg px-4 py-2"
            )

        filaments = Q.list_filaments()
        if not filaments:
            ui.label("No filament in inventory.").classes(
                "text-slate-400 text-lg text-center py-10"
            )
            return

        with ui.element("div").classes("grid gap-2 w-full"):
            for f in filaments:
                low = f.get("quantity_g", 0) < 100
                border = "border-amber-300 bg-amber-50" if low else "border-slate-200"
                with ui.card().classes(f"p-3 rounded-lg border {border}"):
                    with ui.row().classes("items-start gap-3"):
                        with ui.column().classes("flex-1 gap-0 min-w-0"):
                            ui.label(
                                f"{f['brand']} — {f['color']} {f['filament_type']}"
                            ).classes("font-medium text-slate-800")
                            with ui.row().classes("gap-3 text-xs text-slate-400 flex-wrap"):
                                ui.label(f"{f.get('diameter_mm', 1.75)} mm")
                                if f.get("supplier"):
                                    ui.label(f"from {f['supplier']}")
                                if f.get("cost_per_kg"):
                                    ui.label(f"${f['cost_per_kg']:.2f}/kg")
                            if f.get("notes"):
                                ui.label(f["notes"]).classes(
                                    "text-xs text-slate-400 italic"
                                )

                        with ui.column().classes("items-end gap-0 shrink-0"):
                            qty_color = (
                                "text-amber-600 font-bold"
                                if low
                                else "text-slate-700 font-semibold"
                            )
                            ui.label(f"{f.get('quantity_g', 0):,.0f} g").classes(
                                qty_color
                            )
                            if low:
                                ui.badge("⚠ Low Stock").classes(
                                    "bg-amber-100 text-amber-700 text-xs rounded px-2"
                                )
                            with ui.row().classes("gap-1"):
                                def _edit(fil: dict = f) -> None:
                                    def _do(data: dict) -> None:
                                        Q.update_filament(fil["id"], **data)
                                        notify_success("Updated")
                                        filament_page(content_area)

                                    _filament_dialog(_do, existing=fil)

                                ui.button("Edit", on_click=_edit).props(
                                    "flat dense"
                                ).classes("text-blue-600 text-xs")

                                def _del(fil: dict = f) -> None:
                                    import sqlite3

                                    def _do() -> None:
                                        try:
                                            Q.delete_filament(fil["id"])
                                            notify_success("Deleted")
                                            filament_page(content_area)
                                        except sqlite3.IntegrityError:
                                            notify_error(
                                                "Cannot delete: referenced by print jobs. "
                                                "Delete those jobs first."
                                            )

                                    confirm_dialog(
                                        f"Delete {fil['brand']} {fil['color']}?", _do
                                    )

                                ui.button("Del", on_click=_del).props(
                                    "flat dense"
                                ).classes("text-red-400 text-xs")


# ── Braille Paper ─────────────────────────────────────────────────────────────

def _paper_dialog(on_save, existing: Optional[dict] = None) -> None:
    is_edit = existing is not None

    def _text(value: object) -> str:
        return value.strip() if isinstance(value, str) else ""

    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[480px] max-w-full"):
        ui.label("Edit Paper" if is_edit else "Add Paper").classes(
            "text-xl font-bold text-slate-800"
        )

        pts = [r["label"] for r in Q.list_material_categories("paper_type")]
        pv = [r["value"] for r in Q.list_material_categories("paper_type")]
        cur = existing.get("paper_type", pv[0] if pv else "") if is_edit else (pv[0] if pv else "")
        try:
            cur_lbl = pts[pv.index(cur)]
        except (ValueError, IndexError):
            cur_lbl = pts[0] if pts else ""
        pt_sel = ui.select(pts, label="Paper Type*", value=cur_lbl).classes("w-full")

        with ui.row().classes("gap-4 w-full"):
            size = ui.input(
                "Size", value=existing.get("size", "") if is_edit else ""
            ).classes("flex-1")
            ltype = ui.input(
                "Label Type", value=existing.get("label_type", "") if is_edit else ""
            ).classes("flex-1")

        with ui.row().classes("gap-4 w-full"):
            qty = ui.number(
                "Quantity*", value=existing.get("quantity", 0) if is_edit else 0, min=0
            ).classes("flex-1")
            sup = ui.input(
                "Supplier", value=existing.get("supplier", "") if is_edit else ""
            ).classes("flex-1")

        notes = ui.textarea(
            "Notes", value=existing.get("notes", "") if is_edit else ""
        ).classes("w-full").props("rows=2")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _save() -> None:
                try:
                    pt_val = pv[pts.index(pt_sel.value)]
                except (ValueError, IndexError):
                    pt_val = pv[0] if pv else "sheet_feed_11.5x11"
                on_save(
                    dict(
                        paper_type=pt_val,
                        quantity=int(qty.value or 0),
                        size=_text(size.value) or None,
                        label_type=_text(ltype.value) or None,
                        supplier=_text(sup.value),
                        notes=_text(notes.value),
                    )
                )
                dlg.close()

            ui.button("Save", on_click=_save).classes("bg-blue-600 text-white")

    dlg.open()


def paper_page(content_area: ui.element) -> None:
    content_area.clear()
    with content_area:
        with ui.row().classes("items-center mb-4"):
            section_header("Braille Paper", "Track paper and label supplies")
            ui.element("div").classes("flex-1")

            def _new() -> None:
                def _do(data: dict) -> None:
                    Q.add_paper(**data)
                    notify_success("Paper added")
                    paper_page(content_area)

                _paper_dialog(_do)

            ui.button("+ Add Paper", on_click=_new).classes(
                "bg-blue-600 text-white rounded-lg px-4 py-2"
            )

        papers = Q.list_paper()
        if not papers:
            ui.label("No paper in inventory.").classes(
                "text-slate-400 text-lg text-center py-10"
            )
            return

        with ui.element("div").classes("grid gap-2 w-full"):
            for p in papers:
                low = p.get("quantity", 0) < 50
                border = "border-amber-300 bg-amber-50" if low else "border-slate-200"
                with ui.card().classes(f"p-3 rounded-lg border {border}"):
                    with ui.row().classes("items-center gap-3"):
                        with ui.column().classes("flex-1 gap-0 min-w-0"):
                            ui.label(
                                p["paper_type"].replace("_", " ").title()
                            ).classes("font-medium text-slate-800")
                            with ui.row().classes("gap-3 text-xs text-slate-400 flex-wrap"):
                                if p.get("size"):
                                    ui.label(f"Size: {p['size']}")
                                if p.get("label_type"):
                                    ui.label(f"Type: {p['label_type']}")
                                if p.get("supplier"):
                                    ui.label(f"from {p['supplier']}")
                        with ui.column().classes("items-end gap-0 shrink-0"):
                            qty_color = (
                                "text-amber-600 font-bold"
                                if low
                                else "text-slate-700 font-semibold"
                            )
                            ui.label(f"{p.get('quantity', 0):,} sheets").classes(
                                qty_color
                            )
                            if low:
                                ui.badge("⚠ Low").classes(
                                    "bg-amber-100 text-amber-700 text-xs rounded px-2"
                                )
                            with ui.row().classes("gap-1"):
                                def _e(pp: dict = p) -> None:
                                    def _do(data: dict) -> None:
                                        Q.update_paper(pp["id"], **data)
                                        notify_success("Updated")
                                        paper_page(content_area)

                                    _paper_dialog(_do, existing=pp)

                                ui.button("Edit", on_click=_e).props(
                                    "flat dense"
                                ).classes("text-blue-600 text-xs")

                                def _d(pp: dict = p) -> None:
                                    def _do() -> None:
                                        Q.delete_paper(pp["id"])
                                        notify_success("Deleted")
                                        paper_page(content_area)

                                    confirm_dialog(f"Delete {pp['paper_type']}?", _do)

                                ui.button("Del", on_click=_d).props(
                                    "flat dense"
                                ).classes("text-red-400 text-xs")


# ── Electronics ───────────────────────────────────────────────────────────────

def _elec_dialog(on_save, existing: Optional[dict] = None) -> None:
    is_edit = existing is not None
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[520px] max-w-full"):
        ui.label("Edit Component" if is_edit else "Add Component").classes(
            "text-xl font-bold text-slate-800"
        )

        cats = [r["label"] for r in Q.list_material_categories("elec_cat")]
        cv = [r["value"] for r in Q.list_material_categories("elec_cat")]
        cur_c = existing.get("category", "other") if is_edit else "other"
        try:
            cur_cl = cats[cv.index(cur_c)]
        except ValueError:
            cur_cl = cats[0] if cats else "Other"
        cat_sel = ui.select(cats, label="Category*", value=cur_cl).classes("w-full")

        name = ui.input(
            "Name*", value=existing.get("name", "") if is_edit else ""
        ).classes("w-full")

        with ui.row().classes("gap-4 w-full"):
            brand = ui.input(
                "Brand", value=existing.get("brand", "") if is_edit else ""
            ).classes("flex-1")
            spec = ui.input(
                "Spec / Size / Gauge",
                value=existing.get("spec", "") if is_edit else "",
            ).classes("flex-1")

        units = [r["label"] for r in Q.list_material_categories("elec_unit")]
        uv = [r["value"] for r in Q.list_material_categories("elec_unit")]
        cur_u = existing.get("unit", "pcs") if is_edit else "pcs"
        try:
            cur_ul = units[uv.index(cur_u)]
        except ValueError:
            cur_ul = units[0] if units else "pcs"

        with ui.row().classes("gap-4 w-full"):
            qty = ui.number(
                "Quantity*",
                value=existing.get("quantity", 0) if is_edit else 0,
                min=0,
            ).classes("flex-1")
            unit_sel = ui.select(units, label="Unit", value=cur_ul).classes("flex-1")

        with ui.row().classes("gap-4 w-full"):
            cost = ui.number(
                "Cost Each ($)", value=existing.get("cost_each") or 0, min=0
            ).classes("flex-1")
            sup = ui.input(
                "Supplier", value=existing.get("supplier", "") if is_edit else ""
            ).classes("flex-1")

        notes = ui.textarea(
            "Notes", value=existing.get("notes", "") if is_edit else ""
        ).classes("w-full").props("rows=2")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _save() -> None:
                name_text = _text_value(name.value)
                brand_text = _text_value(brand.value)
                spec_text = _text_value(spec.value)
                supplier_text = _text_value(sup.value)
                notes_text = _text_value(notes.value)

                if not name_text:
                    notify_error("Name required")
                    return
                try:
                    cat_val = cv[cats.index(cat_sel.value)]
                except (ValueError, IndexError):
                    cat_val = "other"
                try:
                    u_val = uv[units.index(unit_sel.value)]
                except (ValueError, IndexError):
                    u_val = "pcs"
                on_save(
                    dict(
                        category=cat_val,
                        name=name_text,
                        brand=brand_text or None,
                        spec=spec_text or None,
                        quantity=float(qty.value or 0),
                        unit=u_val,
                        cost_each=float(cost.value) if cost.value else None,
                        supplier=supplier_text,
                        notes=notes_text,
                    )
                )
                dlg.close()

            ui.button("Save", on_click=_save).classes("bg-blue-600 text-white")

    dlg.open()


def electronics_page(content_area: ui.element) -> None:
    content_area.clear()
    with content_area:
        with ui.row().classes("items-center mb-4"):
            section_header(
                "Electronics Inventory", "Components, boards, wire, and hardware"
            )
            ui.element("div").classes("flex-1")

            def _new() -> None:
                def _do(data: dict) -> None:
                    Q.add_electronic(**data)
                    notify_success("Component added")
                    electronics_page(content_area)

                _elec_dialog(_do)

            ui.button("+ Add Component", on_click=_new).classes(
                "bg-blue-600 text-white rounded-lg px-4 py-2"
            )

        items = Q.list_electronics()
        if not items:
            ui.label("No electronics in inventory.").classes(
                "text-slate-400 text-lg text-center py-10"
            )
            return

        # Group by category
        by_cat: dict[str, list] = {}
        for item in items:
            by_cat.setdefault(item["category"], []).append(item)

        cat_labels = {
            r["value"]: r["label"]
            for r in Q.list_material_categories("elec_cat", active_only=False)
        }

        for cat, cat_items in by_cat.items():
            ui.label(cat_labels.get(cat, cat.replace("_", " ").title())).classes(
                "text-xs font-semibold text-slate-500 uppercase tracking-wider mt-4 mb-2"
            )
            with ui.element("div").classes("grid gap-2 w-full"):
                for item in cat_items:
                    with ui.card().classes("p-3 rounded-lg border border-slate-200"):
                        with ui.row().classes("items-center gap-3"):
                            with ui.column().classes("flex-1 gap-0 min-w-0"):
                                ui.label(item["name"]).classes(
                                    "font-medium text-slate-800"
                                )
                                parts = []
                                if item.get("brand"):
                                    parts.append(item["brand"])
                                if item.get("spec"):
                                    parts.append(item["spec"])
                                if item.get("supplier"):
                                    parts.append(f"from {item['supplier']}")
                                if parts:
                                    ui.label(" · ".join(parts)).classes(
                                        "text-xs text-slate-400"
                                    )
                            with ui.column().classes("items-end gap-0 shrink-0"):
                                ui.label(
                                    f"{item.get('quantity', 0)} {item.get('unit', 'pcs')}"
                                ).classes("font-semibold text-slate-700")
                                if item.get("cost_each"):
                                    ui.label(f"${item['cost_each']:.2f} ea").classes(
                                        "text-xs text-slate-400"
                                    )
                            with ui.row().classes("gap-1 shrink-0"):
                                def _e(it: dict = item) -> None:
                                    def _do(data: dict) -> None:
                                        Q.update_electronic(it["id"], **data)
                                        notify_success("Updated")
                                        electronics_page(content_area)

                                    _elec_dialog(_do, existing=it)

                                ui.button("Edit", on_click=_e).props(
                                    "flat dense"
                                ).classes("text-blue-600 text-xs")

                                def _d(it: dict = item) -> None:
                                    def _do() -> None:
                                        Q.delete_electronic(it["id"])
                                        notify_success("Deleted")
                                        electronics_page(content_area)

                                    confirm_dialog(f"Delete '{it['name']}'?", _do)

                                ui.button("Del", on_click=_d).props(
                                    "flat dense"
                                ).classes("text-red-400 text-xs")
