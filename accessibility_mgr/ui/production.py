from nicegui import ui

from services.production_service import ProductionService


def production_page() -> None:
    ui.label("Physical Production Tracking").classes("text-2xl font-bold")

    name = ui.input("Device Name")
    device_type = ui.input("Device Type")
    material = ui.input("Material / Media")

    container = ui.column().classes("w-full")

    def refresh():
        container.clear()

        with container:
            for device in ProductionService.list_devices():
                with ui.card().classes("w-full"):
                    ui.label(device.name).classes("text-lg font-semibold")
                    ui.label(device.device_type)
                    ui.label(f"Material: {device.material}")
                    ui.label(f"Status: {device.status}")
                    ui.label(
                        f"Last Maintenance: {device.last_maintenance}"
                    )
                    ui.label(
                        f"Next Maintenance: {device.next_maintenance}"
                    )

    def create_device():
        ProductionService.register_device(
            name.value,
            device_type.value,
            material.value,
        )

        ui.notify("Production device registered")
        refresh()

    ui.button("Register Device", on_click=create_device)

    refresh()
