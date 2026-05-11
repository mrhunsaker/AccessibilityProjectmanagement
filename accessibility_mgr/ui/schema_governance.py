from nicegui import ui

from ..services.schema_governance_service import (
    SchemaGovernanceService,
)


def schema_governance_page() -> None:
    ui.label("Schema Governance").classes("text-2xl font-bold")

    vocabularies = SchemaGovernanceService.get_vocabularies()

    for field, values in vocabularies.items():
        with ui.card().classes("w-full"):
            ui.label(field).classes("text-lg font-semibold")

            with ui.row().classes("gap-2 flex-wrap"):
                for value in values:
                    ui.badge(value)
