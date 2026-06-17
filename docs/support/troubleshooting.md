# Troubleshooting

---

## App Won't Start

### `FileNotFoundError: .secrets`

The `.secrets` file must be in the **repository root**, not inside
`accessibility_mgr/`.

```bash
ls -la .secrets   # should be present
```

### `ValueError: Storage secret is missing or empty`

Add `STORAGE_SECRET` to `.secrets`:
```bash
python -c "import secrets; print('STORAGE_SECRET=' + secrets.token_urlsafe(32))" >> .secrets
```

### `RuntimeError: Database schema is missing step date columns`

A migration did not complete.  The safest fix for a fresh install is to delete
the database file and restart:
```bash
rm ~/.local/share/accessibility_mgr/accessibility_manager.db
uv run AccessMan
```

For a database with data, run `init_db()` manually from a Python shell:
```python
from accessibility_mgr.db.schema import init_db
init_db()
```

---

## Login Issues

### Correct password rejected

Regenerate the hash — the `.secrets` file may have a stale value:
```bash
python -c "
import hashlib, os, base64
salt = os.urandom(16)
dk = hashlib.pbkdf2_hmac('sha256', b'NEW_PASSWORD', salt, 260000)
print(base64.b64encode(salt + dk).decode())
"
```
Replace the `ACCESSMAN_PASSWORD_HASH` value in `.secrets`.

---

## Pages Won't Load

### Sidebar shows "Failed to load" for a page

Check the terminal log for the import traceback.  Common causes:
- Missing dependency: run `uv sync`
- Syntax error in a custom file you edited

---

## Search Returns No Results

### FTS index out of sync after bulk import

```bash
sqlite3 ~/.local/share/accessibility_mgr/accessibility_manager.db
```
```sql
INSERT INTO braille_job_fts(braille_job_fts) VALUES('rebuild');
INSERT INTO lp_ebraille_job_fts(lp_ebraille_job_fts) VALUES('rebuild');
```

---

## File Ingestion Failures

### `PermissionError: source outside permitted staging directory`

Copy or upload the file to the staging directory first:
```bash
cp /path/to/file.brf ~/.local/share/accessibility_mgr/job_files/
```
Then ingest from `~/.local/share/accessibility_mgr/job_files/file.brf`.

### `ValueError: Artifact destination path is too long`

Shorten the **Project Title**, school name, or student initials so the
resulting file path stays under 240 characters.

---

## Backup Failures

### `RuntimeError: Insufficient disk space`

APM requires at least 2× the database size free in the backups directory.
Free up disk space or point `ACCESSMAN_DB_PATH` to a drive with more space.

---

## QA Tools Show "Not on PATH"

This is expected if the tool is not installed.  APM degrades gracefully.

To install DAISY Ace:
```bash
npm install -g @daisy/ace
```

To install EPUBCheck, download from
<https://github.com/w3c/epubcheck/releases> and add it to your `PATH`, or
configure the path in `tools.ini`.
