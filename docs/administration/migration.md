# Database Migrations

APM uses an **incremental migration system** built on top of SQLite.  There
is no separate migration tool — migrations run automatically on every startup
via `init_db()`.

---

## 🔄 How It Works

1. `init_db()` runs the full `_SCHEMA_SQL` block with `CREATE TABLE IF NOT EXISTS`.
   This is idempotent and safe to run on existing databases.
2. `_migrate()` then checks the `schema_migration` table and applies any
   pending numbered migration functions.
3. Each migration is tracked by a string ID (e.g. `m004_student_table_and_links`).
   Once marked as applied it is never re-run.

---

## 📋 Applied Migrations

| ID | Description |
|----|-------------|
| `m001_braille_embosser_and_timestamps` | Added `embosser_id` to `braille_job`; added `created_at`/`updated_at` to printers and embossers |
| `m002_workflow_step_columns` | Added `updated_at` and `description` to `workflow_step` |
| `m003_backup_log_table` | Created `backup_log` table |
| `m004_student_table_and_links` | Created `student` table; added `student_id` FK to all job tables |
| `m005_print_step_columns` | Added workflow step boolean columns to `print_job` |
| `m006_delivery_columns` | Added `delivery_date/method/recipient/notes` to all job tables |
| `m007_normalize_file_use_master` | Renamed `MASTER` → `ORIGINAL` in existing `file_object` rows |
| `m008_step_completion_timestamps` | Added `<step>_date` columns to all job tables |
| `m009_full_text_search_indexes` | Created FTS5 virtual tables and triggers for fast search |
| `m010_step_date_columns` | Second pass to ensure all `*_date` columns exist (idempotent) |

---

## ➕ Adding a New Migration

1. Open `accessibility_mgr/db/schema.py`.
2. Add a new function `_mNNN_your_description()` inside `_migrate()`.
3. Call `_apply_migration(conn, "mNNN_your_description", _mNNN_your_description)`.

```python
def _m011_example_column() -> None:
    if not _table_has_column(conn, "braille_job", "new_column"):
        conn.execute("ALTER TABLE braille_job ADD COLUMN new_column TEXT")

_apply_migration(conn, "m011_example_column", _m011_example_column)
```

**Rules**:
- Always guard column additions with `_table_has_column()`.
- Use `CREATE TABLE IF NOT EXISTS` for new tables.
- Never modify or delete existing migration functions.
- Increment the number prefix to ensure correct ordering.

---

## 🔍 Schema Validation

After migrations run, `_validate_step_columns()` verifies that every expected
`<step>_date` column exists in the live schema.  If any column is missing the
app raises `RuntimeError` at startup with a clear list of the missing columns.

---

## 📁 Manual Inspection

```bash
sqlite3 ~/.local/share/accessibility_mgr/accessibility_manager.db \
  "SELECT * FROM schema_migration ORDER BY applied_at;"
```
