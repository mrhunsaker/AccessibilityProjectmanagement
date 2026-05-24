"""Production accessibility binary integration dashboard."""

from __future__ import annotations

from nicegui import ui

from ..services.toolchain_binaries import (
    AccessibilityBinaryIntegrationService,
)
from .components import section_header


_service = AccessibilityBinaryIntegrationService()



def binary_integrations_dashboard(content_area: ui.element) -> None:
    """Render production binary integration dashboard."""

    content_area.clear()

    ace_binary = _service.discover_binary("ace")
    epubcheck_binary = _service.discover_binary("epubcheck")

    with content_area:
        section_header(
            "Production Accessibility Toolchain",
            "Production DAISY Ace and EPUBCheck binary integrations",
        )

        with ui.grid(columns=2).classes("w-full gap-4"):
            for label, binary in [
                ("DAISY Ace CLI", ace_binary),
                ("EPUBCheck", epubcheck_binary),
            ]:
                with ui.card().classes(
                    "p-5 rounded-xl border border-slate-200"
                ):
                    ui.label(label).classes(
                        "text-lg font-semibold text-slate-700 mb-2"
                    )

                    if binary:
                        ui.badge("installed").classes(
                            "bg-green-100 text-green-700 mb-2"
                        )

                        ui.label(binary).classes(
                            "text-xs font-mono text-slate-500"
                        )
                    else:
                        ui.badge("missing").classes(
                            "bg-red-100 text-red-700 mb-2"
                        )

                        ui.label(
                            "Binary not available in execution environment"
                        ).classes("text-xs text-slate-500")

        with ui.card().classes(
            "w-full mt-6 p-5 rounded-xl border border-slate-200"
        ):
            ui.label("Operational Readiness").classes(
                "text-base font-semibold text-slate-700 mb-3"
            )

            readiness = [
                "CLI binary discovery",
                "Structured subprocess execution",
                "Artifact output capture",
                "Execution timeout enforcement",
                "Operational telemetry",
            ]

            for item in readiness:
                ui.row().classes("items-center gap-2 py-1")
                ui.icon("check_circle").classes(
                    "text-green-600"
                )
                ui.label(item).classes(
                    "text-sm text-slate-700"
                )
