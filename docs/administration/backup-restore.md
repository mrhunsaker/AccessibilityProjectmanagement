# Backup & Restore

APM automatically backs up the SQLite database on a **7-day schedule** and
retains the 10 most-recent copies.  Manual backups can be triggered at any
time from the Admin panel.

---

## 📁 Backup Location

Backups are written to the `backups/` subdirectory of the database data
directory (resolved at startup via `ACCESSMAN_DB_PATH` or the XDG default):

```
~/.local/share/accessibility_mgr/backups/
    accessibility_manager_20260601_093012.db
    accessibility_manager_20260608_093015.db
    ...
```

---

## ⚙️ How Backups Work

APM uses `sqlite3.Connection.backup()`, which performs a WAL checkpoint
before copying.  The result is always a **clean, consistent snapshot** even
while the application is running.

* **Retention**: 10 most-recent files are kept; older ones are pruned automatically.
* **Space check**: APM verifies there is at least 2× the database size of free
  space before starting.  The backup is aborted with a clear error if space is
  insufficient.
* **Audit trail**: Every backup attempt (success or failure) is recorded in the
  `backup_log` table and visible on the Admin → Backups tab.

---

## 🖱️ Trigger a Manual Backup

1. Navigate to **Admin → Backups**.
2. Click **Run Backup Now**.
3. The status label updates when the backup finishes (or reports an error).

---

## 🔁 Restore from a Backup

> **Warning**: Restoring overwrites the live database.  APM automatically
> creates a *pre-restore safety snapshot* before overwriting.

### Via Admin Panel (recommended)

Backup restore is currently a CLI operation (see below).  The Admin panel
displays the backup directory path so you can locate the file.

### Via Python / CLI

```python
from accessibility_mgr.services.backup_service import BackupService

BackupService.restore_backup("/path/to/accessibility_manager_20260601_093012.db")
```

The call:
1. Validates the backup file is a readable SQLite database (`PRAGMA integrity_check`).
2. Saves a `pre_restore_<timestamp>.db` safety snapshot.
3. Copies the backup over the live database path.
4. Verifies the restored file passes an integrity check.

Raises `RuntimeError` on any failure so the caller can surface the problem to
the user.

---

## 🗑️ Retention & Pruning

Only the 10 most-recent `accessibility_manager_*.db` files are kept.
Older files are deleted automatically after each successful backup.  To keep
more copies, edit `BackupService._KEEP_BACKUPS` in
`accessibility_mgr/services/backup_service.py`.

---

## 📋 Backup Log

The `backup_log` table stores every backup event:

| Column | Description |
|--------|-------------|
| `backup_path` | Absolute path to the backup file |
| `size_bytes` | File size at the time of backup |
| `trigger` | `scheduled` or `manual` |
| `status` | `ok` or error description |
| `created_at` | UTC timestamp |

Query directly:
```sql
SELECT * FROM backup_log ORDER BY created_at DESC LIMIT 20;
```
