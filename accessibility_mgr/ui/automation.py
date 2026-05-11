from nicegui import ui

from ..services.automation_service import AutomationService


def automation_page() -> None:
    ui.label("Workflow Automation Integrations").classes(
        "text-2xl font-bold"
    )

    integrations = AutomationService.list_integrations()

    for tool, description in integrations.items():
        with ui.card().classes("w-full"):
            ui.label(tool).classes("text-lg font-semibold")
            ui.label(description)

            ui.button(f"Run {tool} Workflow")
