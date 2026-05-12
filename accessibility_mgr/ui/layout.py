"""Layout module.

"""
from nicegui import ui
from .inventory import inventory_page
from .dashboard import dashboard_page
from .categories import categories_page

def build_layout():
    """Build layout.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with ui.row().classes('w-full no-wrap'):
        with ui.column().classes('bg-gray-200 h-screen p-4 w-64'):
            ui.label('Accessibility PM').classes('text-xl')

            ui.button('Dashboard', on_click=dashboard_page).classes('w-full')
            ui.button('Inventory', on_click=inventory_page).classes('w-full')
            ui.button('Categories', on_click=categories_page).classes('w-full')
            ui.button('Add Category').classes('w-full')
            ui.button('Add Item').classes('w-full')
            ui.button('Transactions').classes('w-full')

        with ui.column().classes('p-4 w-full') as content:
            dashboard_page()
