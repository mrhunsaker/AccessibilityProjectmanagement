"""Multi-tenant organization infrastructure."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone


@dataclass(slots=True)
class Organization:
    organization_id: str
    name: str
    created_at: str


@dataclass(slots=True)
class TenantMembership:
    username: str
    organization_id: str
    role: str


class MultiTenantService:
    """Organization and tenant isolation service."""

    def __init__(self) -> None:
        self._organizations: list[Organization] = []
        self._memberships: list[TenantMembership] = []

    def create_organization(self, name: str) -> Organization:
        organization = Organization(
            organization_id=f"org-{len(self._organizations) + 1}",
            name=name,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        self._organizations.append(organization)
        return organization

    def add_member(
        self,
        *,
        username: str,
        organization_id: str,
        role: str,
    ) -> TenantMembership:
        membership = TenantMembership(
            username=username,
            organization_id=organization_id,
            role=role,
        )

        self._memberships.append(membership)
        return membership

    def list_organizations(self) -> list[dict]:
        return [asdict(org) for org in self._organizations]

    def list_memberships(self) -> list[dict]:
        return [asdict(member) for member in self._memberships]


__all__ = [
    "Organization",
    "TenantMembership",
    "MultiTenantService",
]
