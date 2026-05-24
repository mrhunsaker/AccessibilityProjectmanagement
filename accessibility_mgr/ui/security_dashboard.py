"""RBAC security and authorization dashboard."""

from __future__ import annotations

from nicegui import ui

from ..services.rbac import RBACService, UserIdentity
from .components import section_header


_rbac = RBACService()

_admin = UserIdentity(
    username="platform-admin",
    roles=[_rbac.get_role("administrator")],
)

_operator = UserIdentity(
    username="workflow-operator",
    roles=[_rbac.get_role("operator")],
)



def security_dashboard_page(content_area: ui.element) -> None:
    """Render RBAC security dashboard."""

    content_area.clear()

    with content_area:
        section_header(
            "Security & Authorization",
            "Role-based access control and governance authorization",
        )

        with ui.grid(columns=2).classes("w-full gap-4 mb-6"):
            with ui.card().classes(
                "p-5 rounded-xl border border-slate-200"
            ):
                ui.label("Registered Roles").classes(
                    "text-sm text-slate-500"
                )
                ui.label(str(len(_rbac.list_roles()))).classes(
                    "text-3xl font-bold text-slate-700"
                )

            with ui.card().classes(
                "p-5 rounded-xl border border-slate-200"
            ):
                ui.label("Authorization Checks").classes(
                    "text-sm text-slate-500"
                )
                ui.label("Active").classes(
                    "text-3xl font-bold text-green-600"
                )

        with ui.card().classes(
            "w-full p-5 rounded-xl border border-slate-200 mb-6"
        ):
            ui.label("Role Definitions").classes(
                "text-base font-semibold text-slate-700 mb-3"
            )

            for role in _rbac.list_roles():
                with ui.column().classes(
                    "border-b border-slate-100 py-3 gap-1"
                ):
                    ui.label(role["name"]).classes(
                        "text-sm font-semibold text-slate-700"
                    )

                    for permission in role["permissions"]:
                        ui.badge(permission).classes(
                            "bg-slate-100 text-slate-700 mr-1"
                        )

        with ui.card().classes(
            "w-full p-5 rounded-xl border border-slate-200"
        ):
            ui.label("Authorization Simulation").classes(
                "text-base font-semibold text-slate-700 mb-3"
            )

            checks = [
                (
                    _admin.username,
                    "governance.manage",
                    _rbac.authorize(_admin, "governance.manage"),
                ),
                (
                    _operator.username,
                    "rbac.manage",
                    _rbac.authorize(_operator, "rbac.manage"),
                ),
            ]

            for username, permission, result in checks:
                with ui.row().classes(
                    "items-center justify-between border-b border-slate-100 py-2"
                ):
                    ui.label(f"{username} → {permission}").classes(
                        "text-sm text-slate-700"
                    )

                    ui.badge(
                        "authorized" if result else "denied"
                    ).classes(
                        "bg-green-100 text-green-700"
                        if result
                        else "bg-red-100 text-red-700"
                    )
