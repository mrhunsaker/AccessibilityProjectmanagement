"""Shared UI helpers — progress bars, badges, confirmation dialogs, notifications."""

from __future__ import annotations

from datetime import date
from typing import Any, Callable

from nicegui import ui

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
    """Confirm dialog.
        ui.label(title).classes("text-lg font-semibold text-slate-800")
        ui.label(message).classes("text-slate-600")
        with ui.row().classes("gap-3 justify-end w-full mt-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat").classes(
                "text-slate-600"
            )

            def _do() -> None:
                """ do.
                
                Returns
                -------
                Any
                    Function result.
                
                """
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
    """Notify error.
    
    Parameters
    ----------
    msg : Any
        msg parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
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
    """File use badge.
    
    Parameters
    ----------
    file_use : Any
        file_use parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    cls = FILE_USE_COLORS.get(file_use, "bg-slate-100 text-slate-600")
    ui.badge(file_use).classes(f"text-xs px-2 py-0.5 rounded {cls}")


def card_row(*labels: tuple[str, Any], cls: str = "") -> None:
    """Card row.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with ui.row().classes(f"gap-6 flex-wrap {cls}"):
        for key, val in labels:
            with ui.column().classes("gap-0"):
                ui.label(key).classes(
                    "text-xs text-slate-400 uppercase tracking-wider"
                )
                ui.label(str(val) if val is not None else "—").classes(
                    "text-sm text-slate-700 font-medium"
                )
