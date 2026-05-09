"""File ingestion workflow UI."""

from nicegui import ui


SUPPORTED_TYPES = [
    "DOCX",
    "PDF",
    "EPUB",
    "BRF",
    "PEF",
    "TXT",
    "HTML",
    "STL",
    "3MF",
    "G-code",
    "Images",
]


def ingestion_page() -> None:
    """Render file ingestion planning interface."""

    ui.label("File Ingestion Pipelines").classes("text-2xl font-bold")

    ui.markdown(
        """
        File ingestion pipelines track incoming and generated accessibility
        production assets.
        """
    )

    with ui.card().classes("w-full"):
        ui.label("Supported Asset Types").classes("text-lg font-semibold")

        with ui.row().classes("gap-2 flex-wrap"):
            for item in SUPPORTED_TYPES:
                ui.badge(item).classes("bg-green-100 text-green-800")

    with ui.card().classes("w-full"):
        ui.label("Planned Pipeline Features").classes(
            "text-lg font-semibold"
        )

        ui.markdown(
            """
            - File uploads
            - Automatic metadata extraction
            - Checksum generation
            - MIME identification
            - OCR integration
            - Derivative tracking
            - Validation pipelines
            - Preservation-oriented storage
            """
        )
