# Debugging

---

## 📋 Log Output

APM uses Python's standard `logging` module.  Enable verbose output by setting
`ACCESSMAN_LOG_LEVEL=DEBUG` in `.secrets`:

```ini
ACCESSMAN_LOG_LEVEL=DEBUG
```

Or pass it on the command line:

```bash
ACCESSMAN_LOG_LEVEL=DEBUG uv run AccessMan
```

Key loggers:

| Logger | What it covers |
|--------|----------------|
| `accessibility_mgr.app` | Page load errors, handler exceptions |
| `accessibility_mgr.db.schema` | Migration steps, schema validation |
| `accessibility_mgr.services.backup_service` | Backup success/failure |
| `accessibility_mgr.services.tools_service` | Tool path resolution |
| `accessibility_mgr.services.authentication` | Token validation attempts |

---

## 🚨 Failed Pages

If a UI module fails to import at startup, it appears under **"Failed to load"**
in the sidebar with a red `error_outline` icon.  Hover over it to see the
module path and function name.

The `FAILED_PAGES` list is printed to the console log at startup with the full
traceback.

---

## 🗄️ Inspecting the Database

```bash
sqlite3 ~/.local/share/accessibility_mgr/accessibility_manager.db
```

Useful queries:

```sql
-- Recent events
SELECT * FROM metadata_event ORDER BY event_datetime DESC LIMIT 20;

-- Jobs with no student linked
SELECT id, title FROM braille_job WHERE student_id IS NULL;

-- FTS sanity check
SELECT * FROM braille_job_fts WHERE braille_job_fts MATCH 'math';

-- Check migrations
SELECT * FROM schema_migration ORDER BY applied_at;
```

---

## 🔍 Page Errors in UI

When a page handler raises an unhandled exception, `render_page()` catches it
and displays a red error card containing:
- The exception message
- The full Python traceback (rendered in a scrollable code block)

This means you can usually diagnose UI bugs without looking at terminal output.

---

## 🛠️ Development Mode

Set `ACCESSMAN_DEV=1` to enable development-only seed data in the Operations
Dashboard and Workflow Monitor pages:

```ini
ACCESSMAN_DEV=1
```

---

## 🔄 Hot Reload

NiceGUI's hot reload is **disabled** (`reload=False`) in production to prevent
accidental restarts in a studio environment.  For development, temporarily
enable it in `app.py`:

```python
ui.run(reload=True, ...)
```
