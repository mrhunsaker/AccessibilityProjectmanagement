from nicegui import ui
from db.database import SessionLocal
from models.inventory import InventoryItem
from services.inventory_service import InventoryService

def inventory_page():
    db = SessionLocal()

    ui.label('Inventory').classes('text-2xl')

    with ui.row().classes('w-full'):
        items = db.query(InventoryItem).all()

        for item in items:
            with ui.card().classes('w-72'):
                ui.label(item.name).classes('text-lg')
                ui.label(f'Quantity: {item.current_quantity} {item.unit}')

                quantity_input = ui.number(label='Quantity')

                with ui.row():
                    ui.button(
                        'Add',
                        on_click=lambda i=item, q=quantity_input:
                            InventoryService.add_inventory(i.id, q.value or 0)
                    )

                    ui.button(
                        'Use',
                        on_click=lambda i=item, q=quantity_input:
                            InventoryService.consume_inventory(i.id, q.value or 0)
                    )

    db.close()
