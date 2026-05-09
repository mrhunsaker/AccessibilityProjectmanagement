"""File ingestion workflow UI."""

from pathlib import Path

from nicegui import events, ui

from services.file_ingestion_service import FileIngestionService

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
    "GCODE",
    "Images",
]


def ingestion_page() -> None:
    """Render file ingestion interface."""

    ui.label("File Ingestion Pipelines").classes("text-2xl font-bold")

    ui.markdown(
        """
        Upload accessibility-production assets and automatically generate
        preservation metadata.
        """
    )

    selected_type = ui.select(SUPPORTED_TYPES, value="PDF")

    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)

    def handle_upload(event: events.UploadEventArguments):
        file_path = uploads_dir / event.name

        file_path.write_bytes(event.content.read())

        FileIngestionService.ingest_file(
            str(file_path),
            selected_type.value,
        )

        ui.notify(f"Ingested file: {event.name}")

    ui.upload(on_upload=handle_upload).props(
        "accept=.pdf,.docx,.epub,.brf,.pef,.txt,.html,.stl,.3mf"
    )

    with ui.card().classes("w-full"):
        ui.label("Supported Asset Types").classes("text-lg font-semibold")

        with ui.row().classes("gap-2 flex-wrap"):
            for item in SUPPORTED_TYPES:
                ui.badge(item).classes("bg-green-100 text-green-800")
