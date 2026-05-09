"""Main NiceGUI entrypoint for the Accessibility Project Manager.

This module replaces the placeholder implementation with a functional
application shell that mirrors the original TUI workflow while integrating
all available NiceGUI pages in the repository.
"""

from __future__ import annotations

import inspect
from importlib import import_module
from typing import Callable

from nicegui import ui

from db.database import init_db

APP_TITLE = "Accessibility Project Manager"

# Ordered to roughly match the original TUI navigation.
PAGE_DEFINITIONS = [
    {
        "name": "Dashboard",
        "icon": "dashboard",
        "module": "ui.dashboard",
        "function": "dashboard_page",
        "description": "Studio overview and active work summary",
    },
    {
        "name": "Inventory",
        "icon": "inventory_2",
        "module": "ui.inventory",
        "function": "inventory_page",
        "description": "Filament, paper, electronics, and supply tracking",
    },
    {
        "name": "Categories",
        "icon": "category",
        "module": "ui.categories",
        "function": "categories_page",
        "description": "Inventory categories and organization",
    },
    {
        "name": "3-D Print Jobs",
        "icon": "print",
        "module": "ui.print_jobs",
        "function": "print_jobs_page",
        "description": "Printer jobs, filament usage, and print history",
    },
    {
        "name": "Braille Jobs",
        "icon": "article",
        "module": "ui.braille_jobs",
        "function": "braille_jobs_page",
        "description": "Braille production workflow tracking",
    },
    {
        "name": "LP / eBraille",
        "icon": "menu_book",
        "module": "ui.lp_jobs",
        "function": "lp_jobs_page",
        "description": "Large print and eBraille production",
    },
    {
        "name": "Transactions",
        "icon": "receipt_long",
        "module": "ui.transactions",
        "function": "transactions_page",
        "description": "Inventory movement and historical changes",
    },
]


def load_page_handler(module_name: str, function_name: str) -> Callable | None:
    """Load a page renderer if the module exists in the repo."""

    try:
        module = import_module(module_name)
    except Exception:
        return None

    return getattr(module, function_name, None)


PAGES: list[dict] = []

for definition in PAGE_DEFINITIONS:
    handler = load_page_handler(definition["module"], definition["function"])
    if handler:
        PAGES.append({**definition, "handler": handler})


init_db()

ui.colors(
    primary="#2563eb",
    secondary="#475569",
    accent="#7c3aed",
    positive="#16a34a",
    negative="#dc2626",
    warning="#d97706",
)


def render_page(content: ui.column, page: dict) -> None:
    """Render a page function regardless of its expected signature."""

    content.clear()

    with content:
        ui.label(page["name"]).classes("text-3xl font-bold text-slate-800")
        ui.label(page["description"]).classes("text-sm text-slate-500 mb-4")

    handler = page["handler"]

    try:
        params = inspect.signature(handler).parameters

        if len(params) == 0:
            with content:
                handler()
        else:
            handler(content)

    except Exception as exc:
        with content:
            with ui.card().classes("w-full border border-red-200 bg-red-50"):
                ui.label("Unable to load page").classes("text-red-700 font-semibold")
                ui.label(str(exc)).classes("text-red-600 text-sm")


@ui.page("/")
def index() -> None:
    ui.page_title(APP_TITLE)

    with ui.row().classes("w-full no-wrap"):
        with ui.column().classes(
            "h-screen w-72 bg-slate-900 text-white p-4 gap-1 shadow-xl"
        ):
            ui.label(APP_TITLE).classes("text-2xl font-bold")
            ui.label("Braille & Maker Studio Workflow").classes(
                "text-xs text-slate-300 mb-4"
            )

            content = ui.column().classes("w-full")

            for page in PAGES:
                ui.button(
                    page["name"],
                    icon=page["icon"],
                    on_click=lambda p=page: render_page(content_area, p),
                ).props("flat align=left").classes(
                    "w-full justify-start text-left"
                )

            ui.separator().classes("my-4 bg-slate-700")

            with ui.card().classes("bg-slate-800 text-white w-full"):
                ui.label("Production Areas").classes("font-semibold")
                ui.markdown(
                    """
                    - Braille Production
                    - Large Print / eBraille
                    - 3-D Print Fabrication
                    - Inventory & Supplies
                    """
                )

        with ui.column().classes("flex-1 h-screen overflow-auto bg-slate-50"):
            with ui.header(elevated=True).classes(
                "bg-white text-slate-800 border-b border-slate-200"
            ):
                with ui.row().classes("w-full items-center justify-between px-4"):
                    with ui.column().classes("gap-0"):
                        ui.label(APP_TITLE).classes("text-lg font-semibold")
                        ui.label(
                            "Accessible project tracking and inventory management"
                        ).classes("text-xs text-slate-500")

                    with ui.row().classes("items-center gap-2"):
                        ui.badge("NiceGUI Frontend").classes(
                            "bg-blue-100 text-blue-700"
                        )
                        ui.badge("SQLite Backend").classes(
                            "bg-green-100 text-green-700"
                        )

            content_area = ui.column().classes("w-full p-6 gap-4")

            if PAGES:
                render_page(content_area, PAGES[0])
            else:
                with content_area:
                    with ui.card().classes("w-full"):
                        ui.label("No UI modules detected").classes(
                            "text-lg font-semibold"
                        )
                        ui.label(
                            "Create page modules under accessibility_mgr/ui to populate the application shell."
                        ).classes("text-slate-500")


ui.run(
    title=APP_TITLE,
    reload=False,
    favicon="♿",
    show=False,
)
