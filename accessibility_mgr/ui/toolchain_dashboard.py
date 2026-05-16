"""Accessibility toolchain execution dashboard."""

from __future__ import annotations

from nicegui import ui

from ..services.toolchain import AccessibilityToolchainService
from .components import section_header


_toolchain = AccessibilityToolchainService()



def toolchain_dashboard_page(content_area: ui.element) -> None:
    """Render accessibility toolchain dashboard."""

    content_area.clear()

    ace_result = _toolchain.run_mock_ace("sample.epub")
    epubcheck_result = _toolchain.run_mock_epubcheck("sample.epub")

    with content_area:
        section_header(
            "Accessibility Toolchain",
            "DAISY Ace, EPUBCheck, and pipeline execution monitoring",
        )

        for label, result in [
            ("DAISY Ace", ace_result),
            ("EPUBCheck", epubcheck_result),
        ]:
            execution = result["execution"]

            with ui.card().classes(
                "w-full p-5 rounded-xl border border-slate-200 mb-5"
            ):
                ui.label(label).classes(
                    "text-lg font-semibold text-slate-700 mb-3"
                )

                with ui.row().classes(
                    "items-center justify-between mb-2"
                ):
                    ui.label("Execution Status").classes(
                        "text-sm text-slate-500"
                    )
                    ui.badge(execution["status"]).classes(
                        "bg-green-100 text-green-700"
                    )

                with ui.row().classes(
                    "items-center justify-between mb-2"
                ):
                    ui.label("Exit Code").classes(
                        "text-sm text-slate-500"
                    )
                    ui.label(str(execution["exit_code"])).classes(
                        "text-sm font-mono text-slate-700"
                    )

                with ui.column().classes("gap-1 mt-3"):
                    ui.label("Artifacts").classes(
                        "text-sm font-semibold text-slate-600"
                    )

                    for artifact in execution["artifacts"]:
                        ui.label(artifact).classes(
                            "text-xs font-mono text-slate-500"
                        )

                with ui.expansion("Execution Output").classes(
                    "mt-4"
                ):
                    ui.label(execution["stdout"] or "No stdout") \
                        .classes("text-xs font-mono text-slate-600")

                    ui.label(execution["stderr"] or "No stderr") \
                        .classes("text-xs font-mono text-red-500")
