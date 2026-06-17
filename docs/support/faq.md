# Frequently Asked Questions

---

## Installation & Setup

**Q: The app says "No Password Configured" and won't let me log in.**

A: You need to set `ACCESSMAN_PASSWORD_HASH` in `.secrets`.  Generate one with:
```bash
python -c "
import hashlib, os, base64
salt = os.urandom(16)
dk = hashlib.pbkdf2_hmac('sha256', b'your_password', salt, 260000)
print('ACCESSMAN_PASSWORD_HASH=' + base64.b64encode(salt + dk).decode())
" >> .secrets
```
For local development only, add `ACCESSMAN_UNPROTECTED=1` instead.

---

**Q: Where is the database stored?**

A: By default at `~/.local/share/accessibility_mgr/accessibility_manager.db`.
Override with `ACCESSMAN_DB_PATH` in `.secrets`.

---

**Q: Can I run APM on Windows?**

A: Yes.  Use `run.bat` as a launcher, or `uv run AccessMan` in a terminal.
All paths use `pathlib.Path` for cross-platform compatibility.

---

## Jobs & Workflows

**Q: How do I link a job to a student?**

A: When creating or editing any job, use the **Student** dropdown.  Students
must be created first under **Students** in the sidebar.

**Q: Can I delete a job type step I don't use?**

A: Go to **Admin → Workflow Steps** and click **Deactivate**.  The step
disappears from the UI but existing completion data is preserved.

**Q: Why does "Mark Done" on the Delivered step open a dialog?**

A: The delivery dialog captures delivery method, recipient, and date, which
are stored for reporting and audit purposes.

---

## Files & Ingestion

**Q: My file fails to ingest with "source outside permitted staging directory".**

A: Files must be staged in `job_files/` (the `FILES_DIR`) before ingestion.
Use the **Upload File** panel on the File Ingestion page to stage them, or
copy the file there manually.

**Q: Where do ingested files go?**

A: To `~/.local/share/accessibility_mgr/artifacts/<Project Title>/`.  The
filename is built from student initials, school name, grade, and subject.

---

## Search & Reports

**Q: Search isn't finding jobs I know exist.**

A: If the FTS5 index is out of sync (e.g. after a bulk import), rebuild it:
```sql
INSERT INTO braille_job_fts(braille_job_fts) VALUES('rebuild');
```

**Q: Can I search by checksum?**

A: Yes.  Paste the full 64-character hex SHA-256 into the search box.  It is
matched exactly against `file_object.checksum_sha256`.

---

## Backup & Restore

**Q: How often are backups taken?**

A: Automatically every 7 days, starting 30 seconds after launch.  Manual
backups can be triggered any time from **Admin → Backups → Run Backup Now**.

**Q: How do I restore a backup?**

A: Use `BackupService.restore_backup("/path/to/backup.db")` from a Python
shell.  A safety snapshot of the current database is created first.
