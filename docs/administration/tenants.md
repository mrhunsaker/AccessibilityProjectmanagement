# Multi-Tenancy

APM's `MultiTenantService` provides an **in-memory** organization and
membership abstraction.  It is surfaced in the **Operations Dashboard** as a
demonstration layer.  The primary application database is single-tenant
(one SQLite file per installation).

---

## 🏢 Organization Model

Each organization has:

| Field | Description |
|-------|-------------|
| `organization_id` | Auto-assigned identifier (e.g. `org-1`) |
| `name` | Display name |
| `created_at` | UTC timestamp |

---

## 👤 Membership

Users are linked to organizations via `TenantMembership`:

| Field | Description |
|-------|-------------|
| `username` | User identifier |
| `organization_id` | Target organization |
| `role` | Assigned role within that organization |

---

## 🔐 RBAC Integration

Permission checks go through `TenantRBACService` which holds a list of
`TenantPermission` records keyed by `(organization_id, role, resource, action)`.

Seed defaults (applied automatically):

| Organization | Role | Resource | Action |
|---|---|---|---|
| system | admin | workflow | manage |
| system | reviewer | artifact | view |
| system | operator | workflow | execute |

---

## 💡 Current Limitations

The current implementation is **in-memory only** — organizations and
memberships do not persist between application restarts.  This is by design
for a single-workstation studio tool.

Future releases may add database-backed tenant isolation for shared network
deployments.  Track progress on the [Roadmap](../project/roadmap.md).
