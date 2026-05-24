"""Workflow orchestration dashboard.

Provides visibility into accessibility-production workflows, lineage stages,
and processing orchestration.
"""

from nicegui import ui


WORKFLOWS = {
    "Braille Production": [
        "Digitization",
        "OCR",
        "Cleanup",
        "Formatting",
        "Translation",
        "Proofreading",
        "Embossing",
        "Packaging",
        "Delivery",
    ],
    "Accessible Documents": [
        "Source Ingestion",
        "Semantic Cleanup",
        "Accessibility Validation",
        "EPUB Generation",
        "DAISY Export",
        "PDF Remediation",
        "Packaging",
        "Delivery",
    ],
    "3-D Printing": [
        "CAD Ingestion",
        "Mesh Validation",
        "Slicer Configuration",
        "G-code Generation",
        "Print Execution",
        "QA Validation",
        "Assembly Tracking",
    ],
}


def workflows_page() -> None:
    """Render workflow orchestration dashboard."""

    ui.label("Workflow Orchestration").classes("text-2xl font-bold")

    ui.markdown(
        """
        This subsystem tracks accessibility production workflows from source
        ingestion through derivative generation and final delivery.
        """
    )

    for workflow_name, stages in WORKFLOWS.items():
        with ui.card().classes("w-full"):
            ui.label(workflow_name).classes("text-lg font-semibold")

            with ui.row().classes("w-full items-center gap-2 flex-wrap"):
                for stage in stages:
                    ui.badge(stage).classes(
                        "bg-blue-100 text-blue-800 px-3 py-2"
                    )

    with ui.card().classes("w-full"):
        ui.label("Planned Workflow Features").classes(
            "text-lg font-semibold"
        )

        ui.markdown(
            """
            - Workflow replay history
            - Assignment tracking
            - Approval checkpoints
            - Automated notifications
            - Validation pipelines
            - Derivative generation graphs
            - Preservation-oriented provenance tracking
            """
        )
