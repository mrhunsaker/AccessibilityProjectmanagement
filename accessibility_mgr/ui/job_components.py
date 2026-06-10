"""Shared job detail components for metadata and event-log rendering."""

from __future__ import annotations

from html import escape
from typing import Callable

from nicegui import ui

from ..db import queries as Q
from .components import OUTCOME_COLORS, notify_success
from .metadata_options import (
    get_dublin_core_examples,
    get_dublin_core_keys,
    get_non_dc_allowed_keys,
    get_option_groups,
)


def export_job_summary(
        *,
        job_type: str,
        job: dict,
        step_order: list[str],
        step_labels: dict[str, str],
) -> None:
        """Generate and download a print-ready HTML summary for a job."""
        job_id = int(job["id"])
        metadata = Q.list_job_metadata(job_type, job_id)
        events = Q.list_events_for_job(job_type, job_id)
        files = Q.list_files_for_job(job_type, job_id)

        step_rows: list[str] = []
        for step in step_order:
                completed = bool(job.get(step, 0))
                completed_at = ""
                for event in events:
                        if event.get("event_type") == "STEP_COMPLETE" and event.get("step_key") == step:
                                completed_at = str(event.get("event_datetime") or "")[:19]
                                break
                step_rows.append(
                        "<tr>"
                        f"<td>{escape(step_labels.get(step, step))}</td>"
                        f"<td>{'Yes' if completed else 'No'}</td>"
                        f"<td>{escape(completed_at or '-')}</td>"
                        "</tr>"
                )

        metadata_rows = "".join(
                f"<tr><td>{escape(str(k))}</td><td>{escape(str(v))}</td></tr>"
                for k, v in sorted(metadata.items())
        ) or "<tr><td colspan='2'>No metadata</td></tr>"

        files_rows = "".join(
                "<tr>"
                f"<td>{escape(str(f.get('original_name') or '-'))}</td>"
                f"<td>{escape(str(f.get('file_use') or '-'))}</td>"
                f"<td>{escape(str(f.get('checksum_sha256') or '-'))}</td>"
                "</tr>"
                for f in files
        ) or "<tr><td colspan='3'>No linked files</td></tr>"

        event_rows = "".join(
                "<tr>"
                f"<td>{escape(str(e.get('event_datetime') or '')[:19])}</td>"
                f"<td>{escape(str(e.get('event_type') or '-'))}</td>"
                f"<td>{escape(str(e.get('detail') or '-'))}</td>"
                "</tr>"
                for e in events[:200]
        ) or "<tr><td colspan='3'>No events</td></tr>"

        core_rows = []
        for key in [
                "title",
                "object_name",
                "requester",
                "request_date",
                "due_date",
                "priority",
                "delivery_date",
                "delivery_method",
                "delivery_recipient",
                "delivery_notes",
                "created_at",
                "printed_at",
        ]:
                if key in job and job.get(key) not in (None, ""):
                        core_rows.append(
                                f"<tr><td>{escape(key)}</td><td>{escape(str(job.get(key)))}</td></tr>"
                        )
        core_table = "".join(core_rows) or "<tr><td colspan='2'>No core fields</td></tr>"

        html = f"""
<!doctype html>
<html lang='en'>
<head>
    <meta charset='utf-8'>
    <title>Job Summary {job_type} #{job_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 24px; color: #1f2937; }}
        h1, h2 {{ margin: 0 0 12px 0; }}
        h2 {{ margin-top: 20px; font-size: 18px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
        th, td {{ border: 1px solid #d1d5db; padding: 6px 8px; text-align: left; font-size: 12px; }}
        th {{ background: #f8fafc; }}
        .meta {{ color: #6b7280; font-size: 12px; }}
    </style>
</head>
<body>
    <h1>Job Summary</h1>
    <div class='meta'>Type: {escape(job_type)} | ID: {job_id}</div>

    <h2>Core Metadata</h2>
    <table>
        <tr><th>Field</th><th>Value</th></tr>
        {core_table}
    </table>

    <h2>Dublin Core and Additional Metadata</h2>
    <table>
        <tr><th>Key</th><th>Value</th></tr>
        {metadata_rows}
    </table>

    <h2>Workflow Steps</h2>
    <table>
        <tr><th>Step</th><th>Completed</th><th>Completion Timestamp</th></tr>
        {''.join(step_rows)}
    </table>

    <h2>Attached Files and Checksums</h2>
    <table>
        <tr><th>File</th><th>Use</th><th>SHA-256</th></tr>
        {files_rows}
    </table>

    <h2>Event Log</h2>
    <table>
        <tr><th>Timestamp</th><th>Event</th><th>Detail</th></tr>
        {event_rows}
    </table>
</body>
</html>
"""

        filename = f"{job_type}_job_{job_id}_summary.html"
        ui.download(html.encode("utf-8"), filename)


def open_metadata_dialog(job_type: str, job_id: int, on_done: Callable[[], None]) -> None:
    """Open the shared metadata editor dialog for a job."""
    existing_meta = Q.list_job_metadata(job_type, job_id)
    option_groups = get_option_groups()
    dc_keys = get_dublin_core_keys()
    dc_examples = get_dublin_core_examples()
    non_dc_keys = get_non_dc_allowed_keys()

    with ui.dialog() as dlg, ui.card().classes(
        "p-6 gap-4 w-[600px] max-w-full max-h-[90vh] overflow-y-auto"
    ):
        ui.label("Descriptive Metadata").classes("text-xl font-bold text-slate-800")
        ui.label(
            "Dublin Core plus controlled eBraille and METS/PREMIS fields."
        ).classes("text-slate-500 text-sm")

        def _show_options() -> None:
            with ui.dialog() as od, ui.card().classes(
                "p-5 gap-3 w-[720px] max-w-full max-h-[85vh] overflow-y-auto"
            ):
                ui.label("Potential Metadata Options").classes(
                    "text-lg font-bold text-slate-800"
                )
                ui.label(
                    "Use Admin Settings -> Metadata Options to add or remove allowed keys."
                ).classes("text-xs text-slate-500")
                for group, keys in option_groups.items():
                    ui.separator()
                    ui.label(group).classes(
                        "text-sm font-semibold text-slate-600 uppercase tracking-wider"
                    )
                    with ui.row().classes("gap-2 flex-wrap"):
                        for key in keys:
                            ui.badge(key).classes(
                                "bg-slate-100 text-slate-700 text-xs rounded px-2 py-1"
                            )
                with ui.row().classes("justify-end mt-2"):
                    ui.button("Close", on_click=od.close).classes("bg-slate-700 text-white")
            od.open()

        ui.button("Potential Options", on_click=_show_options).props("flat dense").classes(
            "text-indigo-600 text-sm self-start"
        )

        meta_rows: dict[str, ui.input] = {}
        with ui.grid(columns=2).classes("gap-2 w-full"):
            for key in dc_keys:
                with ui.column().classes("gap-0"):
                    inp = ui.input(key, value=existing_meta.get(key, "")).classes(
                        "w-full font-mono text-sm"
                    )
                    ui.label(dc_examples.get(key, "")).classes("text-[11px] text-slate-400")
                    meta_rows[key] = inp

        ui.separator()
        ui.label("Additional Allowed Fields").classes("text-sm font-medium text-slate-600")
        ui.label("Choose keys from the approved eBraille and METS/PREMIS list.").classes(
            "text-xs text-slate-400"
        )

        extra_rows: list[dict[str, ui.element]] = []
        extra_box = ui.column().classes("w-full gap-2")

        def _add_extra_row(initial_key: str = "", initial_val: str = "") -> None:
            with extra_box:
                with ui.row().classes("gap-2 w-full items-center") as row:
                    key_sel = ui.select(
                        non_dc_keys,
                        label="Key",
                        value=initial_key if initial_key in non_dc_keys else None,
                    ).classes("w-64")
                    val_inp = ui.input("Value", value=initial_val).classes("flex-1")
                    ref = {"row": row, "key": key_sel, "value": val_inp}
                    extra_rows.append(ref)

                    def _remove(r: dict[str, ui.element] = ref) -> None:
                        r["row"].delete()
                        if r in extra_rows:
                            extra_rows.remove(r)

                    ui.button("x", on_click=_remove).props("flat dense").classes("text-red-400")

        ui.button("+ Add Field", on_click=lambda: _add_extra_row()).props("flat dense").classes(
            "text-indigo-600 text-sm self-start"
        )

        for key, value in existing_meta.items():
            if key not in dc_keys and key in non_dc_keys:
                _add_extra_row(initial_key=key, initial_val=value)

        with ui.row().classes("justify-end gap-3 mt-4"):
            ui.button("Close", on_click=dlg.close).props("flat").classes("text-slate-500")

            def _save_all() -> None:
                saved_keys: list[str] = []
                for key, inp in meta_rows.items():
                    value = inp.value.strip()
                    if value:
                        Q.set_job_metadata(job_type, job_id, key, value)
                        saved_keys.append(key)
                    else:
                        Q.delete_job_metadata(job_type, job_id, key)

                for key in non_dc_keys:
                    Q.delete_job_metadata(job_type, job_id, key)
                for row in extra_rows:
                    key = (row["key"].value or "").strip()
                    value = (row["value"].value or "").strip()
                    if key and value and key in non_dc_keys:
                        Q.set_job_metadata(job_type, job_id, key, value)
                        saved_keys.append(key)

                Q.log_event(
                    job_type,
                    job_id,
                    "METADATA_UPDATE",
                    "SUCCESS",
                    agent="user",
                    detail=f"Metadata updated: {len(saved_keys)} field(s)",
                    extra_metadata={"updated_keys": saved_keys},
                )
                notify_success("Metadata saved")
                dlg.close()
                on_done()

            ui.button("Save All", on_click=_save_all).classes("bg-blue-600 text-white")

    dlg.open()


def render_event_log(
    *,
    job_type: str,
    job_id: int,
    step_labels: dict[str, str],
    on_done: Callable[[], None],
    title: str = "Provenance / Event Log",
    subtitle: str = "",
    step_badge_classes: str = "text-xs bg-blue-50 text-blue-700 rounded px-1",
) -> None:
    """Render the shared event log card body with add-note dialog."""
    with ui.row().classes("items-center mb-3"):
        ui.label(title).classes("font-semibold text-slate-700 flex-1")
        if subtitle:
            ui.label(subtitle).classes("text-xs text-slate-400")

        def _add_note() -> None:
            with ui.dialog() as nd, ui.card().classes("p-5 gap-3 w-96"):
                ui.label("Add Note Event").classes("font-semibold text-slate-800")
                note_txt = ui.textarea("Note").classes("w-full").props("rows=3")
                agent_txt = ui.input("Agent/Author", value="user").classes("w-full")
                with ui.row().classes("justify-end gap-2"):
                    ui.button("Cancel", on_click=nd.close).props("flat")

                    def _save_note() -> None:
                        Q.log_event(
                            job_type,
                            job_id,
                            "NOTE",
                            "SUCCESS",
                            agent=agent_txt.value.strip() or "user",
                            detail=note_txt.value.strip(),
                        )
                        nd.close()
                        on_done()

                    ui.button("Save", on_click=_save_note).classes("bg-slate-700 text-white")
            nd.open()

        ui.button("+ Add Note", on_click=_add_note).props("flat dense").classes(
            "text-slate-600 text-sm"
        )

    events = Q.list_events_for_job(job_type, job_id)
    if not events:
        ui.label("No events recorded.").classes("text-slate-400 text-sm")
        return

    for ev in events:
        outcome = ev.get("event_outcome", "SUCCESS")
        text_class = OUTCOME_COLORS.get(outcome, "text-slate-700")
        with ui.row().classes(
            "items-start gap-3 py-2 border-b border-slate-50 last:border-0"
        ):
            with ui.column().classes("gap-0 w-36 shrink-0"):
                ui.label(str(ev.get("event_datetime", ""))[:19]).classes(
                    "text-xs text-slate-400 font-mono"
                )
                ui.label(ev.get("agent", "system")).classes(
                    "text-xs text-slate-400 italic"
                )
            with ui.column().classes("flex-1 gap-0"):
                with ui.row().classes("gap-2 items-center"):
                    ui.badge(ev["event_type"]).classes(
                        "text-xs bg-slate-100 text-slate-700 rounded px-1"
                    )
                    if ev.get("step_key"):
                        ui.badge(step_labels.get(ev["step_key"], ev["step_key"])).classes(
                            step_badge_classes
                        )
                    if ev.get("file_name"):
                        ui.badge(ev["file_name"]).classes(
                            "text-xs bg-indigo-50 text-indigo-700 rounded px-1"
                        )
                if ev.get("detail"):
                    ui.label(ev["detail"]).classes(f"text-sm {text_class}")
