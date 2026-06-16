"""
Accessibility Project Manager — NiceGUI application entry point.

Changes applied (see fix_specs.json):
  FIX-010  Students page added to Production group.
  FIX-015  Reports page added to Overview group.
"""

from __future__ import annotations

import os
import inspect
from importlib import import_module
from pathlib import Path
from typing import Callable
import logging

from nicegui import app as nicegui_app
from nicegui import ui

log = logging.getLogger(__name__)

from accessibility_mgr.api.platform_api import app as platform_api_app
from accessibility_mgr.db.schema import DB_PATH, init_db
from accessibility_mgr.services import tools_service
from accessibility_mgr.services.backup_service import BackupService

APP_TITLE = "Accessibility Document Generation Project Manager"

PAGE_DEFINITIONS: list[dict] = [
    # ── Overview ──────────────────────────────────────────────────────────────
    {
        "name": "Dashboard",
        "icon": "dashboard",
        "module": "accessibility_mgr.ui.dashboard",
        "function": "dashboard_page",
        "description": "Studio overview and active work summary",
        "group": "Overview",
    },
    {
        "name": "Search",
        "icon": "search",
        "module": "accessibility_mgr.ui.search",
        "function": "search_page",
        "description": "Search jobs, files, metadata, and event log",
        "group": "Overview",
    },
    {
        "name": "Reports",                          # FIX-015
        "icon": "summarize",
        "module": "accessibility_mgr.ui.reports",
        "function": "reports_page",
        "description": "Filter and export jobs by school, grade, type, and status",
        "group": "Overview",
    },
    {
        "name": "Operations",
        "icon": "insights",
        "module": "accessibility_mgr.ui.operations_dashboard",
        "function": "operations_dashboard_page",
        "description": "Operational KPI and analytics dashboard",
        "group": "Overview",
    },
    # ── Production Jobs ───────────────────────────────────────────────────────
    {
        "name": "Students",                         # FIX-010
        "icon": "person",
        "module": "accessibility_mgr.ui.students",
        "function": "students_page",
        "description": "Student records and cross-job production history",
        "group": "Production",
    },
    {
        "name": "Braille Jobs",
        "icon": "article",
        "module": "accessibility_mgr.ui.braille_jobs",
        "function": "braille_jobs_page",
        "description": "Braille transcription workflow tracking",
        "group": "Production",
    },
    {
        "name": "Large Print Jobs",
        "icon": "format_size",
        "module": "accessibility_mgr.ui.lp_ebraille",
        "function": "large_print_jobs_page",
        "description": "Large print workflow tracking",
        "group": "Production",
    },
    {
        "name": "eBraille Jobs",
        "icon": "menu_book",
        "module": "accessibility_mgr.ui.lp_ebraille",
        "function": "ebraille_jobs_page",
        "description": "eBraille workflow tracking",
        "group": "Production",
    },
    {
        "name": "EPUB3 / DAISY Jobs",
        "icon": "import_contacts",
        "module": "accessibility_mgr.ui.lp_ebraille",
        "function": "epub3_daisy_jobs_page",
        "description": "EPUB3 and DAISY workflow tracking",
        "group": "Production",
    },
    {
        "name": "Tactile Graphics",
        "icon": "texture",
        "module": "accessibility_mgr.ui.tactile_graphics",
        "function": "tactile_graphics_page",
        "description": "Thermoform, hand-tooled, and embossed figure tracking",
        "group": "Production",
    },
    {
        "name": "3-D Print Jobs",
        "icon": "print",
        "module": "accessibility_mgr.ui.print_jobs",
        "function": "print_jobs_page",
        "description": "3-D fabrication job tracking",
        "group": "Production",
    },
    # ── Inventory ─────────────────────────────────────────────────────────────
    {
        "name": "Filament",
        "icon": "cable",
        "module": "accessibility_mgr.ui.inventory_panels",
        "function": "filament_page",
        "description": "3-D printer filament inventory",
        "group": "Inventory",
    },
    {
        "name": "Braille Paper",
        "icon": "inventory_2",
        "module": "accessibility_mgr.ui.inventory_panels",
        "function": "paper_page",
        "description": "Braille paper and label stock",
        "group": "Inventory",
    },
    {
        "name": "Electronics",
        "icon": "memory",
        "module": "accessibility_mgr.ui.inventory_panels",
        "function": "electronics_page",
        "description": "Electronics and assembly components",
        "group": "Inventory",
    },
    # ── Metadata & Files ──────────────────────────────────────────────────────
    {
        "name": "File Ingestion",
        "icon": "upload_file",
        "module": "accessibility_mgr.ui.ingestion",
        "function": "ingestion_page",
        "description": "Preservation-aware file ingestion",
        "group": "Metadata & Files",
    },
    {
        "name": "Metadata Editor",
        "icon": "edit_note",
        "module": "accessibility_mgr.ui.metadata_editor",
        "function": "metadata_editor_page",
        "description": "Dublin Core and custom metadata editing",
        "group": "Metadata & Files",
    },
    {
        "name": "Lineage Viewer",
        "icon": "share",
        "module": "accessibility_mgr.ui.lineage",
        "function": "lineage_page",
        "description": "File lineage and provenance graph",
        "group": "Metadata & Files",
    },
    # ── QA & Automation ───────────────────────────────────────────────────────
    {
        "name": "QA Tooling",
        "icon": "verified",
        "module": "accessibility_mgr.ui.qa",
        "function": "qa_page",
        "description": "Accessibility validation tools",
        "group": "QA & Automation",
    },
    {
        "name": "Pipelines",
        "icon": "account_tree",
        "module": "accessibility_mgr.ui.pipelines",
        "function": "pipelines_page",
        "description": "Multi-stage workflow automation",
        "group": "QA & Automation",
    },
    # ── Admin ─────────────────────────────────────────────────────────────────
    {
        "name": "Admin Settings",
        "icon": "settings",
        "module": "accessibility_mgr.ui.admin",
        "function": "admin_page",
        "description": "Categories, metadata, steps, printers, embossers, and backups",
        "group": "Admin",
    },
    {
        "name": "Security Dashboard",
        "icon": "security",
        "module": "accessibility_mgr.ui.security_dashboard",
        "function": "security_dashboard_page",
        "description": "Role and authorization visibility",
        "group": "Admin",
    },
]


def _load_handler(module_name: str, function_name: str) -> Callable | None:
    try:
        mod = import_module(module_name)
    except Exception as exc:
        log.error("Could not import %s: %s", module_name, exc)
        return None
    return getattr(mod, function_name, None)


PAGES: list[dict] = []
FAILED_PAGES: list[dict] = []
for _defn in PAGE_DEFINITIONS:
    _handler = _load_handler(_defn["module"], _defn["function"])
    if _handler is not None:
        PAGES.append({**_defn, "handler": _handler})
    else:
        log.error("Handler not found for page '%s' (%s.%s)", _defn["name"], _defn["module"], _defn["function"])
        FAILED_PAGES.append(_defn)


tools_service.bootstrap()
init_db()
print(f"[app] Database path: {DB_PATH}")
nicegui_app.mount("/api", platform_api_app)
BackupService.start()


def render_page(content: ui.column, page: dict) -> None:
    content.clear()
    handler = page.get("handler")
    # FUN-020: guard against None handler rather than letting AttributeError surface
    if handler is None:
        with content, ui.card().classes(
            "w-full border border-amber-200 bg-amber-50 p-4 rounded-xl"
        ):
            ui.label(f"Page '{page.get('name', '?')}' has no handler registered.").classes(
                "text-amber-700 font-semibold"
            )
        return
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
        with content, ui.card().classes(
            "w-full border border-red-200 bg-red-50 p-4 rounded-xl"
        ):
            ui.label(f"Error loading '{page['name']}'").classes(
                "text-red-700 font-semibold"
            )
            ui.label(str(exc)).classes("text-sm text-red-600 mt-1")
            ui.code(traceback.format_exc()).classes(
                "text-xs mt-2 overflow-auto max-h-48"
            )


def _shutdown() -> None:
    BackupService.stop()
    ui.notify("Shutting down…", position="top")
    nicegui_app.shutdown()


def _is_authenticated() -> bool:
    """Return True when the current browser session has a valid login."""
    return bool(nicegui_app.storage.user.get("authenticated", False))


@ui.page("/login")
def login_page() -> None:
    """Password-protected login page.

    SEC-001: Passwords are verified with PBKDF2-HMAC-SHA-256.
             ACCESSMAN_PASSWORD_HASH must be produced by:
               python -c "import hashlib,os,base64; salt=os.urandom(16);
                 dk=hashlib.pbkdf2_hmac('sha256',b'yourpassword',salt,260000);
                 print(base64.b64encode(salt+dk).decode())"
             For backwards-compat a 64-hex-char legacy SHA-256 hash is still
             accepted but triggers a deprecation warning.

    FUN-019: When ACCESSMAN_PASSWORD_HASH is unset the app no longer silently
             auto-approves access.  Instead it blocks login and shows a clear
             setup warning.  Set ACCESSMAN_UNPROTECTED=1 only for offline dev.

    FUN-022: Empty-password submissions are rejected before any hashing.
    """
    import hashlib
    import base64
    import hmac

    ui.page_title("Login — " + APP_TITLE)
    _expected_hash = os.getenv("ACCESSMAN_PASSWORD_HASH", "").strip()
    _unprotected   = os.getenv("ACCESSMAN_UNPROTECTED", "0").lower() in {"1", "true", "yes"}

    if not _expected_hash:
        if _unprotected:
            log.warning(
                "ACCESSMAN_UNPROTECTED=1 — authentication is disabled. "
                "Do NOT use this in production."
            )
            nicegui_app.storage.user["authenticated"] = True
            ui.navigate.to("/")
        else:
            # FUN-019: no silent auto-approve
            with ui.column().classes(
                "items-center justify-center w-full min-h-screen bg-slate-100"
            ):
                with ui.card().classes("p-8 gap-4 w-96 shadow-xl rounded-2xl border-red-300"):
                    ui.label("⚠ No Password Configured").classes(
                        "text-lg font-bold text-red-700 text-center"
                    )
                    ui.label(
                        "Set ACCESSMAN_PASSWORD_HASH in your .secrets file to enable login. "
                        "For offline dev only, set ACCESSMAN_UNPROTECTED=1."
                    ).classes("text-sm text-slate-600 text-center")
        return

    if _is_authenticated():
        ui.navigate.to("/")
        return

    def _verify(candidate: str) -> bool:
        """SEC-001: verify against PBKDF2 hash, with legacy SHA-256 fallback."""
        if len(_expected_hash) == 64 and all(c in "0123456789abcdef" for c in _expected_hash):
            # Legacy plain SHA-256 (64 hex chars) — accept but warn
            log.warning(
                "ACCESSMAN_PASSWORD_HASH is a plain SHA-256 hex digest. "
                "Regenerate it with PBKDF2 — see the login_page docstring."
            )
            entered = hashlib.sha256(candidate.encode()).hexdigest()
            return hmac.compare_digest(entered, _expected_hash)
        # PBKDF2-HMAC-SHA-256: hash = base64(salt[16] || dk[32])
        try:
            raw  = base64.b64decode(_expected_hash)
            salt = raw[:16]
            stored_dk = raw[16:]
            dk = hashlib.pbkdf2_hmac("sha256", candidate.encode(), salt, 260000)
            return hmac.compare_digest(dk, stored_dk)
        except Exception:
            return False

    with ui.column().classes("items-center justify-center w-full min-h-screen bg-slate-100"):
        with ui.card().classes("p-8 gap-4 w-80 shadow-xl rounded-2xl"):
            ui.label(APP_TITLE).classes("text-base font-bold text-slate-700 text-center")
            ui.label("Sign in to continue").classes("text-sm text-slate-400 text-center mb-2")
            pw = ui.input("Password", password=True, password_toggle_button=True).classes(
                "w-full"
            )
            err = ui.label("").classes("text-red-500 text-xs")

            def _login() -> None:
                # FUN-022: reject empty passwords before hashing
                if not pw.value:
                    err.set_text("Password cannot be empty")
                    return
                if _verify(pw.value):
                    nicegui_app.storage.user["authenticated"] = True
                    ui.navigate.to("/")
                else:
                    err.set_text("Incorrect password")
                    pw.set_value("")

            ui.button("Sign In", on_click=_login).classes("w-full bg-blue-600 text-white")
            pw.on("keydown.enter", lambda: _login())


@ui.page("/")
def index() -> None:  # noqa: C901 - top-level page builder; complexity comes from sidebar layout.
    if not _is_authenticated():
        ui.navigate.to("/login")
        return
    ui.page_title(APP_TITLE)

    def _global_shortcuts(e) -> None:
        if getattr(e, "action", "") != "keydown":
            return
        if str(getattr(e, "key", "")).lower() == "escape":
            ui.run_javascript(
                """
                document.querySelectorAll('.q-dialog').forEach((el) => {
                  const vm = el.__vueParentComponent && el.__vueParentComponent.proxy;
                  if (vm && typeof vm.hide === 'function') {
                    vm.hide();
                  }
                });
                """
            )

    ui.keyboard(on_key=_global_shortcuts)

    groups: dict[str, list[dict]] = {}
    for page in PAGES:
        groups.setdefault(page["group"], []).append(page)

    stored_page_name = str(nicegui_app.storage.user.get("active_page_name", ""))

    with ui.column().classes("w-full h-[100dvh] overflow-hidden min-h-0"):
        with ui.row().classes(
            "w-full bg-white border-b border-slate-200 px-6 py-3 items-center justify-end shadow-sm"
        ):
            def _logout() -> None:
                # FUN-021: clear entire user session, not just the auth flag
                nicegui_app.storage.user.clear()
                ui.navigate.to("/login")

            ui.button(icon="person_off", on_click=_logout).props(
                "flat round dense"
            ).classes(
                "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            ).tooltip("Log out")
            ui.button(icon="logout", on_click=_shutdown).props(
                "flat round dense"
            ).classes(
                "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            ).tooltip("Shutdown app")

        with ui.row().classes("flex-1 w-full no-wrap overflow-hidden min-h-0"):
            with ui.column().classes(
                "h-full bg-slate-900 text-white p-4 gap-1 shadow-xl overflow-y-auto min-h-0"
            ).style("min-width:240px; max-width:240px").props("id=sidebar-nav"):

                ui.label(APP_TITLE).classes("text-lg font-bold leading-tight mb-1")
                ui.label("Accessibility Workflow Platform").classes(
                    "text-xs text-slate-400 mb-4"
                )

                active_page: list[dict | None] = [None]
                btn_refs: dict[str, ui.button] = {}

                def _activate_page(p: dict) -> None:
                    for b in btn_refs.values():
                        b.classes(
                            remove="bg-slate-700 text-white",
                            add="text-slate-300",
                        )
                    btn_refs[p["name"]].classes(
                        remove="text-slate-300",
                        add="bg-slate-700 text-white",
                    )
                    active_page[0] = p
                    nicegui_app.storage.user["active_page_name"] = p["name"]
                    render_page(content_area, p)

                for group_name, group_pages in groups.items():
                    ui.label(group_name).classes(
                        "text-xs text-slate-400 uppercase tracking-widest mt-3 mb-1 px-2"
                    )
                    for page in group_pages:
                        def _make_click(p: dict) -> Callable:
                            def _click() -> None:
                                _activate_page(p)
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

                # ── Failed pages — show as disabled with error indicator ────
                if FAILED_PAGES:
                    ui.separator().classes("border-red-800 mt-2 mb-1")
                    ui.label("Failed to load").classes(
                        "text-xs text-red-400 uppercase tracking-wider px-2 mb-1"
                    )
                    for fp in FAILED_PAGES:
                        (
                            ui.button(fp["name"], icon="error_outline")
                            .props("flat align=left disable")
                            .classes(
                                "w-full justify-start text-left text-red-400 "
                                "opacity-60 cursor-not-allowed rounded-lg px-2 py-1"
                            )
                            .tooltip(f"Import failed: {fp['module']}.{fp['function']}")
                        )

            with ui.column().classes(
                "flex-1 h-full overflow-auto bg-slate-50 min-h-0"
            ):
                content_area = ui.column().classes("w-full p-6 pb-20 gap-4 min-h-0")

                if PAGES:
                    initial = next(
                        (p for p in PAGES if p["name"] == stored_page_name),
                        PAGES[0],
                    )
                    _activate_page(initial)

                ui.run_javascript(
                    """
                    const sidebar = document.getElementById('sidebar-nav');
                    if (sidebar) {
                        const key = 'apm.sidebar.scrollTop';
                        const saved = window.localStorage.getItem(key);
                        if (saved !== null) {
                            sidebar.scrollTop = Number(saved) || 0;
                        }
                        sidebar.addEventListener('scroll', () => {
                            window.localStorage.setItem(key, String(sidebar.scrollTop));
                        }, { passive: true });
                    }
                    """
                )

        with ui.row().classes(
            "w-full shrink-0 items-center justify-between gap-4 border-t border-slate-200 "
            "bg-white px-6 py-3 text-xs text-slate-500"
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

def load_secrets():
    """Load KEY=VALUE secrets from .secrets into os.environ.

    SEC-002: uses partition('=') so values containing '=' (e.g. base64 Fernet
    keys) are preserved intact.  Blank lines and comment lines are skipped.
    FUN-013: strips whitespace from both key and value independently.
    """
    secrets_path = '.secrets'
    if not os.path.exists(secrets_path):
        raise FileNotFoundError(f"Secrets file '{secrets_path}' not found.")

    with open(secrets_path, 'r') as file:
        for line in file:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            key, sep, value = stripped.partition('=')
            if not sep:
                continue  # malformed line — no '=' found; skip silently
            os.environ[key.strip()] = value.strip()

def main() -> None:
    """Console-script entry point for ``uv run AccessMan``."""
    favicon_path = Path(__file__).parent.parent / "resources/icons/favicon.svg"
    load_secrets()
    storage_secret = os.getenv('STORAGE_SECRET')
    
    if not storage_secret:
        raise ValueError("Storage secret is missing or empty.")
        
    ui.run(
        title=APP_TITLE,
        reload=False,
        favicon=str(favicon_path),
        show=False,
        port=8765,
        storage_secret=storage_secret,
    )

if __name__ in {"__main__", "__mp_main__"}:
    main()