from nicegui import ui

from ..services.auth_service import AuthService


def authentication_page() -> None:
    ui.label("Authentication and RBAC").classes("text-2xl font-bold")

    current = ui.label(
        f"Current User: {AuthService.current_user.username}"
    )

    usernames = [user.username for user in AuthService.list_users()]

    selector = ui.select(usernames, value=usernames[0])

    def switch():
        AuthService.switch_user(selector.value)
        current.set_text(
            f"Current User: {AuthService.current_user.username}"
        )
        ui.notify("Switched active user")

    ui.button("Switch User", on_click=switch)

    with ui.card().classes("w-full"):
        ui.label("Registered Roles").classes("text-lg font-semibold")

        for user in AuthService.list_users():
            with ui.row().classes("justify-between w-full"):
                ui.label(user.username)
                ui.badge(user.role)
