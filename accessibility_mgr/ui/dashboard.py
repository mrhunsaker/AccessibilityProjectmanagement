"""Dashboard panel — summary statistics and recent activity."""

from __future__ import annotations

from nicegui import ui

import db.queries as Q
from ui.components import section_header, PRIORITY_COLORS


def _stat_card(label: str, value: str | int, color: str = "blue", icon: str = "") -> None:
    colors = {
        "blue":   ("bg-blue-50",   "text-blue-600",   "border-blue-200"),
        "green":  ("bg-green-50",  "text-green-600",  "border-green-200"),
        "amber":  ("bg-amber-50",  "text-amber-600",  "border-amber-200"),
        "purple": ("bg-purple-50", "text-purple-600", "border-purple-200"),
        "red":    ("bg-red-50",    "text-red-600",    "border-red-200"),
    }
    bg, text, border = colors.get(color, colors["blue"])
    with ui.card().classes(f"p-4 {bg} border {border} rounded-xl shadow-sm"):
        if icon:
            ui.label(icon).classes("text-2xl mb-1")
        ui.label(str(value)).classes(f"text-3xl font-bold {text}")
        ui.label(label).classes("text-slate-600 text-sm mt-1")


def dashboard_page(content_area: ui.element) -> None:
    content_area.clear()
    with content_area:
        section_header("Dashboard", "Overview of your accessibility materials studio")

        # ── Stats ─────────────────────────────────────────────────────────────
        braille_jobs = Q.list_braille_jobs()
        lp_jobs = Q.list_lp_jobs()
        print_jobs = Q.list_print_jobs()
        filaments = Q.list_filaments()
        paper = Q.list_paper()

        in_progress_b = sum(1 for j in braille_jobs
                           if 0 < sum([j.get(k, 0) for k in ["digitized","formatted","brailled","proofread","delivered"]]) < 5)
        in_progress_lp = sum(1 for j in lp_jobs
                            if 0 < sum([j.get(k, 0) for k in ["digitized","formatted","converted","proofread","delivered"]]) < 5)
        urgent = [j for j in braille_jobs + lp_jobs if j.get("priority") == "urgent"]
        low_filament = [f for f in filaments if f.get("quantity_g", 0) < 100]

        with ui.row().classes("gap-4 flex-wrap mb-8"):
            _stat_card("Braille Jobs",       len(braille_jobs),           "purple",  "⠿")
            _stat_card("In Progress",         in_progress_b + in_progress_lp, "blue", "⏳")
            _stat_card("LP/eBraille Jobs",   len(lp_jobs),                "green",   "🔠")
            _stat_card("Print Jobs",          len(print_jobs),             "amber",   "🖨️")
            _stat_card("Urgent Items",        len(urgent),                 "red",     "🚨")
            _stat_card("Low Filament",        len(low_filament),           "amber",   "🧵")

        with ui.row().classes("gap-6 flex-wrap items-start"):
            # ── Recent braille jobs ───────────────────────────────────────────
            with ui.card().classes("flex-1 min-w-80 p-5 rounded-xl shadow-sm border border-slate-200"):
                ui.label("Recent Braille Jobs").classes("text-base font-semibold text-slate-700 mb-3")
                if not braille_jobs:
                    ui.label("No braille jobs yet").classes("text-slate-400 text-sm")
                else:
                    for job in braille_jobs[:8]:
                        steps = ["digitized","formatted","brailled","proofread","delivered"]
                        done = sum(job.get(s, 0) for s in steps)
                        pct = int(done / 5 * 100)
                        with ui.row().classes("items-center gap-3 py-2 border-b border-slate-100 last:border-0"):
                            with ui.column().classes("flex-1 gap-0"):
                                ui.label(job["title"]).classes("text-sm font-medium text-slate-700 truncate max-w-52")
                                ui.label(job.get("braille_type","").capitalize()).classes("text-xs text-slate-400")
                            with ui.element("div").classes("w-20 bg-slate-100 rounded-full h-1.5"):
                                ui.element("div").classes(
                                    f"h-1.5 rounded-full {'bg-green-500' if pct==100 else 'bg-blue-500'}"
                                ).style(f"width:{pct}%")
                            p = job.get("priority","normal")
                            pcls = PRIORITY_COLORS.get(p,"")
                            ui.badge(p[0].upper()).classes(f"text-xs w-5 h-5 flex items-center justify-center rounded-full {pcls}")

            # ── Recent LP/eBraille jobs ────────────────────────────────────────
            with ui.card().classes("flex-1 min-w-80 p-5 rounded-xl shadow-sm border border-slate-200"):
                ui.label("Recent LP / eBraille Jobs").classes("text-base font-semibold text-slate-700 mb-3")
                if not lp_jobs:
                    ui.label("No LP/eBraille jobs yet").classes("text-slate-400 text-sm")
                else:
                    for job in lp_jobs[:8]:
                        steps = ["digitized","formatted","converted","proofread","delivered"]
                        done = sum(job.get(s, 0) for s in steps)
                        pct = int(done / 5 * 100)
                        with ui.row().classes("items-center gap-3 py-2 border-b border-slate-100 last:border-0"):
                            with ui.column().classes("flex-1 gap-0"):
                                ui.label(job["title"]).classes("text-sm font-medium text-slate-700 truncate max-w-52")
                                ui.label(job.get("job_type","").replace("_"," ").title()).classes("text-xs text-slate-400")
                            with ui.element("div").classes("w-20 bg-slate-100 rounded-full h-1.5"):
                                ui.element("div").classes(
                                    f"h-1.5 rounded-full {'bg-green-500' if pct==100 else 'bg-purple-500'}"
                                ).style(f"width:{pct}%")

            # ── Inventory alerts ──────────────────────────────────────────────
            with ui.card().classes("flex-1 min-w-72 p-5 rounded-xl shadow-sm border border-slate-200"):
                ui.label("Inventory Alerts").classes("text-base font-semibold text-slate-700 mb-3")
                alerts = []
                for f in filaments:
                    if f.get("quantity_g", 0) < 100:
                        alerts.append(f"🧵 {f['brand']} {f['color']} {f['filament_type']}: {f['quantity_g']}g remaining")
                for p in paper:
                    if p.get("quantity", 0) < 50:
                        alerts.append(f"📄 {p['paper_type'].replace('_',' ').title()}: {p['quantity']} sheets")
                if not alerts:
                    with ui.row().classes("items-center gap-2"):
                        ui.label("✅").classes("text-lg")
                        ui.label("All inventory levels OK").classes("text-sm text-slate-500")
                else:
                    for a in alerts[:6]:
                        ui.label(a).classes("text-sm text-amber-700 py-1 border-b border-amber-50 last:border-0")

        # ── Recent print jobs ─────────────────────────────────────────────────
        with ui.card().classes("mt-6 p-5 rounded-xl shadow-sm border border-slate-200"):
            ui.label("Recent Print Jobs").classes("text-base font-semibold text-slate-700 mb-3")
            if not print_jobs:
                ui.label("No print jobs yet").classes("text-slate-400 text-sm")
            else:
                with ui.row().classes("gap-2 text-xs text-slate-400 font-medium uppercase tracking-wider pb-2 border-b border-slate-100"):
                    ui.label("Object").classes("flex-1")
                    ui.label("Printer").classes("w-40")
                    ui.label("Filament").classes("w-48")
                    ui.label("Used (g)").classes("w-20 text-right")
                    ui.label("Result").classes("w-20 text-center")
                    ui.label("Date").classes("w-32")
                for job in print_jobs[:10]:
                    with ui.row().classes("items-center gap-2 py-2 border-b border-slate-50 last:border-0 text-sm"):
                        ui.label(job.get("object_name") or job.get("file_name") or "—").classes("flex-1 text-slate-700")
                        ui.label(job.get("printer_name","—")).classes("w-40 text-slate-500")
                        ui.label(job.get("filament_desc","—")).classes("w-48 text-slate-500 truncate")
                        ui.label(str(job.get("filament_used_g","—"))).classes("w-20 text-right text-slate-500")
                        if job.get("successful"):
                            ui.badge("✓ OK").classes("w-20 text-center bg-green-100 text-green-700 rounded text-xs")
                        else:
                            ui.badge("✗ FAIL").classes("w-20 text-center bg-red-100 text-red-700 rounded text-xs")
                        ui.label(str(job.get("printed_at",""))[:10]).classes("w-32 text-slate-400")
