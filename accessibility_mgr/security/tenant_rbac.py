"""Tenant-aware RBAC enforcement infrastructure."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TenantPermission:
    organization_id: str
    role: str
    resource: str
    action: str


class TenantRBACService:
    """Tenant-scoped RBAC authorization engine."""

    def __init__(self) -> None:
        self._permissions: list[TenantPermission] = []

    def register_permission(
        self,
        *,
        organization_id: str,
        role: str,
        resource: str,
        action: str,
    ) -> None:
        self._permissions.append(
            TenantPermission(
                organization_id=organization_id,
                role=role,
                resource=resource,
                action=action,
            )
        )

    def authorize(
        self,
        *,
        organization_id: str,
        role: str,
        resource: str,
        action: str,
    ) -> bool:
        return any(
            permission.organization_id == organization_id
            and permission.role == role
            and permission.resource == resource
            and permission.action == action
            for permission in self._permissions
        )

    def seed_defaults(self) -> None:
        defaults = [
            ("system", "admin", "workflow", "manage"),
            ("system", "reviewer", "artifact", "view"),
            ("system", "operator", "workflow", "execute"),
        ]

        for organization_id, role, resource, action in defaults:
            self.register_permission(
                organization_id=organization_id,
                role=role,
                resource=resource,
                action=action,
            )


__all__ = [
    "TenantPermission",
    "TenantRBACService",
]
