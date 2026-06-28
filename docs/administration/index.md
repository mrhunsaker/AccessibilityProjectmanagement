# Administration

Configuration, security, and maintenance tasks for running an APM instance:
managing categories and lookups, securing the deployment, backing up data,
and the REST API used for programmatic access.

| Page | Description |
|------|-------------|
| [REST API](api.md) | Endpoints for jobs, students, inventory, and QA |
| [Backup & Restore](backup-restore.md) | Automatic and manual backups, retention, and restore procedure |
| [Configurable Categories](categories.md) | Editing dropdown options stored in `material_category` |
| [Database Migrations](migration.md) | How the incremental migration system works and how to add migrations |
| [Performance](performance.md) | SQLite tuning, full-text search rebuilds, and pagination |
| [Printers & Embossers](printers-embossers.md) | Managing 3-D printer and embosser devices |
| [Security Guide](security.md) | Authentication, 2FA, secret management, and RBAC in depth |
| [Multi-Tenancy](tenants.md) | The in-memory organization/membership model used by the Operations Dashboard |
| [Users & Roles](users-roles.md) | Defining accounts in `.secrets` and switching users |

New to administering APM? Start with [Security Guide](security.md) and
[Users & Roles](users-roles.md) before touching categories or backups.
