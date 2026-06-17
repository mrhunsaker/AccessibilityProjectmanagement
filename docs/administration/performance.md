# Performance

APM is a **single-user local application** backed by SQLite.  For typical
studio workloads (hundreds to low thousands of jobs) no tuning is required.
This page covers the available knobs if you encounter slowness.

---

## ⚡ SQLite Tuning

APM enables WAL mode (`PRAGMA journal_mode = WAL`) and foreign key checks on
every connection.  These are set in `db/schema.py:get_conn()`.

Additional pragmas you can add to `get_conn()` for faster reads on spinning
disks:

```python
conn.execute("PRAGMA cache_size = -64000")   # 64 MB page cache
conn.execute("PRAGMA synchronous = NORMAL")  # safe but faster than FULL
conn.execute("PRAGMA temp_store = MEMORY")
```

> **Warning**: `synchronous = OFF` risks corruption on power failure.  Avoid it.

---

## 🔍 Full-Text Search

Migration `m009` builds FTS5 virtual tables (`braille_job_fts`, etc.) and
triggers.  These keep search fast even with large job counts.

If search feels slow after bulk imports, rebuild the FTS index:

```sql
INSERT INTO braille_job_fts(braille_job_fts) VALUES('rebuild');
INSERT INTO lp_ebraille_job_fts(lp_ebraille_job_fts) VALUES('rebuild');
INSERT INTO tactile_graphics_job_fts(tactile_graphics_job_fts) VALUES('rebuild');
INSERT INTO print_job_fts(print_job_fts) VALUES('rebuild');
INSERT INTO file_object_fts(file_object_fts) VALUES('rebuild');
INSERT INTO job_metadata_fts(job_metadata_fts) VALUES('rebuild');
INSERT INTO metadata_event_fts(metadata_event_fts) VALUES('rebuild');
```

---

## 📄 Pagination

All list views default to **50 rows per page**.  If pages feel slow, ensure
that the relevant indexed columns are used.  The schema defines indexes on:

- `student_id` for all job tables
- `delivered` for all job tables
- `(job_type, job_id)` for `metadata_event`, `job_metadata`, `job_file_link`
- `(job_type, job_id, step_key)` for `job_file_link`

---

## 🗄️ Database Size

The `file_object` table stores **paths**, not file content.  Large artifact
stores do not inflate the database.  Typical databases with thousands of jobs
and metadata entries remain under 50 MB.

To check current size:

```bash
du -sh ~/.local/share/accessibility_mgr/accessibility_manager.db
```

---

## 🔄 Backup Performance

Backups use `sqlite3.Connection.backup()` which checkpoints the WAL and copies
pages incrementally.  For a 50 MB database this takes under one second.  The
scheduler runs in a daemon thread so it never blocks the UI.
