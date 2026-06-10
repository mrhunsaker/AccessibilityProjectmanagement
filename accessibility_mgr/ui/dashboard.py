"""Dashboard — operational overview of the accessibility studio."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

from nicegui import ui

from ..db import queries as Q
from .braille_jobs import braille_jobs_page
from .components import PRIORITY_COLORS, notify_error, notify_success, section_header
from .lp_ebraille import (
    ebraille_jobs_page,
    epub3_daisy_jobs_page,
    large_print_jobs_page,
)
from .print_jobs import print_jobs_page
from .reports import reports_page
from .tactile_graphics import tactile_graphics_page
from .inventory_panels import filament_page, paper_page


def _is_overdue(job: dict) -> bool:
    due_date = (job.get("due_date") or "").strip()
    if not due_date:
        return False
    if int(job.get("delivered") or 0) == 1:
        return False
    try:
        return date.fromisoformat(due_date) < date.today()
    except ValueError:
        return False


def _open_quick_create_dialog(content_area: ui.element) -> None:
    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[520px] max-w-full"):
        ui.label("Quick Create Job").classes("text-xl font-bold text-slate-800")
        ui.label("Create a job with minimum required fields.").classes(
            "text-sm text-slate-500"
        )

        type_map = {
            "Braille": "braille",
            "Large Print": "large_print",
            "eBraille": "ebraille",
            "EPUB3 / DAISY": "epub3_daisy",
            "Tactile": "tactile",
            "3-D Print": "print",
        }
        type_select = ui.select(
            list(type_map.keys()),
            label="Job Type",
            value="Braille",
        ).classes("w-full")
        title_input = ui.input("Title*").classes("w-full")
        requester_input = ui.input("Requester").classes("w-full")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _save() -> None:
                title = (title_input.value or "").strip()
                if not title:
                    notify_error("Title is required")
                    return
                requester = (requester_input.value or "").strip()
                job_kind = type_map.get(type_select.value, "braille")

                try:
                    if job_kind == "braille":
                        Q.add_braille_job(
                            title=title,
                            braille_type="literary",
                            requester=requester,
                            priority="normal",
                        )
                        braille_jobs_page(content_area)
                    elif job_kind in {"large_print", "ebraille", "epub3_daisy"}:
                        Q.add_lp_job(
                            title=title,
                            job_type=job_kind,
                            requester=requester,
                            priority="normal",
                        )
                        if job_kind == "large_print":
                            large_print_jobs_page(content_area)
                        elif job_kind == "ebraille":
                            ebraille_jobs_page(content_area)
                        else:
                            epub3_daisy_jobs_page(content_area)
                    elif job_kind == "tactile":
                        Q.add_tactile_job(
                            title=title,
                            tactile_type="thermoform_swell",
                            requester=requester,
                            priority="normal",
                        )
                        tactile_graphics_page(content_area)
                    else:
                        printers = Q.list_printers()
                        if not printers:
                            notify_error("No printer configured; add one in Admin Settings")
                            return
                        filaments = Q.list_filaments()
                        Q.add_print_job(
                            printer_id=printers[0]["id"],
                            filament_id=filaments[0]["id"] if filaments else None,
                            filament_used_g=0,
                            object_name=title,
                            requester=requester,
                        )
                        print_jobs_page(content_area)

                    notify_success("Job created")
                    dlg.close()
                except Exception as exc:  # noqa: BLE001
                    notify_error(f"Could not create job: {exc}")

            ui.button("Create", on_click=_save).classes("bg-blue-600 text-white")

    dlg.open()


def _stat_card(
    label: str,
    value: Any,
    color: str = "blue",
    icon: str = "",
    on_click: Callable[[], None] | None = None,
) -> None:
    colors = {
        "blue": ("bg-blue-50", "text-blue-600", "border-blue-200"),
        "green": ("bg-green-50", "text-green-600", "border-green-200"),
        "amber": ("bg-amber-50", "text-amber-600", "border-amber-200"),
        "purple": ("bg-purple-50", "text-purple-600", "border-purple-200"),
        "red": ("bg-red-50", "text-red-600", "border-red-200"),
    }
    bg, text, border = colors.get(color, colors["blue"])

    card_classes = f"p-4 {bg} border {border} rounded-xl shadow-sm"
    if on_click:
        card_classes += " cursor-pointer hover:shadow-md transition-all"

    with ui.card().classes(card_classes) as card:
        if icon:
            ui.label(icon).classes("text-2xl mb-1")

        ui.label(str(value)).classes(f"text-3xl font-bold {text}")
        ui.label(label).classes("text-slate-600 text-sm mt-1")

    if on_click:
        card.on("click", lambda _: on_click())


def _recent_job_card(
    title: str,
    jobs: list[dict],
    steps: list[str],
    empty_text: str,
    progress_color: str,
    job_type_label: str,
    type_key: str,
) -> None:
    with ui.card().classes(
        "flex-1 min-w-80 p-5 rounded-xl shadow-sm border border-slate-200"
    ):
        ui.label(title).classes("text-base font-semibold text-slate-700 mb-3")

        if not jobs:
            ui.label(empty_text).classes("text-slate-400 text-sm")
            return

        for job in jobs[:8]:
            done = sum(job.get(step, 0) for step in steps)
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
    content_area.clear()

    with content_area:
        ui.keyboard(
            on_key=lambda e: _open_quick_create_dialog(content_area)
            if getattr(e, "action", "") == "keydown"
            and str(getattr(e, "key", "")).lower() == "n"
            else None
        )

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
        tactile_steps = ["designed", "produced", "qa_reviewed", "delivered"]

        in_progress_b = sum(
            1 for job in braille_jobs
            if 0 < sum(job.get(step, 0) for step in b_steps) < len(b_steps)
        )

        in_progress_lp = sum(
            1 for job in lp_jobs
            if 0 < sum(job.get(step, 0) for step in lp_steps) < len(lp_steps)
        )

        in_progress_ebraille = sum(
            1 for job in ebraille_jobs
            if 0 < sum(job.get(step, 0) for step in lp_steps) < len(lp_steps)
        )

        in_progress_epub3_daisy = sum(
            1 for job in epub3_daisy_jobs
            if 0 < sum(job.get(step, 0) for step in lp_steps) < len(lp_steps)
        )

        in_progress_tactile = sum(
            1 for job in tactile_jobs
            if 0 < sum(job.get(step, 0) for step in tactile_steps) < len(tactile_steps)
        )

        urgent = [
            job
            for job in (
                braille_jobs
                + lp_jobs
                + ebraille_jobs
                + epub3_daisy_jobs
                + tactile_jobs
            )
            if job.get("priority") == "urgent"
        ]

        low_filament = [f for f in filaments if f.get("quantity_g", 0) < 100]
        low_paper = [p for p in paper if p.get("quantity", 0) < 50]
        upcoming_deadlines: list[dict] = []
        for job_type, rows in (
            ("Braille", braille_jobs),
            ("Large Print", lp_jobs),
            ("eBraille", ebraille_jobs),
            ("EPUB3 / DAISY", epub3_daisy_jobs),
            ("Tactile", tactile_jobs),
        ):
            for row in rows:
                due = (row.get("due_date") or "").strip()
                if not due:
                    continue
                if int(row.get("delivered") or 0) == 1:
                    continue
                upcoming_deadlines.append(
                    {
                        "job_type": job_type,
                        "title": row.get("title") or "(untitled)",
                        "due_date": due,
                        "priority": row.get("priority") or "normal",
                        "overdue": _is_overdue(row),
                    }
                )
        upcoming_deadlines.sort(key=lambda item: item["due_date"])

        with ui.row().classes("gap-4 flex-wrap mb-8"):
            _stat_card(
                "Braille Jobs",
                len(braille_jobs),
                "purple",
                "⠿",
                on_click=lambda: braille_jobs_page(content_area),
            )
            _stat_card(
                "In Progress",
                in_progress_b
                + in_progress_lp
                + in_progress_ebraille
                + in_progress_epub3_daisy
                + in_progress_tactile,
                "blue",
                "⏳",
                on_click=lambda: reports_page(content_area, presets={"status": "in_progress"}),
            )
            _stat_card(
                "Large Print",
                len(lp_jobs),
                "green",
                "🔠",
                on_click=lambda: large_print_jobs_page(content_area),
            )
            _stat_card(
                "eBraille",
                len(ebraille_jobs),
                "green",
                "⠮",
                on_click=lambda: ebraille_jobs_page(content_area),
            )
            _stat_card(
                "EPUB3/DAISY",
                len(epub3_daisy_jobs),
                "green",
                "📚",
                on_click=lambda: epub3_daisy_jobs_page(content_area),
            )
            _stat_card(
                "Tactile",
                len(tactile_jobs),
                "red",
                "▦",
                on_click=lambda: tactile_graphics_page(content_area),
            )
            _stat_card(
                "Print Jobs",
                len(print_jobs),
                "amber",
                "🖨️",
                on_click=lambda: print_jobs_page(content_area),
            )
            _stat_card(
                "Urgent",
                len(urgent),
                "red",
                "🚨",
                on_click=lambda: reports_page(content_area, presets={"priority": "urgent"}),
            )
            _stat_card(
                "Low Stock",
                len(low_filament) + len(low_paper),
                "amber",
                "⚠️",
                on_click=lambda: filament_page(content_area)
                if len(low_filament) >= len(low_paper)
                else paper_page(content_area),
            )

        with ui.card().classes(
            "mb-6 p-5 rounded-xl shadow-sm border border-slate-200"
        ):
            ui.label("Quick Launch").classes("text-base font-semibold text-slate-700 mb-2")
            ui.label("Jump directly to key production job pages.").classes(
                "text-sm text-slate-500 mb-3"
            )

            with ui.row().classes("gap-2 flex-wrap"):
                ui.button(
                    "Braille Jobs",
                    on_click=lambda: braille_jobs_page(content_area),
                ).classes("bg-indigo-600 text-white")

                ui.button(
                    "Large Print Jobs",
                    on_click=lambda: large_print_jobs_page(content_area),
                ).classes("bg-green-600 text-white")

                ui.button(
                    "eBraille Jobs",
                    on_click=lambda: ebraille_jobs_page(content_area),
                ).classes("bg-emerald-600 text-white")

                ui.button(
                    "EPUB3 / DAISY Jobs",
                    on_click=lambda: epub3_daisy_jobs_page(content_area),
                ).classes("bg-teal-600 text-white")

                ui.button(
                    "Tactile Graphics",
                    on_click=lambda: tactile_graphics_page(content_area),
                ).classes("bg-rose-600 text-white")

        with ui.card().classes(
            "mb-6 p-5 rounded-xl shadow-sm border border-slate-200"
        ):
            ui.label("Upcoming Deadlines").classes("text-base font-semibold text-slate-700 mb-2")
            if not upcoming_deadlines:
                ui.label("No undelivered jobs with due dates.").classes("text-sm text-slate-400")
            else:
                for entry in upcoming_deadlines[:10]:
                    with ui.row().classes(
                        "items-center gap-3 py-2 border-b border-slate-100 last:border-0"
                    ):
                        with ui.column().classes("flex-1 gap-0"):
                            ui.label(entry["title"]).classes(
                                "text-sm font-medium text-slate-700 truncate"
                            )
                            ui.label(entry["job_type"]).classes("text-xs text-slate-400")
                        priority_color = PRIORITY_COLORS.get(
                            str(entry.get("priority", "normal")),
                            "bg-slate-100 text-slate-700",
                        )
                        ui.badge(str(entry.get("priority", "normal")).capitalize()).classes(
                            f"text-xs rounded px-2 {priority_color}"
                        )
                        due_classes = "text-xs text-red-600 font-semibold" if entry[
                            "overdue"
                        ] else "text-xs text-slate-500"
                        due_prefix = "Overdue" if entry["overdue"] else "Due"
                        ui.label(f"{due_prefix}: {entry['due_date']}").classes(due_classes)

        ui.button(
            icon="add",
            on_click=lambda: _open_quick_create_dialog(content_area),
        ).props("round color=indigo").classes(
            "fixed bottom-24 right-8 z-50 shadow-lg"
        ).tooltip("Quick create job")
