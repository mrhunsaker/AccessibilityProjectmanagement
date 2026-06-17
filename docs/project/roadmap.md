# Roadmap

Items are loosely ordered by priority.  Dates are aspirational.

---

## 🟢 Recently Completed

- Student records with cross-job production history (FIX-010)
- Reports page with school/grade/type/status filtering and CSV export (FIX-015)
- Delivery confirmation dialog with method, recipient, and date capture (FIX-016)
- FTS5 full-text search indexes on all job tables (IMP-023)
- Metadata backfill dry-run preview (FIX-017)
- Workflow step completion timestamps (IMP-022)

---

## 🔵 In Progress / Near-Term

- Restore from backup via Admin UI (currently CLI only)
- Keyboard shortcut reference page in the app
- Operations Dashboard resource monitor widget using `ResourceMonitorService`

---

## 🟡 Planned

### Production
- Bulk metadata editing across multiple jobs
- Job templates (pre-fill common metadata for recurring assignments)
- Student import from CSV
- Per-student production report (PDF export)

### Files & Preservation
- Checksum verification scheduler (periodic fixity checks against stored SHA-256)
- Support for ingesting files via URL (auto-download to staging)

### Integration
- DAISY Pipeline 2 server mode integration (REST API rather than CLI)
- LMS webhook notifications on job delivery

### Infrastructure
- Database-backed `ApiToken` table (currently in-memory only)
- PostgreSQL adapter for `db/queries.py` (shared network deployments)
- Docker Compose deployment stack

---

## 🔴 Under Consideration

- Mobile-responsive layout improvements
- Role-based UI restrictions (hide pages for non-admin users)
- Multi-language UI (i18n)
