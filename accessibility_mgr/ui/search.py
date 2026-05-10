from nicegui import ui

from services.search_service import SearchService


def search_page() -> None:
    ui.label("Search and Discovery").classes("text-2xl font-bold")

    query = ui.input("Search assets and metadata")
    results_container = ui.column().classes("w-full")

    def execute_search():
        results_container.clear()

        assets = SearchService.search_assets(query.value)
        metadata = SearchService.search_metadata(query.value)

        with results_container:
            with ui.card().classes("w-full"):
                ui.label("Asset Results").classes("text-lg font-semibold")

                if not assets:
                    ui.label("No asset matches found")

                for asset in assets:
                    with ui.row().classes("w-full justify-between"):
                        ui.label(asset.name)
                        ui.badge(asset.asset_type)

            with ui.card().classes("w-full"):
                ui.label("Metadata Results").classes("text-lg font-semibold")

                if not metadata:
                    ui.label("No metadata matches found")

                for record in metadata:
                    with ui.column().classes("border-b pb-2"):
                        ui.label(record.key).classes("font-semibold")
                        ui.label(record.value)

    ui.button("Search", on_click=execute_search)
