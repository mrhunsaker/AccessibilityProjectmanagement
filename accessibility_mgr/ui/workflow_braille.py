"""Workflow braille module.

"""
from nicegui import ui

from ..services.assets_service import AssetService
from ..services.workflow_engine import WorkflowEngine

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
    """Workflow braille page.
    
    Returns
    -------
    Any
        Function result.
    
    """
    ui.label("Braille Workflow Execution").classes("text-2xl font-bold")

    assets = AssetService.list_assets()

    asset_map = {f"{asset.id}: {asset.name}": asset.id for asset in assets}

    selected_asset = ui.select(asset_map, label="Select Asset")
    operator = ui.input("Operator")
    notes = ui.textarea("Workflow Notes")

    history_container = ui.column().classes("w-full")

    def refresh_history():
        """Refresh history.
        
        Returns
        -------
        Any
            Function result.
        
        """
        history_container.clear()

        if not selected_asset.value:
            return

        history = AssetService.get_workflow_history(selected_asset.value)

        with history_container:
            with ui.card().classes("w-full"):
                ui.label("Workflow History").classes(
                    "text-lg font-semibold"
                )

                if not history:
                    ui.label("No workflow events recorded")

                for event in history:
                    with ui.row().classes(
                        "w-full justify-between border-b pb-2"
                    ):
                        with ui.column():
                            ui.label(event.stage).classes("font-semibold")
                            ui.label(event.operator).classes(
                                "text-sm text-slate-500"
                            )
                            ui.label(event.notes).classes(
                                "text-xs text-slate-400"
                            )

    selected_asset.on_value_change(lambda _: refresh_history())

    with ui.row().classes("gap-2 flex-wrap"):
        for stage in BRAILLE_STAGES:

            def execute(current_stage=stage):
                """Execute.
                
                Parameters
                ----------
                current_stage : Any
                    current_stage parameter.
                
                Returns
                -------
                Any
                    Function result.
                
                """
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
                refresh_history()

            ui.button(
                stage.replace("_", " ").title(),
                on_click=execute,
            )

    refresh_history()
