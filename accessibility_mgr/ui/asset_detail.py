from nicegui import ui

from services.assets_service import AssetService


def asset_detail_page() -> None:
    ui.label("Asset Detail Manager").classes("text-2xl font-bold")

    assets = AssetService.list_assets()
    asset_map = {f"{asset.id}: {asset.name}": asset.id for asset in assets}

    selected_asset = ui.select(asset_map, label="Select Asset")
    detail_container = ui.column().classes("w-full")

    def render_details():
        detail_container.clear()

        if not selected_asset.value:
            return

        asset = next(
            (a for a in assets if a.id == selected_asset.value),
            None,
        )

        if not asset:
            return

        history = AssetService.get_workflow_history(asset.id)

        with detail_container:
            with ui.card().classes("w-full"):
                ui.label(asset.name).classes("text-xl font-bold")
                ui.label(f"Type: {asset.asset_type}")
                ui.label(f"Path: {asset.path}")

                if asset.parent_id:
                    ui.label(f"Derived From: {asset.parent_id}")

            with ui.card().classes("w-full"):
                ui.label("Workflow Summary").classes("text-lg font-semibold")

                if not history:
                    ui.label("No workflow history")

                for event in history:
                    with ui.column().classes("border-b pb-2"):
                        ui.label(event.stage).classes("font-semibold")
                        ui.label(event.operator)
                        ui.label(event.notes).classes("text-sm")

    selected_asset.on_value_change(lambda _: render_details())
