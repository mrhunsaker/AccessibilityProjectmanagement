"""
Shared delivery dialog helper (FIX-016).

Call open_delivery_dialog() from any job detail view when the operator
clicks "Mark Done" on the Delivered step. Captures delivery method,
recipient, and date before writing the step completion and delivery fields.
"""

from __future__ import annotations

from datetime import date

from nicegui import ui

from ..db import queries as Q
from .components import notify_success, validate_iso_date

_DELIVERY_METHODS = [
    "Physical Copy",
    "Email",
    "Learning Management System",
    "USB / Media",
    "Pickup",
    "Other",
]


def open_delivery_dialog(
    job_type: str,
    job_id: int,
    on_done,
    agent: str = "user",
) -> None:
    """Open a delivery confirmation dialog for any job type.

    On confirmation, calls Q.record_delivery() which:
      - Sets delivered = 1 and all four delivery_ columns
      - Logs a DELIVERY event to metadata_event
      - Logs a FIELD_UPDATE event (via update_*_job)

    Parameters
    ----------
    job_type : str
        One of 'braille', 'lp_ebraille', 'tactile', 'print'.
    job_id : int
        Primary key of the job being delivered.
    on_done : callable
        Zero-argument callback invoked after the DB writes complete.
    agent : str
        Name/identifier of the actor confirming delivery.
    """
    today = date.today().isoformat()

    # Guard: if the job is already delivered, show a read-only summary.
    _fetch_fn = {
        "braille":     Q.get_braille_job,
        "lp_ebraille": Q.get_lp_job,
        "tactile":     Q.get_tactile_job,
        "print":       Q.get_print_job,
    }.get(job_type)
    if _fetch_fn:
        _row = _fetch_fn(job_id)
        if _row and int(_row.get("delivered") or 0) == 1:
            with ui.dialog() as _info_dlg, ui.card().classes("p-6 gap-4 w-[440px] max-w-full"):
                ui.label("Already Delivered").classes("text-xl font-bold text-slate-800")
                ui.label(
                    f"This job was delivered on {_row.get('delivery_date') or '—'} "
                    f"via {_row.get('delivery_method') or '—'} "
                    f"to {_row.get('delivery_recipient') or '—'}."
                ).classes("text-sm text-slate-600")
                if _row.get("delivery_notes"):
                    ui.label(_row["delivery_notes"]).classes("text-xs text-slate-400")
                ui.button("Close", on_click=_info_dlg.close).classes("bg-slate-200")
            _info_dlg.open()
            return

    with ui.dialog() as dlg, ui.card().classes("p-6 gap-4 w-[480px] max-w-full"):
        ui.label("Confirm Delivery").classes("text-xl font-bold text-slate-800")
        ui.label(
            "Recording delivery will mark this job as delivered and log a permanent audit event."
        ).classes("text-sm text-slate-500 mb-2")

        method_sel = ui.select(
            _DELIVERY_METHODS,
            label="Delivery Method*",
            value="Physical Copy",
        ).classes("w-full")

        recipient_inp = ui.input(
            "Delivered To* (student name, teacher, or org)",
            placeholder="e.g. Smith, John — Legacy Jr. High",
        ).classes("w-full")

        date_inp = ui.input(
            "Delivery Date*",
            value=today,
            placeholder="YYYY-MM-DD",
        ).classes("w-full")

        notes_inp = ui.textarea(
            "Delivery Notes (optional)",
            placeholder="e.g. Delivered to homeroom teacher. Confirmation email sent.",
        ).classes("w-full").props("rows=2")

        with ui.row().classes("justify-end gap-3 mt-2"):
            ui.button("Cancel", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _confirm() -> None:
                if not recipient_inp.value.strip():
                    ui.notify("Recipient is required", type="negative", position="top-right")
                    return
                if not date_inp.value.strip():
                    ui.notify("Delivery date is required", type="negative", position="top-right")
                    return
                if not validate_iso_date(date_inp.value.strip(), "Delivery Date"):
                    return

                Q.record_delivery(
                    job_type=job_type,
                    job_id=job_id,
                    delivery_method=method_sel.value,
                    delivery_recipient=recipient_inp.value.strip(),
                    delivery_date=date_inp.value.strip(),
                    delivery_notes=notes_inp.value.strip(),
                    agent=agent,
                )
                notify_success(
                    f"Delivered to {recipient_inp.value.strip()} "
                    f"via {method_sel.value} on {date_inp.value.strip()}"
                )
                dlg.close()
                on_done()

            ui.button("Confirm Delivery", on_click=_confirm).classes(
                "bg-green-600 text-white"
            )

    dlg.open()
