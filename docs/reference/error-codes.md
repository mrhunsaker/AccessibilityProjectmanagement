# Error Reference

---

## Application Startup

| Error | Cause | Resolution |
|-------|-------|-----------|
| `FileNotFoundError: .secrets` | `.secrets` file missing from repository root | Create `.secrets` with at least `STORAGE_SECRET` |
| `ValueError: Storage secret is missing or empty` | `STORAGE_SECRET` not in `.secrets` | Add `STORAGE_SECRET=<value>` |
| `RuntimeError: Database schema is missing step date columns` | Incomplete migration | Delete the database and restart to rebuild, or run `init_db()` manually |
| `ModuleNotFoundError` | Dependency not installed | Run `uv sync` |

---

## Authentication

| Error | Cause | Resolution |
|-------|-------|-----------|
| "No Password Configured" banner | `ACCESSMAN_PASSWORD_HASH` not set and `ACCESSMAN_UNPROTECTED` ≠ 1 | Generate a hash or set `ACCESSMAN_UNPROTECTED=1` for dev |
| "Incorrect password" | Wrong password entered | Check the password used when generating `ACCESSMAN_PASSWORD_HASH` |
| "Password cannot be empty" | Empty form submission | Enter a non-empty password |

---

## File Ingestion

| Error | Cause | Resolution |
|-------|-------|-----------|
| `FileNotFoundError: Source file not found` | Path does not exist | Verify the path; the file must be accessible from the server machine |
| `PermissionError: ingest_file: source outside permitted staging directory` | File is not in `FILES_DIR` (SEC-004) | Upload through the browser upload panel first, then ingest |
| `ValueError: Artifact destination path is too long` | Project title + metadata produces a path > 240 chars | Shorten the project title or student/school fields |

---

## Database

| Error | Cause | Resolution |
|-------|-------|-----------|
| `sqlite3.IntegrityError` on delete | Foreign key constraint (e.g. deleting a printer with active jobs) | Remove or reassign dependent records first |
| `ValueError: No valid fields to update` | All fields passed to `update_*` are outside the allow-list | Check the `allowed` set in the relevant `update_*` function |
| `ValueError: Disallowed table` | `_build_update_sql()` called with an unregistered table name | Add the table to `_SAFE_TABLES` in `db/queries.py` |

---

## Execution Service

| Return code | Meaning |
|-------------|---------|
| `0` | Success |
| `-1` | Command not found (binary not on PATH) |
| `-2` | Timeout expired |
| `-3` | Unexpected Python exception |
| `-4` | Binary not in `ALLOWED_EXECUTABLES` allow-list |
| `-5` | Required binary not found (pipeline pre-check) |

---

## REST API

| HTTP status | Meaning |
|-------------|---------|
| `401 Unauthorized` | Missing or invalid `X-API-Key` header |
| `200 OK` | Success |
