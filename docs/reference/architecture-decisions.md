# Architecture Decisions

---

## ADR-001: SQLite as the primary database

**Decision**: Use SQLite with WAL mode rather than a client-server database.

**Rationale**:
- Single-workstation target; no network connectivity required.
- Zero-configuration deployment.
- `sqlite3.Connection.backup()` provides safe hot backups.
- FTS5 extension gives full-text search without a separate search index.

**Consequences**:
- One writer at a time.  Acceptable for a single-user application.
- Network/multi-user deployments require care (see [Scaling](../operations/scaling.md)).

---

## ADR-002: All SQL in `db/queries.py`

**Decision**: No SQL strings outside `db/queries.py`.

**Rationale**:
- Single point of audit for injection risks.
- Allow-list column validation in `_build_update_sql()` prevents dynamic column injection.
- Easier to profile and optimise.

---

## ADR-003: NiceGUI for the UI

**Decision**: Use NiceGUI (Vue.js + Python) rather than a separate frontend framework.

**Rationale**:
- Single-language stack; no JavaScript build pipeline.
- Local desktop-style UX without Electron.
- FastAPI is already embedded; REST API can be mounted without a separate process.

---

## ADR-004: In-memory services with singleton pattern

**Decision**: Analytics, provenance, and queue services are in-memory singletons
shared between the UI and REST API via `services/singletons.py`.

**Rationale**:
- Avoids a message bus for a single-process app.
- Jobs enqueued via the REST API are immediately visible in the UI queue.

**Consequences**:
- Service state does not survive application restart.
- Future persistence requires replacing the singleton implementation, not the callers.

---

## ADR-005: PBKDF2-HMAC-SHA-256 for passwords

**Decision**: Use PBKDF2 with 260,000 iterations and a random 16-byte salt.

**Rationale**:
- `hashlib.pbkdf2_hmac` is available in the Python standard library (no dependency).
- 260,000 iterations aligns with OWASP 2024 recommendation.
- Backwards-compatible SHA-256 hex fallback with deprecation warning.

---

## ADR-006: Soft-delete for categories and students

**Decision**: `delete_material_category()` and `delete_student()` set `active = 0`
rather than removing rows.

**Rationale**:
- Historical records (jobs, metadata) remain valid.
- Deactivated values disappear from dropdowns but data integrity is preserved.
