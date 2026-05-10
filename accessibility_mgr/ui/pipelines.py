from nicegui import ui

from services.pipeline_service import PipelineService


def pipelines_page() -> None:
    ui.label("Workflow Pipelines").classes("text-2xl font-bold")

    for pipeline in PipelineService.list_pipelines():
        with ui.card().classes("w-full"):
            ui.label(pipeline.name).classes("text-lg font-semibold")

            for step in pipeline.steps:
                with ui.row().classes("w-full justify-between"):
                    with ui.column():
                        ui.label(step.name)
                        ui.label(step.tool).classes(
                            "text-xs text-slate-500"
                        )

                    ui.code(step.command)

            ui.button("Execute Pipeline")
