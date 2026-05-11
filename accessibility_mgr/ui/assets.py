"""Asset and metadata registry UI with CRUD functionality."""

from __future__ import annotations

from nicegui import ui

from ..services.assets_service import AssetService

ASSET_TYPES = [
    "BRF",
    "PEF",
    "EPUB",
    "DAISY",
    "STL",
    "3MF",
    "GCODE",
    "PDF",
    "DOCX",
]


def assets_page() -> None:
    """Render metadata and asset management UI."""

    ui.label("Asset Registry & Metadata Workflows").classes(
        "text-2xl font-bold"
    )

    ui.markdown(
        """
        Track digital and physical accessibility-production assets along with
        metadata, workflow events, and derivative lineage.
        """
    )

    with ui.row().classes("w-full gap-4 items-start"):
        with ui.card().classes("w-full max-w-xl"):
            ui.label("Create Project").classes("text-lg font-semibold")

            project_title = ui.input("Project Title")
            project_description = ui.textarea("Description")

            def create_project():
                AssetService.create_project(
                    project_title.value,
                    project_description.value,
                )
                ui.notify("Project created")
                refresh_projects()

            ui.button("Create Project", on_click=create_project)

        with ui.card().classes("w-full max-w-xl"):
            ui.label("Register Asset").classes("text-lg font-semibold")

            asset_name = ui.input("Asset Name")
            asset_type = ui.select(ASSET_TYPES, value="BRF")
            asset_path = ui.input("File Path")

            def create_asset():
                AssetService.create_asset(
                    asset_name.value,
                    asset_type.value,
                    asset_path.value,
                )
                ui.notify("Asset registered")
                refresh_assets()

            ui.button("Register Asset", on_click=create_asset)

    projects_container = ui.column().classes("w-full")
    assets_container = ui.column().classes("w-full")

    def refresh_projects():
        projects_container.clear()

        with projects_container:
            with ui.card().classes("w-full"):
                ui.label("Projects").classes("text-lg font-semibold")

                for project in AssetService.list_projects():
                    with ui.row().classes(
                        "w-full justify-between border-b pb-2"
                    ):
                        with ui.column():
                            ui.label(project.title).classes("font-semibold")
                            ui.label(project.description).classes(
                                "text-sm text-slate-500"
                            )

    def refresh_assets():
        assets_container.clear()

        with assets_container:
            with ui.card().classes("w-full"):
                ui.label("Tracked Assets").classes(
                    "text-lg font-semibold"
                )

                for asset in AssetService.list_assets():
                    with ui.card().classes("w-full"):
                        ui.label(asset.name).classes("font-semibold")
                        ui.label(asset.asset_type).classes(
                            "text-sm text-blue-600"
                        )
                        ui.label(asset.path).classes(
                            "text-xs text-slate-500"
                        )

                        metadata_key = ui.input("Metadata Key")
                        metadata_value = ui.input("Metadata Value")

                        def add_metadata(asset_id=asset.id):
                            AssetService.add_metadata(
                                asset_id,
                                metadata_key.value,
                                metadata_value.value,
                            )
                            ui.notify("Metadata added")

                        ui.button(
                            "Add Metadata",
                            on_click=add_metadata,
                        )

    refresh_projects()
    refresh_assets()
