from nicegui import ui

from services.assets_service import AssetService
from services.workflow_engine import WorkflowEngine

BRAILLE_STAGES = [
    "digitization",
    "ocr",
    "cleanup",
    "translation",
    "proofreading",
    "embossing",
    "delivery",
]


def workflow_braille_page() -> None:
    ui.label("Braille Workflow Execution").classes("text-2xl font-bold")

    assets = AssetService.list_assets()

    asset_map = {f"{asset.id}: {asset.name}": asset.id for asset in assets}

    selected_asset = ui.select(asset_map, label="Select Asset")
    operator = ui.input("Operator")
    notes = ui.textarea("Workflow Notes")

    with ui.row().classes("gap-2 flex-wrap"):
        for stage in BRAILLE_STAGES:

            def execute(current_stage=stage):
                if not selected_asset.value:
                    ui.notify("Select an asset first")
                    return

                WorkflowEngine.execute_stage(
                    asset_id=selected_asset.value,
                    workflow_type="braille",
                    stage=current_stage,
                    operator=operator.value,
                    notes=notes.value,
                )

                ui.notify(f"Executed stage: {current_stage}")

            ui.button(
                stage.replace("_", " ").title(),
                on_click=execute,
            )
