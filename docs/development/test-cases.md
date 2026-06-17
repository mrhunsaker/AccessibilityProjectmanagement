# Testing

APM does not currently ship an automated test suite.  This page documents the
recommended manual test cases and guidance for adding automated tests.

---

## ✅ Core Manual Test Checklist

### Authentication
- [ ] Login with correct password succeeds
- [ ] Login with wrong password shows error and clears field
- [ ] Empty password submission is rejected before hashing
- [ ] Logout clears the session and redirects to `/login`
- [ ] Accessing `/` unauthenticated redirects to `/login`

### Job Lifecycle (repeat for Braille, LP/eBraille, Tactile, Print)
- [ ] Create a new job — appears in list
- [ ] Edit job fields — changes persist after page reload
- [ ] Mark each workflow step complete — progress bar updates
- [ ] Revert a step — step returns to incomplete
- [ ] Mark "Delivered" step — delivery dialog appears, captures method/recipient/date
- [ ] Delete job — job removed, event log entries preserved

### File Ingestion
- [ ] Ingest a file via path — file_object row created, SHA-256 computed
- [ ] Upload a file via browser — staged and ingested correctly
- [ ] Ingest with project context — file lands in `artifacts/<title>/`
- [ ] Attempt to ingest a file outside `FILES_DIR` — PermissionError raised

### Search
- [ ] Search by job title — braille/LP/tactile/print results appear
- [ ] Search by requester name — results appear
- [ ] Search by SHA-256 hash (64 hex chars) — exact file match
- [ ] Search by metadata value — metadata section populated
- [ ] Empty search — results cleared

### Inventory
- [ ] Add filament — appears with correct quantity
- [ ] Deduct filament via print job — `quantity_g` decreases
- [ ] Attempt to deduct 0 or negative grams — error raised

### Reports
- [ ] Filter by school — only matching jobs returned
- [ ] Filter by status (delivered) — only delivered jobs
- [ ] Export CSV — file downloads with correct headers
- [ ] Date range filter — respects from/to bounds

### Backups
- [ ] Manual backup — new file in `backups/`, entry in `backup_log`
- [ ] Backup log shows correct size and timestamp

---

## 🧪 Unit Testing Approach

The data layer (`db/queries.py`) is the highest-value target for unit tests
because it contains all SQL logic.  Use an in-memory SQLite database:

```python
import sqlite3
import pytest
from accessibility_mgr.db.schema import _SCHEMA_SQL, _migrate

@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript(_SCHEMA_SQL)
    _migrate(c)
    c.commit()
    yield c
    c.close()
```

Patch `get_conn()` to return this connection in tests of `queries.py` functions.
