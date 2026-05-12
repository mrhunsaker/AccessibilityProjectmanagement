"""
Inventory panels: Filament, Paper, Electronics, and 3-D Print Jobs.
"""

"""Legacy inventory UI module retained for documentation and compatibility."""

from __future__ import annotations

from typing import Optional

from nicegui import ui

from ..db import queries as Q
from ..ui.components import (
    confirm_dialog, notify_error, notify_success, section_header,
)


# ═══════════════════════════════════════════════════════════════════════════════
# FILAMENT
# ═══════════════════════════════════════════════════════════════════════════════

def _filament_dialog(on_save, existing: Optional[dict] = None) -> None:
    """ filament dialog.
    
    Parameters
    ----------
    on_save : Any
        on_save parameter.
    
    existing : Any
        existing parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    is_edit = existing is not None
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[500px] max-w-full"):
        ui.label("Edit Filament" if is_edit else "Add Filament").classes("text-xl font-bold text-slate-800")

        with ui.row().classes("gap-4 w-full"):
            brand = ui.input("Brand*", value=existing.get("brand","") if is_edit else "").classes("flex-1")
            color = ui.input("Color*", value=existing.get("color","") if is_edit else "").classes("flex-1")

        types = [r["label"] for r in Q.list_material_categories("filament_type")]
        tv    = [r["value"] for r in Q.list_material_categories("filament_type")]
        cur = existing.get("filament_type","PLA") if is_edit else "PLA"
        try: cur_lbl = types[tv.index(cur)]
        except ValueError: cur_lbl = types[0] if types else "PLA"
        ft_sel = ui.select(types, label="Type*", value=cur_lbl).classes("w-full")

        diams = [r["label"] for r in Q.list_material_categories("diameter_mm")]
        dv    = [r["value"] for r in Q.list_material_categories("diameter_mm")]
        cur_d = str(existing.get("diameter_mm",1.75)) if is_edit else "1.75"
        try: cur_dlbl = diams[dv.index(cur_d)]
        except ValueError: cur_dlbl = diams[0] if diams else "1.75 mm"
        diam_sel = ui.select(diams, label="Diameter", value=cur_dlbl).classes("w-full")

        with ui.row().classes("gap-4 w-full"):
            qty  = ui.number("Qty (g)*", value=existing.get("quantity_g",0) if is_edit else 0, min=0).classes("flex-1")
            cpk  = ui.number("Cost/kg ($)", value=existing.get("cost_per_kg") or 0, min=0).classes("flex-1")

        with ui.row().classes("gap-4 w-full"):
            supplier = ui.input("Supplier", value=existing.get("supplier","") if is_edit else "").classes("flex-1")

        notes = ui.textarea("Notes", value=existing.get("notes","") if is_edit else "").classes("w-full").props("rows=2")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")
            def _save():
                """ save.
                
                Returns
                -------
                Any
                    Function result.
                
                """
                if not brand.value.strip() or not color.value.strip():
                    notify_error("Brand and Color are required"); return
                try: ft_val = tv[types.index(ft_sel.value)]
                except (ValueError, IndexError): ft_val = "PLA"
                try: d_val = float(dv[diams.index(diam_sel.value)])
                except (ValueError, IndexError): d_val = 1.75
                cpk_val = float(cpk.value) if cpk.value else None
                on_save(dict(brand=brand.value.strip(), color=color.value.strip(),
                             filament_type=ft_val, diameter_mm=d_val,
                             quantity_g=float(qty.value or 0),
                             cost_per_kg=cpk_val,
                             supplier=supplier.value.strip(),
                             notes=notes.value.strip()))
                dlg.close()
            ui.button("Save", on_click=_save).classes("bg-blue-600 text-white")
    dlg.open()


def filament_page(content_area: ui.element) -> None:
    """Filament page.
    
    Parameters
    ----------
    content_area : Any
        content_area parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    content_area.clear()
    with content_area:
        with ui.row().classes("items-center mb-4"):
            section_header("Filament Inventory", "Track 3-D printer filament stock")
            ui.element("div").classes("flex-1")
            def _new():
                               """ do.
                               
                               Parameters
                               ----------
                               data : Any
                                   data parameter.
                               
                               Returns
                               -------
                               Any
                                   Function result.
                               
                               """
                """ new.
                
                Returns
                -------
                Any
                    Function result.
                
                """
                def _do(data): Q.add_filament(**data); notify_success("Filament added"); filament_page(content_area)
                _filament_dialog(_do)
            ui.button("+ Add Filament", on_click=_new).classes("bg-blue-600 text-white rounded-lg px-4 py-2")

        filaments = Q.list_filaments()
        if not filaments:
            ui.label("No filament in inventory").classes("text-slate-400 text-lg text-center py-10")
            return

        with ui.element("div").classes("grid gap-3 w-full"):
            for f in filaments:
                low = f.get("quantity_g",0) < 100
                border = "border-amber-300 bg-amber-50" if low else "border-slate-200"
                with ui.card().classes(f"p-4 rounded-xl border {border}"):
                    with ui.row().classes("items-start gap-4"):
                        # Color swatch
                        with ui.element("div").classes("w-10 h-10 rounded-full border border-slate-300 shrink-0").style(
                            f"background:{f['color'].lower() if f['color'].lower() in ['red','blue','green','black','white','yellow','orange','purple','pink','gray','grey','silver','gold'] else '#888'}"
                        ):
                            pass

                        with ui.column().classes("flex-1 gap-1 min-w-0"):
                            ui.label(f"{f['brand']} — {f['color']} {f['filament_type']}").classes("font-semibold text-slate-800")
                            with ui.row().classes("gap-4 text-sm text-slate-500 flex-wrap"):
                                ui.label(f"{f.get('diameter_mm',1.75)} mm")
                                if f.get("supplier"): ui.label(f"📦 {f['supplier']}")
                                if f.get("cost_per_kg"): ui.label(f"${f['cost_per_kg']:.2f}/kg")
                            if f.get("notes"):
                                ui.label(f["notes"]).classes("text-xs text-slate-400 italic")

                        with ui.column().classes("items-end gap-1 shrink-0"):
                            qty_color = "text-amber-600 font-bold" if low else "text-slate-700 font-semibold"
                            ui.label(f"{f.get('quantity_g',0):,.0f} g").classes(f"text-lg {qty_color}")
                            if low:
                                ui.badge("⚠ Low Stock").classes("bg-amber-100 text-amber-700 text-xs rounded px-2")

                            with ui.row().classes("gap-1"):
                                def _edit(fil=f):
                                                   """ do.
                                                   
                                                   Parameters
                                                   ----------
                                                   data : Any
                                                       data parameter.
                                                   
                                                   Returns
                                                   -------
                                                   Any
                                                       Function result.
                                                   
                                                   """
                                    """ edit.
                                    
                                    Parameters
                                    ----------
                                    fil : Any
                                        fil parameter.
                                    
                                    Returns
                                    -------
                                    Any
                                        Function result.
                                    
                                    """
                                    def _do(data): Q.update_filament(fil["id"], **data); notify_success("Updated"); filament_page(content_area)
                                    _filament_dialog(_do, existing=fil)
                                ui.button("Edit", on_click=_edit).props("flat dense").classes("text-blue-600 text-sm")
                                def _del(fil=f):
                                               """ do.
                                               
                                               Returns
                                               -------
                                               Any
                                                   Function result.
                                               
                                               """
                                    """ del.
                                    
                                    Parameters
                                    ----------
                                    fil : Any
                                        fil parameter.
                                    
                                    Returns
                                    -------
                                    Any
                                        Function result.
                                    
                                    """
                                    def _do(): Q.delete_filament(fil["id"]); notify_success("Deleted"); filament_page(content_area)
                                    confirm_dialog(f"Delete {fil['brand']} {fil['color']}?", _do)
                                ui.button("Delete", on_click=_del).props("flat dense").classes("text-red-400 text-sm")


# ═══════════════════════════════════════════════════════════════════════════════
# BRAILLE PAPER
# ═══════════════════════════════════════════════════════════════════════════════

def _paper_dialog(on_save, existing: Optional[dict] = None) -> None:
    """ paper dialog.
    
    Parameters
    ----------
    on_save : Any
        on_save parameter.
    
    existing : Any
        existing parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    is_edit = existing is not None
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[480px] max-w-full"):
        ui.label("Edit Paper" if is_edit else "Add Paper").classes("text-xl font-bold text-slate-800")

        pts = [r["label"] for r in Q.list_material_categories("paper_type")]
        pv  = [r["value"] for r in Q.list_material_categories("paper_type")]
        cur = existing.get("paper_type","sheet_feed_11.5x11") if is_edit else pv[0] if pv else ""
        try: cur_lbl = pts[pv.index(cur)]
        except ValueError: cur_lbl = pts[0] if pts else ""
        pt_sel = ui.select(pts, label="Paper Type*", value=cur_lbl).classes("w-full")

        with ui.row().classes("gap-4 w-full"):
            size  = ui.input("Size (for generic labels)", value=existing.get("size","") if is_edit else "").classes("flex-1")
            ltype = ui.input("Label Type (removable/permanent)", value=existing.get("label_type","") if is_edit else "").classes("flex-1")

        with ui.row().classes("gap-4 w-full"):
            qty  = ui.number("Quantity*", value=existing.get("quantity",0) if is_edit else 0, min=0).classes("flex-1")
            sup  = ui.input("Supplier", value=existing.get("supplier","") if is_edit else "").classes("flex-1")

        notes = ui.textarea("Notes", value=existing.get("notes","") if is_edit else "").classes("w-full").props("rows=2")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")
            def _save():
                """ save.
                
                Returns
                -------
                Any
                    Function result.
                
                """
                try: pt_val = pv[pts.index(pt_sel.value)]
                except (ValueError, IndexError): pt_val = pv[0] if pv else "sheet_feed_11.5x11"
                on_save(dict(paper_type=pt_val, quantity=int(qty.value or 0),
                             size=size.value.strip() or None,
                             label_type=ltype.value.strip() or None,
                             supplier=sup.value.strip(), notes=notes.value.strip()))
                dlg.close()
            ui.button("Save", on_click=_save).classes("bg-blue-600 text-white")
    dlg.open()


def paper_page(content_area: ui.element) -> None:
    """Paper page.
    
    Parameters
    ----------
    content_area : Any
        content_area parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    content_area.clear()
    with content_area:
        with ui.row().classes("items-center mb-4"):
            section_header("Braille Paper", "Track paper and label supplies")
            ui.element("div").classes("flex-1")
            def _new():
                               """ do.
                               
                               Parameters
                               ----------
                               data : Any
                                   data parameter.
                               
                               Returns
                               -------
                               Any
                                   Function result.
                               
                               """
                """ new.
                
                Returns
                -------
                Any
                    Function result.
                
                """
                def _do(data): Q.add_paper(**data); notify_success("Paper added"); paper_page(content_area)
                _paper_dialog(_do)
            ui.button("+ Add Paper", on_click=_new).classes("bg-blue-600 text-white rounded-lg px-4 py-2")

        papers = Q.list_paper()
        if not papers:
            ui.label("No paper in inventory").classes("text-slate-400 text-lg text-center py-10")
            return

        with ui.element("div").classes("grid gap-3 w-full"):
            for p in papers:
                low = p.get("quantity",0) < 50
                border = "border-amber-300 bg-amber-50" if low else "border-slate-200"
                with ui.card().classes(f"p-4 rounded-xl border {border}"):
                    with ui.row().classes("items-center gap-4"):
                        with ui.column().classes("flex-1 gap-1"):
                            ui.label(p["paper_type"].replace("_"," ").title()).classes("font-semibold text-slate-800")
                            with ui.row().classes("gap-4 text-sm text-slate-500 flex-wrap"):
                                if p.get("size"): ui.label(f"Size: {p['size']}")
                                if p.get("label_type"): ui.label(f"Type: {p['label_type']}")
                                if p.get("supplier"): ui.label(f"📦 {p['supplier']}")
                        with ui.column().classes("items-end gap-1"):
                            qty_color = "text-amber-600 font-bold" if low else "text-slate-700 font-semibold"
                            ui.label(f"{p.get('quantity',0):,} sheets").classes(f"text-lg {qty_color}")
                            if low: ui.badge("⚠ Low").classes("bg-amber-100 text-amber-700 text-xs rounded px-2")
                            with ui.row().classes("gap-1"):
                                def _e(pp=p):
                                                   """ do.
                                                   
                                                   Parameters
                                                   ----------
                                                   data : Any
                                                       data parameter.
                                                   
                                                   Returns
                                                   -------
                                                   Any
                                                       Function result.
                                                   
                                                   """
                                    """ e.
                                    
                                    Parameters
                                    ----------
                                    pp : Any
                                        pp parameter.
                                    
                                    Returns
                                    -------
                                    Any
                                        Function result.
                                    
                                    """
                                    def _do(data): Q.update_paper(pp["id"], **data); notify_success("Updated"); paper_page(content_area)
                                    _paper_dialog(_do, existing=pp)
                                ui.button("Edit", on_click=_e).props("flat dense").classes("text-blue-600 text-sm")
                                def _d(pp=p):
                                               """ do.
                                               
                                               Returns
                                               -------
                                               Any
                                                   Function result.
                                               
                                               """
                                    """ d.
                                    
                                    Parameters
                                    ----------
                                    pp : Any
                                        pp parameter.
                                    
                                    Returns
                                    -------
                                    Any
                                        Function result.
                                    
                                    """
                                    def _do(): Q.delete_paper(pp["id"]); notify_success("Deleted"); paper_page(content_area)
                                    confirm_dialog(f"Delete {pp['paper_type']}?", _do)
                                ui.button("Delete", on_click=_d).props("flat dense").classes("text-red-400 text-sm")


# ═══════════════════════════════════════════════════════════════════════════════
# ELECTRONICS
# ═══════════════════════════════════════════════════════════════════════════════

def _elec_dialog(on_save, existing: Optional[dict] = None) -> None:
    """ elec dialog.
    
    Parameters
    ----------
    on_save : Any
        on_save parameter.
    
    existing : Any
        existing parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    is_edit = existing is not None
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[520px] max-w-full"):
        ui.label("Edit Component" if is_edit else "Add Component").classes("text-xl font-bold text-slate-800")

        cats = [r["label"] for r in Q.list_material_categories("elec_cat")]
        cv   = [r["value"] for r in Q.list_material_categories("elec_cat")]
        cur  = existing.get("category","other") if is_edit else "other"
        try: cur_cl = cats[cv.index(cur)]
        except ValueError: cur_cl = cats[0] if cats else "Other"
        cat_sel = ui.select(cats, label="Category*", value=cur_cl).classes("w-full")

        name = ui.input("Name*", value=existing.get("name","") if is_edit else "").classes("w-full")

        with ui.row().classes("gap-4 w-full"):
            brand = ui.input("Brand", value=existing.get("brand","") if is_edit else "").classes("flex-1")
            spec  = ui.input("Spec / Size / Gauge", value=existing.get("spec","") if is_edit else "").classes("flex-1")

        units = [r["label"] for r in Q.list_material_categories("elec_unit")]
        uv    = [r["value"] for r in Q.list_material_categories("elec_unit")]
        cur_u = existing.get("unit","pcs") if is_edit else "pcs"
        try: cur_ul = units[uv.index(cur_u)]
        except ValueError: cur_ul = units[0] if units else "pcs"

        with ui.row().classes("gap-4 w-full"):
            qty     = ui.number("Quantity*", value=existing.get("quantity",0) if is_edit else 0, min=0).classes("flex-1")
            unit_sel= ui.select(units, label="Unit", value=cur_ul).classes("flex-1")

        with ui.row().classes("gap-4 w-full"):
            cost   = ui.number("Cost Each ($)", value=existing.get("cost_each") or 0, min=0).classes("flex-1")
            sup    = ui.input("Supplier", value=existing.get("supplier","") if is_edit else "").classes("flex-1")

        notes = ui.textarea("Notes", value=existing.get("notes","") if is_edit else "").classes("w-full").props("rows=2")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")
            def _save():
                """ save.
                
                Returns
                -------
                Any
                    Function result.
                
                """
                if not name.value.strip(): notify_error("Name required"); return
                try: cat_val = cv[cats.index(cat_sel.value)]
                except (ValueError,IndexError): cat_val = "other"
                try: u_val = uv[units.index(unit_sel.value)]
                except (ValueError,IndexError): u_val = "pcs"
                cost_val = float(cost.value) if cost.value else None
                on_save(dict(category=cat_val, name=name.value.strip(),
                             brand=brand.value.strip() or None,
                             spec=spec.value.strip() or None,
                             quantity=float(qty.value or 0),
                             unit=u_val,
                             cost_each=cost_val,
                             supplier=sup.value.strip(),
                             notes=notes.value.strip()))
                dlg.close()
            ui.button("Save", on_click=_save).classes("bg-blue-600 text-white")
    dlg.open()


def electronics_page(content_area: ui.element) -> None:
    """Electronics page.
    
    Parameters
    ----------
    content_area : Any
        content_area parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    content_area.clear()
    with content_area:
        with ui.row().classes("items-center mb-4"):
            section_header("Electronics Inventory", "Components, boards, wire, and hardware")
            ui.element("div").classes("flex-1")
            def _new():
                               """ do.
                               
                               Parameters
                               ----------
                               data : Any
                                   data parameter.
                               
                               Returns
                               -------
                               Any
                                   Function result.
                               
                               """
                """ new.
                
                Returns
                -------
                Any
                    Function result.
                
                """
                def _do(data): Q.add_electronic(**data); notify_success("Added"); electronics_page(content_area)
                _elec_dialog(_do)
            ui.button("+ Add Component", on_click=_new).classes("bg-blue-600 text-white rounded-lg px-4 py-2")

        items = Q.list_electronics()
        if not items:
            ui.label("No electronics in inventory").classes("text-slate-400 text-lg text-center py-10")
            return

        # Group by category
        by_cat: dict[str, list] = {}
        for item in items:
            by_cat.setdefault(item["category"], []).append(item)

        for cat, cat_items in by_cat.items():
            cat_labels = {r["value"]: r["label"] for r in Q.list_material_categories("elec_cat", active_only=False)}
            ui.label(cat_labels.get(cat, cat.replace("_"," ").title())).classes("text-sm font-semibold text-slate-500 uppercase tracking-wider mt-4 mb-2")
            with ui.element("div").classes("grid gap-2 w-full"):
                for item in cat_items:
                    with ui.card().classes("p-3 rounded-lg border border-slate-200"):
                        with ui.row().classes("items-center gap-3"):
                            with ui.column().classes("flex-1 gap-0 min-w-0"):
                                ui.label(item["name"]).classes("font-medium text-slate-800")
                                detail_parts = []
                                if item.get("brand"): detail_parts.append(item["brand"])
                                if item.get("spec"):  detail_parts.append(item["spec"])
                                if item.get("supplier"): detail_parts.append(f"from {item['supplier']}")
                                if detail_parts:
                                    ui.label(" · ".join(detail_parts)).classes("text-xs text-slate-400")
                            with ui.column().classes("items-end gap-0 shrink-0"):
                                ui.label(f"{item.get('quantity',0)} {item.get('unit','pcs')}").classes("font-semibold text-slate-700")
                                if item.get("cost_each"):
                                    ui.label(f"${item['cost_each']:.2f} ea").classes("text-xs text-slate-400")
                            with ui.row().classes("gap-1 shrink-0"):
                                def _e(it=item):
                                                   """ do.
                                                   
                                                   Parameters
                                                   ----------
                                                   data : Any
                                                       data parameter.
                                                   
                                                   Returns
                                                   -------
                                                   Any
                                                       Function result.
                                                   
                                                   """
                                    """ e.
                                    
                                    Parameters
                                    ----------
                                    it : Any
                                        it parameter.
                                    
                                    Returns
                                    -------
                                    Any
                                        Function result.
                                    
                                    """
                                    def _do(data): Q.update_electronic(it["id"], **data); notify_success("Updated"); electronics_page(content_area)
                                    _elec_dialog(_do, existing=it)
                                ui.button("Edit", on_click=_e).props("flat dense").classes("text-blue-600 text-xs")
                                def _d(it=item):
                                               """ do.
                                               
                                               Returns
                                               -------
                                               Any
                                                   Function result.
                                               
                                               """
                                    """ d.
                                    
                                    Parameters
                                    ----------
                                    it : Any
                                        it parameter.
                                    
                                    Returns
                                    -------
                                    Any
                                        Function result.
                                    
                                    """
                                    def _do(): Q.delete_electronic(it["id"]); notify_success("Deleted"); electronics_page(content_area)
                                    confirm_dialog(f"Delete '{it['name']}'?", _do)
                                ui.button("Del", on_click=_d).props("flat dense").classes("text-red-400 text-xs")


# ═══════════════════════════════════════════════════════════════════════════════
# 3-D PRINT JOBS
# ═══════════════════════════════════════════════════════════════════════════════

def _print_job_dialog(on_save, existing: Optional[dict] = None) -> None:
    """ print job dialog.
    
    Parameters
    ----------
    on_save : Any
        on_save parameter.
    
    existing : Any
        existing parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    is_edit = existing is not None
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[560px] max-w-full"):
        ui.label("Edit Print Job" if is_edit else "Log Print Job").classes("text-xl font-bold text-slate-800")

        printers = Q.list_printers()
        pnames   = [p["name"] for p in printers]
        pids     = [p["id"]   for p in printers]
        cur_p    = existing.get("printer_name","") if is_edit else (pnames[0] if pnames else "")
        pr_sel   = ui.select(pnames, label="Printer*", value=cur_p).classes("w-full")

        filaments = Q.list_filaments()
        fdescs    = ["(none)"] + [f"{f['brand']} {f['color']} {f['filament_type']}" for f in filaments]
        fids      = [None] + [f["id"] for f in filaments]
        cur_fd    = existing.get("filament_desc","(none)") if is_edit else "(none)"
        fil_sel   = ui.select(fdescs, label="Filament Used", value=cur_fd).classes("w-full")

        with ui.row().classes("gap-4 w-full"):
            obj_name = ui.input("Object Name", value=existing.get("object_name","") if is_edit else "").classes("flex-1")
            used_g   = ui.number("Filament Used (g)", value=existing.get("filament_used_g",0) if is_edit else 0, min=0).classes("flex-1")

        with ui.row().classes("gap-4 w-full"):
            req     = ui.input("Requester", value=existing.get("requester","") if is_edit else "").classes("flex-1")
            rdate   = ui.input("Request Date (YYYY-MM-DD)", value=existing.get("request_date","") if is_edit else "").classes("flex-1")

        file_path = ui.input("Attach File Path (optional)", placeholder="/path/to/file.3mf").classes("w-full")

        success_chk = ui.checkbox("Successful", value=bool(existing.get("successful",1)) if is_edit else True)
        fail_reason = ui.input("Failure Reason", value=existing.get("failure_reason","") if is_edit else "").classes("w-full")
        notes       = ui.textarea("Notes", value=existing.get("notes","") if is_edit else "").classes("w-full").props("rows=2")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")
            def _save():
                """ save.
                
                Returns
                -------
                Any
                    Function result.
                
                """
                try: pr_id = pids[pnames.index(pr_sel.value)]
                except (ValueError, IndexError): notify_error("Select a printer"); return
                try: f_id = fids[fdescs.index(fil_sel.value)]
                except (ValueError, IndexError): f_id = None
                on_save(dict(
                    printer_id=pr_id, filament_id=f_id,
                    filament_used_g=float(used_g.value or 0),
                    file_source_path=file_path.value.strip() or None,
                    successful=1 if success_chk.value else 0,
                    failure_reason=fail_reason.value.strip() or None,
                    object_name=obj_name.value.strip(),
                    requester=req.value.strip(),
                    request_date=rdate.value.strip() or None,
                    notes=notes.value.strip(),
                ))
                dlg.close()
            ui.button("Save", on_click=_save).classes("bg-blue-600 text-white")
    dlg.open()


def print_jobs_page(content_area: ui.element) -> None:
    """Print jobs page.
    
    Parameters
    ----------
    content_area : Any
        content_area parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    content_area.clear()
    with content_area:
        with ui.row().classes("items-center mb-4"):
            section_header("3-D Print Jobs", "Log every print run with filament tracking and file attachment")
            ui.element("div").classes("flex-1")
            def _new():
                """ new.
                
                Returns
                -------
                Any
                    Function result.
                
                """
                def _do(data):
                    """ do.
                    
                    Parameters
                    ----------
                    data : Any
                        data parameter.
                    
                    Returns
                    -------
                    Any
                        Function result.
                    
                    """
                    try:
                        Q.add_print_job(**data)
                        notify_success("Print job logged")
                        print_jobs_page(content_area)
                    except Exception as e:
                        notify_error(f"Error: {e}")
                _print_job_dialog(_do)
            ui.button("+ Log Print Job", on_click=_new).classes("bg-amber-600 text-white rounded-lg px-4 py-2")

        jobs = Q.list_print_jobs()
        if not jobs:
            ui.label("No print jobs yet").classes("text-slate-400 text-lg text-center py-10")
            return

        with ui.card().classes("w-full rounded-xl border border-slate-200 overflow-hidden"):
            with ui.row().classes("gap-2 px-4 py-2 bg-slate-50 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200"):
                ui.label("Object").classes("flex-1 min-w-40")
                ui.label("Printer").classes("w-40")
                ui.label("Filament").classes("w-48")
                ui.label("Used (g)").classes("w-20 text-right")
                ui.label("Result").classes("w-24 text-center")
                ui.label("Requester").classes("w-32")
                ui.label("Date").classes("w-28")
                ui.label("").classes("w-20")

            for job in jobs:
                with ui.row().classes("items-center gap-2 px-4 py-3 border-b border-slate-50 last:border-0 hover:bg-slate-50"):
                    with ui.column().classes("flex-1 min-w-40 gap-0"):
                        ui.label(job.get("object_name") or job.get("file_name") or "—").classes("text-sm text-slate-700 font-medium truncate")
                        if job.get("file_name"):
                            ui.label(f"📎 {job['file_name']}").classes("text-xs text-indigo-500 truncate")
                    ui.label(job.get("printer_name","—")).classes("w-40 text-sm text-slate-500 truncate")
                    ui.label(job.get("filament_desc","—")).classes("w-48 text-sm text-slate-500 truncate")
                    ui.label(f"{job.get('filament_used_g',0):,.0f}").classes("w-20 text-right text-sm text-slate-700")
                    if job.get("successful"):
                        ui.badge("✓ OK").classes("w-24 text-center bg-green-100 text-green-700 rounded text-xs")
                    else:
                        with ui.element("div").classes("w-24"):
                            ui.badge("✗ FAIL").classes("w-full text-center bg-red-100 text-red-700 rounded text-xs")
                            if job.get("failure_reason"):
                                ui.label(job["failure_reason"]).classes("text-xs text-red-500 truncate")
                    ui.label(job.get("requester") or "—").classes("w-32 text-sm text-slate-500 truncate")
                    ui.label(str(job.get("printed_at",""))[:10]).classes("w-28 text-xs text-slate-400")
                    with ui.row().classes("w-20 gap-1 justify-end"):
                        def _del(j=job):
                                       """ do.
                                       
                                       Returns
                                       -------
                                       Any
                                           Function result.
                                       
                                       """
                            """ del.
                            
                            Parameters
                            ----------
                            j : Any
                                j parameter.
                            
                            Returns
                            -------
                            Any
                                Function result.
                            
                            """
                            def _do(): Q.delete_print_job(j["id"]); notify_success("Deleted"); print_jobs_page(content_area)
                            confirm_dialog(f"Delete print job?", _do)
                        ui.button("Del", on_click=_del).props("flat dense").classes("text-red-400 text-xs")
