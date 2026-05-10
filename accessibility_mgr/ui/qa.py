from nicegui import ui

from services.qa_service import QAService


def qa_page() -> None:
    ui.label("Accessibility QA Tooling").classes("text-2xl font-bold")

    ui.markdown(
        """
        Accessibility validation and QA orchestration for EPUB,
        Braille, DAISY, and tactile production workflows.
        """
    )

    for tool in QAService.list_tools():
        with ui.card().classes("w-full"):
            ui.label(tool.name).classes("text-lg font-semibold")
            ui.badge(tool.domain)
            ui.label(tool.description)
            ui.code(tool.command_hint)

            with ui.row():
                ui.button("Run Validation")
                ui.button("View QA History")
