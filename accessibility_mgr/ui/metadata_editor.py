"""Metadata editor planning UI.

Provides structured metadata editing concepts for accessibility-production
assets and workflow entities.
"""

from nicegui import ui


METADATA_GROUPS = {
    "Descriptive": [
        "Title",
        "Subject",
        "Language",
        "Keywords",
        "Accessibility Need",
    ],
    "Technical": [
        "OCR Engine",
        "Translation Engine",
        "Embosser Settings",
        "Printer Profile",
        "File Format",
    ],
    "Workflow": [
        "Revision Notes",
        "Operator",
        "QA Status",
        "Workflow Stage",
        "Approval Status",
    ],
    "Preservation": [
        "Checksum",
        "Provenance",
        "Derivative Chain",
        "Generation Timestamp",
        "Source Relationship",
    ],
}


def metadata_editor_page() -> None:
    """Render metadata editor planning page."""

    ui.label("Metadata Editor").classes("text-2xl font-bold")

    ui.markdown(
        """
        The metadata editor is intended to provide flexible METS-inspired
        metadata management for accessibility-production workflows.
        """
    )

    for category, fields in METADATA_GROUPS.items():
        with ui.card().classes("w-full"):
            ui.label(category).classes("text-lg font-semibold")

            with ui.grid(columns=2).classes("w-full gap-2"):
                for field in fields:
                    ui.input(label=field).props("outlined")

    with ui.card().classes("w-full"):
        ui.label("Planned Metadata Features").classes(
            "text-lg font-semibold"
        )

        ui.markdown(
            """
            - Dynamic metadata templates
            - JSON metadata editing
            - Metadata inheritance
            - Validation schemas
            - Metadata provenance tracking
            - Preservation export support
            - Bulk metadata editing
            """
        )
