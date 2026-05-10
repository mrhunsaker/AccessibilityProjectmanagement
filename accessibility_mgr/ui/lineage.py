from nicegui import ui

from services.assets_service import AssetService


def lineage_page() -> None:
    ui.label("Asset Lineage Viewer").classes("text-2xl font-bold")

    ui.markdown(
        """
        Visualize derivative relationships and workflow provenance chains.
        """
    )

    assets = AssetService.list_assets()

    with ui.card().classes("w-full"):
        ui.label("Provenance Graph").classes("text-lg font-semibold")

        mermaid = "graph TD\n"

        for asset in assets:
            mermaid += f"A{asset.id}[{asset.name}]\n"

            if asset.parent_id:
                mermaid += (
                    f"A{asset.parent_id} --> A{asset.id}\n"
                )

        ui.mermaid(mermaid)

    with ui.column().classes("w-full gap-4"):
        for asset in assets:
            with ui.card().classes("w-full"):
                ui.label(asset.name).classes("text-lg font-semibold")
                ui.label(asset.asset_type).classes("text-sm text-slate-500")
                ui.label(asset.path).classes("text-xs text-slate-400")

                if asset.parent_id:
                    ui.label(f"Derived From Asset ID: {asset.parent_id}")
                else:
                    ui.label("Root Asset")
