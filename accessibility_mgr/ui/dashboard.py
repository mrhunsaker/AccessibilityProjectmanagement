from nicegui import ui

def dashboard_page():
    ui.label('Dashboard').classes('text-2xl')

    with ui.row().classes('w-full'):
        for title in [
            'Low Stock Alerts',
            'Recent Transactions',
            'Active Projects',
            'Inventory Summary',
        ]:
            with ui.card().classes('w-64 h-40'):
                ui.label(title).classes('text-lg')
