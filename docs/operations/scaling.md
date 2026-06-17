# Scaling

APM is intentionally designed for **single-user local operation**.  This page
documents the practical limits and paths to scale when needed.

---

## 📐 Practical Limits

| Entity | Tested comfortably | Notes |
|---|---|---|
| Jobs per type | ~5,000 | Pagination (50/page) keeps UI fast |
| File objects | ~10,000 | Paths stored, not content |
| Metadata rows | ~50,000 | FTS index keeps search fast |
| Event log rows | ~100,000 | No pagination on event log card |
| Backup files | 10 | Older ones pruned automatically |

---

## 🗄️ Large Event Logs

If the event log card on a job detail page is slow, you can archive old events:

```sql
-- Move events older than 1 year to an archive table
CREATE TABLE metadata_event_archive AS
  SELECT * FROM metadata_event WHERE event_datetime < date('now', '-1 year');
DELETE FROM metadata_event WHERE event_datetime < date('now', '-1 year');
```

APM's UI only reads from `metadata_event`, so archived rows will no longer
appear in the job detail view.

---

## 🌐 Multi-User / Network Access

APM's SQLite database supports **one writer at a time**.  For teams of 2-3
users sharing a database over a LAN:

1. Place `accessibility_manager.db` on a shared network drive.
2. Set `ACCESSMAN_DB_PATH` to the network path on each machine.
3. WAL mode (already enabled) allows concurrent readers with one writer.

For more than ~5 concurrent users, consider migrating the data layer to
PostgreSQL.  The `db/queries.py` module uses standard SQL that is
PostgreSQL-compatible with minor adjustments (`?` → `%s`, `datetime('now')` →
`NOW()`).

---

## 🔄 Workflow Queue

The in-memory `WorkflowQueueService` is replaced by `PersistentWorkflowQueue`
(SQLite-backed) when `services/singletons.py` is updated to use it.  This
allows workflow jobs to survive application restarts.
