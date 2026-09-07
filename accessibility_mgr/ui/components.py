"""Shared UI helpers — progress bars, badges, confirmation dialogs, notifications."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from nicegui import events, ui

PRIORITY_COLORS: dict[str, str] = {
    "low":    "bg-slate-400 text-white",
    "normal": "bg-blue-500 text-white",
    "high":   "bg-amber-500 text-white",
    "urgent": "bg-red-600 text-white",
}

OUTCOME_COLORS: dict[str, str] = {
    "SUCCESS": "text-green-600",
    "FAILURE": "text-red-600",
    "WARNING": "text-amber-600",
}

FILE_USE_COLORS: dict[str, str] = {
    "ORIGINAL":     "bg-indigo-100 text-indigo-800",
    "DERIVATIVE":   "bg-purple-100 text-purple-800",
    "INTERMEDIATE": "bg-amber-100 text-amber-800",
    "SOURCE":       "bg-green-100 text-green-800",
    "REFERENCE":    "bg-slate-100 text-slate-800",
}


def progress_bar(done: int, total: int) -> None:
    """Render a compact labelled progress bar."""
    pct = int(done / total * 100) if total else 0
    with ui.column().classes("gap-0 w-full"):
        with ui.row().classes("w-full items-center gap-2"):
            with ui.element("div").classes("flex-1 bg-slate-200 rounded-full h-2"):
                ui.element("div").classes(
                    f"h-2 rounded-full {'bg-green-500' if pct == 100 else 'bg-blue-500'}"
                ).style(f"width:{pct}%")
            ui.label(f"{done}/{total}").classes("text-xs text-slate-500 whitespace-nowrap")


def priority_badge(priority: str | None) -> None:
    normalized = (priority or "normal").lower()
    cls = PRIORITY_COLORS.get(normalized, "bg-slate-400 text-white")
    ui.badge(normalized.upper()).classes(f"text-xs px-2 py-0.5 rounded {cls}")


def status_chip(label: str, done: bool) -> None:
    if done:
        ui.badge("✓ " + label).classes(
            "bg-green-100 text-green-800 text-xs rounded px-2 py-0.5"
        )
    else:
        ui.badge(label).classes("bg-slate-100 text-slate-500 text-xs rounded px-2 py-0.5")


def confirm_dialog(
    message: str,
    on_confirm: Callable[[], None],
    title: str = "Confirm",
) -> None:
    """Show a modal confirmation dialog; call on_confirm only if the user confirms."""
    with ui.dialog() as dialog, ui.card().classes("p-6 gap-4 min-w-80"):
        ui.label(title).classes("text-lg font-semibold text-slate-800")
        ui.label(message).classes("text-slate-600")
        with ui.row().classes("gap-3 justify-end w-full mt-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat").classes(
                "text-slate-600"
            )

            def _do() -> None:
                dialog.close()
                on_confirm()

            ui.button("Confirm", on_click=_do).classes("bg-red-500 text-white")
    dialog.open()


def section_header(title: str, subtitle: str = "") -> None:
    with ui.column().classes("gap-1 mb-2"):
        ui.label(title).classes("text-2xl font-bold text-slate-800 tracking-tight")
        if subtitle:
            ui.label(subtitle).classes("text-slate-500 text-sm")


def notify_success(msg: str) -> None:
    ui.notify(msg, type="positive", position="top-right")


def notify_error(msg: str) -> None:
    """Show a red error notification toast."""
    ui.notify(msg, type="negative", position="top-right")


def validate_iso_date(value: str, label: str) -> bool:
    """Validate YYYY-MM-DD date strings and notify on failure."""
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        notify_error(f"{label} must be in YYYY-MM-DD format")
        return False


def file_use_badge(file_use: str) -> None:
    """Render a colored badge indicating the file's role (e.g. ORIGINAL, DERIVATIVE)."""
    cls = FILE_USE_COLORS.get(file_use, "bg-slate-100 text-slate-600")
    ui.badge(file_use).classes(f"text-xs px-2 py-0.5 rounded {cls}")


def card_row(*labels: tuple[str, Any], cls: str = "") -> None:
    """Render a row of label-value pairs inside a card layout."""
    with ui.row().classes(f"gap-6 flex-wrap {cls}"):
        for key, val in labels:
            with ui.column().classes("gap-0"):
                ui.label(key).classes(
                    "text-xs text-slate-400 uppercase tracking-wider"
                )
                ui.label(str(val) if val is not None else "—").classes(
                    "text-sm text-slate-700 font-medium"
                )


def file_picker(
    holder: dict[str, Any],
    *,
    accept: str = "",
    hint: str = "Click to select a file from this machine",
    label: str = "Attach File",
) -> None:
    """Render a file picker that stages the selected file into FILES_DIR.

    Clicking the control opens the native browser file dialog. The chosen file
    is written into the app staging directory (``Q.FILES_DIR``) so it satisfies
    ``ingest_file``'s SEC-004 staging requirement, and the staged absolute
    source path is recorded on ``holder`` under ``source_path`` (and
    ``file_name`` for the original basename). Callers read
    ``holder.get("source_path")`` from their save handler and pass it as the
    ingest/copy source. Selecting a file replaces any previously staged one.

    SEC-005: the incoming ``event.name`` originates in the browser and may carry
    path separators or traversal sequences, so only a sanitised basename is used
    to build the staged path.
    """
    from ..db import queries as Q

    holder["source_path"] = None
    holder["file_name"] = None

    def _cleanup_previous() -> None:
        prev = holder.get("source_path")
        if prev:
            try:
                Path(prev).unlink(missing_ok=True)
            except OSError:
                pass

    def _on_upload(event: events.UploadEventArguments) -> None:
        raw_name = Path(event.name).name
        safe_name = "".join(c for c in raw_name if c.isalnum() or c in "._- ").strip()
        if not safe_name:
            notify_error(f"Upload rejected: filename '{event.name}' is not safe.")
            return
        Q.FILES_DIR.mkdir(parents=True, exist_ok=True)
        stage = Q.FILES_DIR / safe_name
        if stage.exists():
            stage = Q.FILES_DIR / (
                f"{Path(safe_name).stem}_{uuid4().hex[:8]}{Path(safe_name).suffix}"
            )
        _cleanup_previous()
        stage.write_bytes(event.content.read())
        holder["source_path"] = str(stage)
        holder["file_name"] = safe_name
        status_label.set_text(f"Attached: {safe_name}")
        notify_success(f"Selected: {safe_name}")

    with ui.column().classes("gap-1 w-full"):
        picker_row = ui.row().classes("w-full items-center gap-2")

        def _open_picker() -> None:
            # Click the hidden upload's file-select input to open the native dialog.
            ui.run_javascript(
                "const el = document.querySelector('.upload-file-picker .q-uploader__input');"
                " if (el) el.click();"
            )

        with picker_row:
            ui.button(label, icon="folder_open", on_click=_open_picker).classes(
                "text-indigo-600 border border-indigo-200 rounded-lg shrink-0"
            )
            with ui.upload(on_upload=_on_upload, auto_upload=True).classes(
                "hidden upload-file-picker"
            ).props(f"accept={accept}" if accept else ""):
                pass

    status_label = ui.label(hint).classes("text-xs text-slate-400")
