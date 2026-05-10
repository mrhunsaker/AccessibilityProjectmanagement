from nicegui import ui

from services.inventory_service import InventoryService


def inventory_page() -> None:
    ui.label("Production Inventory").classes("text-2xl font-bold")

    item_id = ui.input("Item ID")
    quantity = ui.input("Quantity")
    notes = ui.input("Notes")

    def add_stock():
        InventoryService.add_inventory(
            int(item_id.value),
            float(quantity.value),
            notes.value,
        )

        ui.notify("Inventory updated")

    ui.button("Add Inventory", on_click=add_stock)
