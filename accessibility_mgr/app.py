from nicegui import ui
from ui.layout import build_layout
from db.database import init_db

init_db()
build_layout()

ui.run(title='Accessibility Project Manager')
