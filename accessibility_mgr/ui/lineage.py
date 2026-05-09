"""Lineage and provenance visualization UI."""

from nicegui import ui


LINEAGE_EXAMPLES = [
    "Source PDF → OCR TXT → Corrected TXT → BRF → Embossed Braille",
    "CAD Source → STL → Slicer Project → G-code → Printed Object",
    "DOCX → EPUB → DAISY → Accessible Delivery Package",
]


def lineage_page() -> None:
    """Render lineage visualization planning interface."""

    ui.label("Lineage & Provenance Visualization").classes(
        "text-2xl font-bold"
    )

    ui.markdown(
        """
        This subsystem is intended to visualize derivative relationships,
        workflow provenance, and preservation-oriented lineage tracking.
        """
    )

    with ui.card().classes("w-full"):
        ui.label("Example Derivative Chains").classes(
            "text-lg font-semibold"
        )

        for chain in LINEAGE_EXAMPLES:
            ui.label(chain).classes("font-mono text-sm")

    with ui.card().classes("w-full"):
        ui.label("Planned Visualization Features").classes(
            "text-lg font-semibold"
        )

        ui.markdown(
            """
            - Asset graph visualization
            - Parent/child relationship trees
            - Provenance timelines
            - Revision comparison
            - Workflow replay
            - Preservation exports
            - Delivery history tracking
            """
        )
