"""
Accessibility Project Manager — NiceGUI application entry point.

All pages are registered here in PAGE_DEFINITIONS and rendered via the
sidebar.  The database is initialised once on startup via db.schema.init_db().
"""

from __future__ import annotations

import inspect
from importlib import import_module
from pathlib import Path
from typing import Callable

from nicegui import app as nicegui_app
from nicegui import ui

from accessibility_mgr.db.schema import init_db
from accessibility_mgr.services import tools_service

APP_TITLE = "Accessibility Document Generation Project Manager"

# ── Page registry ─────────────────────────────────────────────────────────────
# Each entry: name, icon (Material), module, function, description, group.
# Groups determine sidebar sections.

PAGE_DEFINITIONS: list[dict] = [
    # ── Overview ──────────────────────────────────────────────────────────────
    {
        "name": "Dashboard",
        "icon": "dashboard",
        "module": "ui.dashboard",
        "function": "dashboard_page",
        "description": "Studio overview and active work summary",
        "group": "Overview",
    },
    {
        "name": "Search",
        "icon": "search",
        "module": "ui.search",
        "function": "search_page",
        "description": "Search jobs, files, and metadata",
        "group": "Overview",
    },
    # ── Production Jobs ───────────────────────────────────────────────────────
    {
        "name": "Braille Jobs",
        "icon": "article",
        "module": "ui.braille_jobs",
        "function": "braille_jobs_page",
        "description": "Braille transcription workflow tracking",
        "group": "Production",
    },
    {
        "name": "Large Print Jobs",
        "icon": "format_size",
        "module": "ui.lp_ebraille",
        "function": "large_print_jobs_page",
        "description": "Large print workflow tracking",
        "group": "Production",
    },
    {
        "name": "eBraille Jobs",
        "icon": "menu_book",
        "module": "ui.lp_ebraille",
        "function": "ebraille_jobs_page",
        "description": "eBraille workflow tracking",
        "group": "Production",
    },
    {
        "name": "Tactile Graphics",
        "icon": "texture",
        "module": "ui.tactile_graphics",
        "function": "tactile_graphics_page",
        "description": "Thermoform, hand-tooled, and embossed figure tracking",
        "group": "Production",
    },
    {
        "name": "3-D Print Jobs",
        "icon": "print",
        "module": "ui.print_jobs",
        "function": "print_jobs_page",
        "description": "3-D fabrication job tracking",
        "group": "Production",
    },
    # ── Inventory ─────────────────────────────────────────────────────────────
    {
        "name": "Filament",
        "icon": "cable",
        "module": "ui.inventory_panels",
        "function": "filament_page",
        "description": "3-D printer filament inventory",
        "group": "Inventory",
    },
    {
        "name": "Braille Paper",
        "icon": "inventory_2",
        "module": "ui.inventory_panels",
        "function": "paper_page",
        "description": "Braille paper and label stock",
        "group": "Inventory",
    },
    {
        "name": "Electronics",
        "icon": "memory",
        "module": "ui.inventory_panels",
        "function": "electronics_page",
        "description": "Electronics and assembly components",
        "group": "Inventory",
    },
    # ── Metadata & Files ──────────────────────────────────────────────────────
    {
        "name": "File Ingestion",
        "icon": "upload_file",
        "module": "ui.ingestion",
        "function": "ingestion_page",
        "description": "Preservation-aware file ingestion",
        "group": "Metadata & Files",
    },
    {
        "name": "Metadata Editor",
        "icon": "edit_note",
        "module": "ui.metadata_editor",
        "function": "metadata_editor_page",
        "description": "Dublin Core and custom metadata editing",
        "group": "Metadata & Files",
    },
    {
        "name": "Lineage Viewer",
        "icon": "share",
        "module": "ui.lineage",
        "function": "lineage_page",
        "description": "File lineage and provenance graph",
        "group": "Metadata & Files",
    },
    # ── QA & Automation ───────────────────────────────────────────────────────
    {
        "name": "QA Tooling",
        "icon": "verified",
        "module": "ui.qa",
        "function": "qa_page",
        "description": "Accessibility validation tools",
        "group": "QA & Automation",
    },
    {
        "name": "Pipelines",
        "icon": "account_tree",
        "module": "ui.pipelines",
        "function": "pipelines_page",
        "description": "Multi-stage workflow automation",
        "group": "QA & Automation",
    },
    # ── Admin ─────────────────────────────────────────────────────────────────
    {
        "name": "Admin Settings",
        "icon": "settings",
        "module": "ui.admin",
        "function": "admin_page",
        "description": "Material categories, steps, printers, and embossers",
        "group": "Admin",
    },
]


def _load_handler(module_name: str, function_name: str) -> Callable | None:
    try:
        mod = import_module(module_name)
    except Exception as exc:
        print(f"[app] Could not import {module_name}: {exc}")
        return None
    return getattr(mod, function_name, None)


# Resolve handlers at startup
PAGES: list[dict] = []
for _defn in PAGE_DEFINITIONS:
    _handler = _load_handler(_defn["module"], _defn["function"])
    if _handler is not None:
        PAGES.append({**_defn, "handler": _handler})
    else:
        print(f"[app] WARNING: handler not found for {_defn['name']}")


tools_service.bootstrap()
init_db()


# ── Rendering ─────────────────────────────────────────────────────────────────

def render_page(content: ui.column, page: dict) -> None:
    content.clear()
    handler = page["handler"]
    try:
        sig = inspect.signature(handler)
        if len(sig.parameters) == 0:
            with content:
                handler()
        else:
            handler(content)
    except Exception as exc:
        import traceback
        content.clear()
        with content, ui.card().classes("w-full border border-red-200 bg-red-50 p-4 rounded-xl"):
                ui.label(f"Error loading '{page['name']}'").classes(
                    "text-red-700 font-semibold"
                )
                ui.label(str(exc)).classes("text-sm text-red-600 mt-1")
                ui.code(traceback.format_exc()).classes("text-xs mt-2 overflow-auto max-h-48")


# ── Shutdown handler ─────────────────────────────────────────────────────────

def _shutdown() -> None:
    """Gracefully shutdown the app."""
    ui.notify("Shutting down...", position="top")
    nicegui_app.shutdown()


# ── Main page ─────────────────────────────────────────────────────────────────

@ui.page("/")
def index() -> None:
    ui.page_title(APP_TITLE)

    # Group pages by their group label
    groups: dict[str, list[dict]] = {}
    for page in PAGES:
        groups.setdefault(page["group"], []).append(page)

    with ui.column().classes("w-full h-[100dvh] overflow-hidden min-h-0"):
        # ── Header with shutdown button ───────────────────────────────────────
        with ui.row().classes(
            "w-full bg-white border-b border-slate-200 px-6 py-3 items-center justify-end shadow-sm"
        ):
            ui.button(
                icon="logout",
                on_click=_shutdown,
            ).props("flat round dense").classes(
                "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            ).tooltip("Shutdown app")

        with ui.row().classes("flex-1 w-full no-wrap overflow-hidden min-h-0"):

            # ── Sidebar ───────────────────────────────────────────────────────────
            with ui.column().classes(
                "h-full bg-slate-900 text-white p-4 gap-1 shadow-xl overflow-y-auto min-h-0"
            ).style("min-width:240px; max-width:240px"):

                ui.label(APP_TITLE).classes("text-lg font-bold leading-tight mb-1")
                ui.label("Accessibility Workflow Platform").classes(
                    "text-xs text-slate-400 mb-4"
                )

                active_page: list[dict | None] = [None]
                btn_refs: dict[str, ui.button] = {}

                for group_name, group_pages in groups.items():
                    ui.label(group_name).classes(
                        "text-xs text-slate-400 uppercase tracking-widest mt-3 mb-1 px-2"
                    )
                    for page in group_pages:
                        def _make_click(p: dict) -> Callable:
                            def _click() -> None:
                                # Reset all buttons
                                for b in btn_refs.values():
                                    b.classes(
                                        remove="bg-slate-700 text-white",
                                        add="text-slate-300",
                                    )
                                # Highlight active
                                btn_refs[p["name"]].classes(
                                    remove="text-slate-300",
                                    add="bg-slate-700 text-white",
                                )
                                active_page[0] = p
                                render_page(content_area, p)

                            return _click

                        btn = (
                            ui.button(
                                page["name"],
                                icon=page["icon"],
                                on_click=_make_click(page),
                            )
                            .props("flat align=left")
                            .classes(
                                "w-full justify-start text-left text-slate-300 "
                                "hover:bg-slate-700 hover:text-white rounded-lg px-2 py-1"
                            )
                        )
                        btn_refs[page["name"]] = btn

            # ── Content area ──────────────────────────────────────────────────────
            with ui.column().classes(
                "flex-1 h-full overflow-auto bg-slate-50 min-h-0"
            ):
                content_area = ui.column().classes("w-full p-6 pb-20 gap-4 min-h-0")

                # Render first page on load
                if PAGES:
                    first = PAGES[0]
                    btn_refs[first["name"]].classes(
                        remove="text-slate-300",
                        add="bg-slate-700 text-white",
                    )
                    render_page(content_area, first)

        # ── Footer ────────────────────────────────────────────────────────────
        with ui.row().classes(
            "w-full shrink-0 items-center justify-between gap-4 border-t border-slate-200 bg-white px-6 py-3 text-xs text-slate-500"
        ):
            ui.link(
                "Repository",
                "https://github.com/mrhunsaker/AccessibilityProjectmanagement",
            ).classes("text-slate-600 hover:text-slate-900")
            ui.label("© 2026 Michael Ryan Hunsaker. Accessibility Project Management.")
            ui.link(
                "Documentation",
                "https://mrhunsaker.github.io/AccessibilityProjectmanagement/",
            ).classes("text-slate-600 hover:text-slate-900")


def main() -> None:
    """Console-script entry point for `uv run AccessMan`."""
    favicon_path = Path(__file__).parent.parent / "resources/icons/favicon.svg"
    ui.run(
        title=APP_TITLE,
        reload=False,
        favicon=str(favicon_path),
        show=False,
        port=8765,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
