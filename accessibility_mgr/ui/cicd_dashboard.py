"""CI/CD accessibility validation dashboard."""

from __future__ import annotations

from nicegui import ui

from ..integrations.cicd_hooks import CICDValidationHookService
from .components import section_header


_service = CICDValidationHookService()



def cicd_dashboard(content_area: ui.element) -> None:
    """Render CI/CD accessibility validation dashboard."""

    content_area.clear()

    with content_area:
        section_header(
            "CI/CD Accessibility Validation",
            "Continuous accessibility validation orchestration",
        )

        with ui.card().classes(
            "w-full p-5 rounded-xl border border-slate-200 mb-6"
        ):
            ui.label("Validation Capabilities").classes(
                "text-base font-semibold text-slate-700 mb-3"
            )

            capabilities = [
                "DAISY Ace pipeline validation",
                "EPUBCheck CI validation",
                "Automated workflow execution",
                "Pipeline execution history",
                "Continuous accessibility governance",
            ]

            for capability in capabilities:
                with ui.row().classes("items-center gap-2 py-1"):
                    ui.icon("check_circle").classes(
                        "text-green-600"
                    )
                    ui.label(capability).classes(
                        "text-sm text-slate-700"
                    )

        with ui.card().classes(
            "w-full p-5 rounded-xl border border-slate-200"
        ):
            ui.label("Recent Validation Activity").classes(
                "text-base font-semibold text-slate-700 mb-3"
            )

            history = _service.list_history()

            if not history:
                ui.label(
                    "No CI/CD validation activity recorded"
                ).classes("text-sm text-slate-500")

            for item in history:
                with ui.row().classes(
                    "w-full justify-between border-b border-slate-100 py-2"
                ):
                    ui.label(item["pipeline_id"]).classes(
                        "text-sm font-medium text-slate-700"
                    )

                    ui.badge(item["status"]).classes(
                        "bg-blue-100 text-blue-700"
                    )
