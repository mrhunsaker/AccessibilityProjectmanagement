"""Dashboard — operational overview of the accessibility studio."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from ..db import queries as Q
from .components import PRIORITY_COLORS, section_header


def _stat_card(label: str, value: Any, color: str = "blue", icon: str = "") -> None:
    """ stat card.
    
    Parameters
    ----------
    label : Any
        label parameter.
    
    value : Any
        value parameter.
    
    color : Any
        color parameter.
    
    icon : Any
        icon parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
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


def _recent_job_card(
    title: str,
    jobs: list[dict],
    steps: list[str],
    empty_text: str,
    progress_color: str,
    job_type_label: str,
    type_key: str,
) -> None:
    """ recent job card.
    
    Parameters
    ----------
    title : Any
        title parameter.
    
    jobs : Any
        jobs parameter.
    
    steps : Any
        steps parameter.
    
    empty_text : Any
        empty_text parameter.
    
    progress_color : Any
        progress_color parameter.
    
    job_type_label : Any
        job_type_label parameter.
    
    type_key : Any
        type_key parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with ui.card().classes(
        "flex-1 min-w-80 p-5 rounded-xl shadow-sm border border-slate-200"
    ):
        ui.label(title).classes("text-base font-semibold text-slate-700 mb-3")
        if not jobs:
            ui.label(empty_text).classes("text-slate-400 text-sm")
            return

        for job in jobs[:8]:
            done = sum(job.get(s, 0) for s in steps)
            pct = int(done / len(steps) * 100) if steps else 0
            with ui.row().classes(
                "items-center gap-3 py-2 border-b border-slate-100 last:border-0"
            ):
                with ui.column().classes("flex-1 gap-0"):
                    ui.label(job["title"]).classes(
                        "text-sm font-medium text-slate-700 truncate max-w-52"
                    )
                    ui.label(job.get(type_key, job_type_label)).classes(
                        "text-xs text-slate-400"
                    )
                with ui.element("div").classes(
                    "w-20 bg-slate-100 rounded-full h-1.5"
                ):
                    ui.element("div").classes(
                        f"h-1.5 rounded-full {progress_color if pct < 100 else 'bg-green-500'}"
                    ).style(f"width:{pct}%")


def dashboard_page(content_area: ui.element) -> None:
    """Dashboard page.
    
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
        section_header("Dashboard", "Overview of your accessibility materials studio")

        braille_jobs = Q.list_braille_jobs()
        lp_jobs = Q.list_lp_jobs("large_print")
        ebraille_jobs = Q.list_lp_jobs("ebraille")
        epub3_daisy_jobs = Q.list_lp_jobs("epub3_daisy")
        tactile_jobs = Q.list_tactile_jobs()
        print_jobs = Q.list_print_jobs()
        filaments = Q.list_filaments()
        paper = Q.list_paper()
        recent_qa = Q.list_qa_runs(limit=5)
        recent_pipelines = Q.list_pipeline_runs(limit=5)

        b_steps = ["digitized", "formatted", "brailled", "proofread", "delivered"]
        lp_steps = ["digitized", "formatted", "converted", "proofread", "delivered"]

        in_progress_b = sum(
            1 for j in braille_jobs
            if 0 < sum(j.get(s, 0) for s in b_steps) < 5
        )
        in_progress_lp = sum(
            1 for j in lp_jobs
            if 0 < sum(j.get(s, 0) for s in lp_steps) < 5
        )
        in_progress_ebraille = sum(
            1 for j in ebraille_jobs
            if 0 < sum(j.get(s, 0) for s in lp_steps) < 5
        )
        in_progress_epub3_daisy = sum(
            1 for j in epub3_daisy_jobs
            if 0 < sum(j.get(s, 0) for s in lp_steps) < 5
        )
        tactile_steps = ["designed", "produced", "qa_reviewed", "delivered"]
        in_progress_tactile = sum(
            1 for j in tactile_jobs
            if 0 < sum(j.get(s, 0) for s in tactile_steps) < len(tactile_steps)
        )
        urgent = [
            j for j in braille_jobs + lp_jobs + ebraille_jobs + epub3_daisy_jobs + tactile_jobs
            if j.get("priority") == "urgent"
        ]
        low_filament = [f for f in filaments if f.get("quantity_g", 0) < 100]
        low_paper = [p for p in paper if p.get("quantity", 0) < 50]

        # ── Stats row ──────────────────────────────────────────────────────────
        with ui.row().classes("gap-4 flex-wrap mb-8"):
            _stat_card("Braille Jobs",    len(braille_jobs),           "purple", "⠿")
            _stat_card(
                "In Progress",
                in_progress_b + in_progress_lp + in_progress_ebraille + in_progress_epub3_daisy + in_progress_tactile,
                "blue",
                "⏳",
            )
            _stat_card("Large Print",     len(lp_jobs),                "green",  "🔠")
            _stat_card("eBraille",        len(ebraille_jobs),          "green",  "⠮")
            _stat_card("EPUB3/DAISY",     len(epub3_daisy_jobs),       "green",  "📚")
            _stat_card("Tactile",         len(tactile_jobs),           "red",    "▦")
            _stat_card("Print Jobs",      len(print_jobs),             "amber",  "🖨️")
            _stat_card("Urgent",          len(urgent),                 "red",    "🚨")
            _stat_card("Low Stock",       len(low_filament) + len(low_paper), "amber", "⚠️")

        # ── Home quick-launch ────────────────────────────────────────────────
        with ui.card().classes(
            "mb-6 p-5 rounded-xl shadow-sm border border-slate-200"
        ):
            ui.label("Quick Launch").classes("text-base font-semibold text-slate-700 mb-2")
            ui.label("Jump directly to key production job pages.").classes(
                "text-sm text-slate-500 mb-3"
            )

            with ui.row().classes("gap-2 flex-wrap"):
                ui.button("Braille Jobs", on_click=lambda: __import__(
                    "accessibility_mgr.ui.braille_jobs", fromlist=["braille_jobs_page"]
                ).braille_jobs_page(content_area)).classes("bg-indigo-600 text-white")
                ui.button("Large Print Jobs", on_click=lambda: __import__(
                    "accessibility_mgr.ui.lp_ebraille", fromlist=["large_print_jobs_page"]
                ).large_print_jobs_page(content_area)).classes("bg-green-600 text-white")
                ui.button("eBraille Jobs", on_click=lambda: __import__(
                    "accessibility_mgr.ui.lp_ebraille", fromlist=["ebraille_jobs_page"]
                ).ebraille_jobs_page(content_area)).classes("bg-emerald-600 text-white")
                ui.button("EPUB3 / DAISY Jobs", on_click=lambda: __import__(
                    "accessibility_mgr.ui.lp_ebraille", fromlist=["epub3_daisy_jobs_page"]
                ).epub3_daisy_jobs_page(content_area)).classes("bg-teal-600 text-white")
                ui.button("Tactile Graphics", on_click=lambda: __import__(
                    "accessibility_mgr.ui.tactile_graphics", fromlist=["tactile_graphics_page"]
                ).tactile_graphics_page(content_area)).classes("bg-rose-600 text-white")

        # ── Inventory alerts ───────────────────────────────────────────────
        with ui.card().classes(
            "mt-2 mb-6 p-5 rounded-xl shadow-sm border border-slate-200"
        ):
            ui.label("Inventory Alerts").classes(
                "text-base font-semibold text-slate-700 mb-3"
            )
            alerts: list[str] = []
            for f in filaments:
                if f.get("quantity_g", 0) < 100:
                    alerts.append(
                        f"🧵 {f['brand']} {f['color']} {f['filament_type']}: "
                        f"{f['quantity_g']:.0f}g left"
                    )
            for p in paper:
                if p.get("quantity", 0) < 50:
                    alerts.append(
                        f"📄 {p['paper_type'].replace('_', ' ').title()}: "
                        f"{p['quantity']} sheets left"
                    )
            if not alerts:
                with ui.row().classes("items-center gap-2"):
                    ui.label("✅").classes("text-lg")
                    ui.label("All inventory levels OK").classes(
                        "text-sm text-slate-500"
                    )
            else:
                for a in alerts[:6]:
                    ui.label(a).classes(
                        "text-sm text-amber-700 py-1 border-b border-amber-50 last:border-0"
                    )

        with ui.row().classes("gap-6 flex-wrap items-start"):
            _recent_job_card(
                "Recent Braille Jobs",
                braille_jobs,
                b_steps,
                "No braille jobs yet.",
                "bg-blue-500",
                "Braille",
                "braille_type",
            )
            _recent_job_card(
                "Recent Large Print Jobs",
                lp_jobs,
                lp_steps,
                "No large print jobs yet.",
                "bg-purple-500",
                "Large Print",
                "job_type",
            )
            _recent_job_card(
                "Recent eBraille Jobs",
                ebraille_jobs,
                lp_steps,
                "No eBraille jobs yet.",
                "bg-purple-500",
                "eBraille",
                "job_type",
            )
            _recent_job_card(
                "Recent EPUB3 / DAISY Jobs",
                epub3_daisy_jobs,
                lp_steps,
                "No EPUB3 / DAISY jobs yet.",
                "bg-teal-500",
                "EPUB3 / DAISY",
                "job_type",
            )
            _recent_job_card(
                "Recent Tactile Graphics Jobs",
                tactile_jobs,
                tactile_steps,
                "No tactile graphics jobs yet.",
                "bg-rose-500",
                "Tactile Graphics",
                "tactile_type",
            )
            _recent_job_card(
                "Recent 3-D Print Jobs",
                print_jobs,
                [],
                "No 3-D print jobs yet.",
                "bg-amber-500",
                "3-D Print",
                "object_name",
            )

        # ── Recent QA / pipeline activity ──────────────────────────────────────
        with ui.row().classes("gap-6 flex-wrap items-start mt-6"):
            with ui.card().classes(
                "flex-1 min-w-72 p-5 rounded-xl shadow-sm border border-slate-200"
            ):
                ui.label("Recent QA Runs").classes(
                    "text-base font-semibold text-slate-700 mb-3"
                )
                if not recent_qa:
                    ui.label("No QA runs recorded yet.").classes("text-slate-400 text-sm")
                else:
                    for run in recent_qa:
                        ok = bool(run.get("success"))
                        with ui.row().classes(
                            "items-center gap-2 py-1 border-b border-slate-50 last:border-0"
                        ):
                            ui.label("✅" if ok else "❌")
                            ui.label(run.get("tool_name", "—")).classes(
                                "text-sm text-slate-700 flex-1"
                            )
                            ui.label(str(run.get("ran_at", ""))[:10]).classes(
                                "text-xs text-slate-400"
                            )

            with ui.card().classes(
                "flex-1 min-w-72 p-5 rounded-xl shadow-sm border border-slate-200"
            ):
                ui.label("Recent Pipeline Runs").classes(
                    "text-base font-semibold text-slate-700 mb-3"
                )
                if not recent_pipelines:
                    ui.label("No pipeline runs recorded yet.").classes(
                        "text-slate-400 text-sm"
                    )
                else:
                    for run in recent_pipelines:
                        ok = run.get("status") == "completed"
                        with ui.row().classes(
                            "items-center gap-2 py-1 border-b border-slate-50 last:border-0"
                        ):
                            ui.label("✅" if ok else "❌")
                            ui.label(run.get("pipeline_name", "—")).classes(
                                "text-sm text-slate-700 flex-1 truncate"
                            )
                            ui.badge(run.get("status", "?")).classes(
                                "text-xs bg-slate-100 text-slate-600 rounded px-1"
                            )
