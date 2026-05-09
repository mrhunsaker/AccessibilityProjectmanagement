from nicegui import ui

from services.assets_service import AssetService
from services.workflow_engine import WorkflowEngine

PRINT_STAGES = [
    "cad_ingestion",
    "mesh_validation",
    "slicing",
    "printing",
    "qa",
    "delivery",
]


def workflow_printing_page() -> None:
    ui.label("3D Printing Workflow Execution").classes(
        "text-2xl font-bold"
    )

    assets = AssetService.list_assets()

    asset_map = {f"{asset.id}: {asset.name}": asset.id for asset in assets}

    selected_asset = ui.select(asset_map, label="Select Asset")
    operator = ui.input("Operator")
    notes = ui.textarea("Workflow Notes")

    with ui.row().classes("gap-2 flex-wrap"):
        for stage in PRINT_STAGES:

            def execute(current_stage=stage):
                if not selected_asset.value:
                    ui.notify("Select an asset first")
                    return

                WorkflowEngine.execute_stage(
                    asset_id=selected_asset.value,
                    workflow_type="3d_print",
                    stage=current_stage,
                    operator=operator.value,
                    notes=notes.value,
                )

                ui.notify(f"Executed stage: {current_stage}")

            ui.button(
                stage.replace("_", " ").title(),
                on_click=execute,
            )
