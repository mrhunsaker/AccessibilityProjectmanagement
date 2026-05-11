from nicegui import ui
from ..db.database import SessionLocal
from ..models.inventory import Category

def categories_page():
    db = SessionLocal()

    ui.label('Categories').classes('text-2xl')

    name = ui.input('Category Name')
    description = ui.input('Description')

    def create_category():
        category = Category(
            name=name.value,
            description=description.value,
        )

        db.add(category)
        db.commit()

        ui.notify('Category added')

    ui.button('Save Category', on_click=create_category)

    with ui.column():
        for category in db.query(Category).all():
            with ui.card().classes('w-96'):
                ui.label(category.name).classes('text-lg')
                ui.label(category.description or '')

    db.close()
