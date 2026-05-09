"""Main NiceGUI entrypoint for the Accessibility Project Manager."""

from __future__ import annotations

import inspect
from importlib import import_module
from typing import Callable

from nicegui import ui

from db.database import init_db

APP_TITLE = "Accessibility Project Manager"

PAGE_DEFINITIONS = [
    {
        "name": "Dashboard",
        "icon": "dashboard",
        "module": "ui.dashboard",
        "function": "dashboard_page",
        "description": "Studio overview and active work summary",
    },
    {
        "name": "Asset Registry",
        "icon": "account_tree",
        "module": "ui.assets",
        "function": "assets_page",
        "description": "Metadata-rich digital and physical asset tracking",
    },
    {
        "name": "Braille Workflow",
        "icon": "article",
        "module": "ui.workflow_braille",
        "function": "workflow_braille_page",
        "description": "Braille workflow execution and tracking",
    },
    {
        "name": "3D Printing Workflow",
        "icon": "print",
        "module": "ui.workflow_printing",
        "function": "workflow_printing_page",
        "description": "3D fabrication workflow execution",
    },
    {
        "name": "Metadata Editor",
        "icon": "edit_note",
        "module": "ui.metadata_editor",
        "function": "metadata_editor_page",
        "description": "Metadata editing and validation",
    },
    {
        "name": "File Ingestion",
        "icon": "upload_file",
        "module": "ui.ingestion",
        "function": "ingestion_page",
        "description": "Preservation-aware ingestion pipelines",
    },
    {
        "name": "Lineage Viewer",
        "icon": "share",
        "module": "ui.lineage",
        "function": "lineage_page",
        "description": "Derivative lineage and provenance visualization",
    },
]


def load_page_handler(module_name: str, function_name: str) -> Callable | None:
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


def render_page(content: ui.column, page: dict) -> None:
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
                ui.label("Unable to load page").classes("text-red-700")
                ui.label(str(exc)).classes("text-sm text-red-600")


@ui.page("/")
def index() -> None:
    ui.page_title(APP_TITLE)

    with ui.row().classes("w-full no-wrap"):
        with ui.column().classes(
            "h-screen w-80 bg-slate-900 text-white p-4 gap-2 shadow-xl"
        ):
            ui.label(APP_TITLE).classes("text-2xl font-bold")
            ui.label("Accessibility Workflow Platform").classes(
                "text-xs text-slate-300 mb-4"
            )

            for page in PAGES:
                ui.button(
                    page["name"],
                    icon=page["icon"],
                    on_click=lambda p=page: render_page(content_area, p),
                ).props("flat align=left").classes(
                    "w-full justify-start text-left"
                )

            ui.separator().classes("bg-slate-700 my-4")

            with ui.card().classes("bg-slate-800 text-white w-full"):
                ui.label("Workflow Domains").classes("font-semibold")
                ui.markdown(
                    """
                    - Braille Production
                    - Accessible Documents
                    - eBraille
                    - Tactile Graphics
                    - 3D Fabrication
                    - Metadata Preservation
                    """
                )

        with ui.column().classes("flex-1 h-screen overflow-auto bg-slate-50"):
            content_area = ui.column().classes("w-full p-6 gap-4")

            if PAGES:
                render_page(content_area, PAGES[0])


ui.run(title=APP_TITLE, reload=False, favicon="♿", show=False)
