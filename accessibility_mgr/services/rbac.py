"""Role-based access control infrastructure."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Role:
    name: str
    permissions: set[str] = field(default_factory=set)


@dataclass(slots=True)
class UserIdentity:
    username: str
    roles: list[Role]


class RBACService:
    """Central authorization service."""

    def __init__(self) -> None:
        self._roles: dict[str, Role] = {}
        self._seed_roles()

    def _seed_roles(self) -> None:
        self.register_role(
            Role(
                name="administrator",
                permissions={
                    "qa.execute",
                    "qa.review",
                    "governance.manage",
                    "workflow.manage",
                    "analytics.view",
                    "rbac.manage",
                },
            )
        )

        self.register_role(
            Role(
                name="operator",
                permissions={
                    "qa.execute",
                    "workflow.manage",
                    "analytics.view",
                },
            )
        )

        self.register_role(
            Role(
                name="reviewer",
                permissions={
                    "qa.review",
                    "analytics.view",
                },
            )
        )

    def register_role(self, role: Role) -> None:
        self._roles[role.name] = role

    def get_role(self, role_name: str) -> Role | None:
        return self._roles.get(role_name)

    def authorize(
        self,
        user: UserIdentity,
        permission: str,
    ) -> bool:
        for role in user.roles:
            if permission in role.permissions:
                return True

        return False

    def list_roles(self) -> list[dict]:
        return [
            {
                "name": role.name,
                "permissions": sorted(role.permissions),
            }
            for role in self._roles.values()
        ]


__all__ = [
    "RBACService",
    "Role",
    "UserIdentity",
]
