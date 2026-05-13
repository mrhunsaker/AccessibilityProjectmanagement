# Accessibility Project Manager — Full Audit Report

**Date:** 2026-05-12  
**Audited against:** `implementation_outline.json`, `CHANGES.md`, `README.md`, all source files  
**Note:** `IMPLEMENTATION_PLAN.md` was not included in the shared files. This audit uses the `implementation_outline.json` phases plus the planned items in `README.md` and `CHANGES.md` as the reference baseline.

---

## Executive Summary

The application core is in excellent shape. All 17 page handlers are correctly wired in `PAGE_DEFINITIONS`, all `queries.py` `__all__` exports have matching function definitions, and the schema tables are fully aligned with query usage. The six implementation phases from `implementation_outline.json` are largely complete, with Phase 6 (Authentication) being a deliberate stub.

**Two bugs require immediate fixes before they can corrupt data or silently misbehave at runtime.** The remaining issues are medium/low priority cleanup items.

---

## Page Handler Wiring

All 17 pages in `PAGE_DEFINITIONS` resolve to existing functions. ✅

| Page               | Module                | Function                | Status |
| ------------------ | --------------------- | ----------------------- | ------ |
| Dashboard          | `ui.dashboard`        | `dashboard_page`        | ✅     |
| Search             | `ui.search`           | `search_page`           | ✅     |
| Braille Jobs       | `ui.braille_jobs`     | `braille_jobs_page`     | ✅     |
| Large Print Jobs   | `ui.lp_ebraille`      | `large_print_jobs_page` | ✅     |
| eBraille Jobs      | `ui.lp_ebraille`      | `ebraille_jobs_page`    | ✅     |
| EPUB3 / DAISY Jobs | `ui.lp_ebraille`      | `epub3_daisy_jobs_page` | ✅     |
| Tactile Graphics   | `ui.tactile_graphics` | `tactile_graphics_page` | ✅     |
| 3-D Print Jobs     | `ui.print_jobs`       | `print_jobs_page`       | ✅     |
| Filament           | `ui.inventory_panels` | `filament_page`         | ✅     |
| Braille Paper      | `ui.inventory_panels` | `paper_page`            | ✅     |
| Electronics        | `ui.inventory_panels` | `electronics_page`      | ✅     |
| File Ingestion     | `ui.ingestion`        | `ingestion_page`        | ✅     |
| Metadata Editor    | `ui.metadata_editor`  | `metadata_editor_page`  | ✅     |
| Lineage Viewer     | `ui.lineage`          | `lineage_page`          | ✅     |
| QA Tooling         | `ui.qa`               | `qa_page`               | ✅     |
| Pipelines          | `ui.pipelines`        | `pipelines_page`        | ✅     |
| Admin Settings     | `ui.admin`            | `admin_page`            | ✅     |

---

## Database Layer Alignment

- All `queries.py` `__all__` exports have matching `def` implementations. ✅
- All tables referenced in SQL strings exist in `_SCHEMA_SQL`. ✅
- All tables in schema are covered by query functions. ✅
- `_TABLES_WITH_UPDATED_AT` is consistent with schema column definitions. ✅
- Entry points `AccessMan` and `AccessMan-seed` resolve to existing `main()` functions. ✅
- Import aliases (`db`, `services`, `ui`) in `__init__.py` enable legacy imports. ✅

---

## Implementation Phase Status

### Phase 1 — Workflow Execution Engine `[CRITICAL]` ✅ Complete

`complete_step()` and `revert_step()` are implemented for `braille`, `lp_ebraille`, and `tactile` job types. `PipelineService` orchestrates multi-step external tool pipelines with full DB persistence.

**⚠ Caveat:** `workflow_step` seed data includes 5 steps for job type `"print"` (`designed`, `sliced`, `printed`, `inspected`, `delivered`), but `complete_step()` raises `ValueError` for `job_type="print"` because it is absent from `_STEP_TABLES`. The seeded print steps are orphaned. See Fix #4 below.

### Phase 2 — File Ingestion Subsystem `[CRITICAL]` ✅ Complete

`ingest_file()` computes SHA-256, detects MIME type, stores files either under `artifacts/<project>/` (named by student/school/grade/subject) or legacy UUID paths under `job_files/`. PREMIS events are logged on ingestion. The ingestion page supports both path-based entry and browser upload.

**⚠ Caveat:** `delete_file_object()` is broken for artifact-stored files. See Fix #2 below.

### Phase 3 — Asset Lineage Graphing `[HIGH]` 🟡 Partial

`lineage_page()` renders a Mermaid DAG connecting jobs to their attached files. The `structural_map_node` table is fully defined and queryable, but there is no UI for creating or managing structural map nodes. Derivative file-to-file parent/child chains are not visualized. The lineage page only covers `braille` and `lp_ebraille` job types — `tactile` and `print` jobs are absent.

**⚠ Bug:** Dead code on lines ~50–52 of `lineage.py` calls `Q.list_files_for_job("braille", -1)` with a placeholder comment but assigns the result to `links` which is never used. The correct per-job iteration follows immediately below. See Fix #1 below.

### Phase 4 — Metadata Schema System `[HIGH]` ✅ Complete

The full Dublin Core 15-element set, eBraille profile fields, and METS/PREMIS fields are seeded into `material_category`. `metadata_options.py` loads keys at runtime from the database, allowing Admin → Metadata Options to extend or deactivate keys app-wide. `backfill_metadata_keys()` provides typo normalization with difflib fuzzy matching. `metadata_editor_page()` exposes cross-job editing for all job types.

### Phase 5 — Search and Indexing `[MEDIUM]` ✅ Complete

`search_page()` performs in-memory full-text matching across braille, LP/eBraille, tactile graphics, print jobs, file objects, and all job metadata. Covers title, requester, notes, filename, format, encoding, and both metadata keys and values. Suitable for current single-user scale; a SQL `LIKE` implementation would be needed for larger datasets.

### Phase 6 — Authentication and RBAC `[MEDIUM]` ❌ Stub Only

`AuthService` in `services/auth_service.py` holds a hardcoded two-user list in memory. `authentication_page()` provides a UI switcher only. There is no session management, no NiceGUI `@ui.page` auth middleware, no cookie or JWT handling, and the page is not wired into `PAGE_DEFINITIONS` so it is unreachable from the running app. NiceGUI's built-in auth support (decorating page routes) has not been implemented.

---

## Bugs Requiring Fixes

### 🔴 Fix #1 — `lineage.py`: Dead query with `job_id=-1`

**File:** `accessibility_mgr/ui/lineage.py` ~lines 50–52

The following block is a leftover placeholder that executes a DB query against a non-existent job (id=-1) and assigns the result to `links`, which is never used. The correct per-job file lookup occurs in the for loops that follow immediately after.

```python
# REMOVE THIS BLOCK:
for f in files:
    fnode = f"F{f['id']}"
    links = Q.list_files_for_job("braille", -1)  # placeholder; we iterate all
```

**Fix:** Delete those three lines.

---

### 🔴 Fix #2 — `queries.py`: `delete_file_object()` breaks for artifact-stored files

**File:** `accessibility_mgr/db/queries.py`, function `delete_file_object()`

When `ingest_file()` is called with a `project_title`, it stores the file under `artifacts/` and saves the **absolute path** in `stored_path`. But `delete_file_object()` always does:

```python
stored = FILES_DIR / row["stored_path"]
```

Joining an absolute path onto `FILES_DIR` with `/` in Python produces the absolute path alone (the left side is discarded), so `stored.unlink()` will attempt to delete from the correct location — _but only by accident_, and only on some platforms. The behavior is implementation-defined and should be made explicit.

```python
# Current (brittle):
stored = FILES_DIR / row["stored_path"]

# Fix:
_p = Path(row["stored_path"])
stored = _p if _p.is_absolute() else FILES_DIR / _p
```

---

### 🟡 Fix #3 — `models/inventory.py`: Missing file

**Files:** `accessibility_mgr/ui/categories.py`, `accessibility_mgr/services/inventory_service.py`

Both files import `Category`, `InventoryItem`, and `InventoryTransaction` from `models/inventory.py`, which does not exist. Neither file is in `PAGE_DEFINITIONS` and neither is reachable from the running app, so there is no crash at startup — but the files are broken and will fail if ever imported (e.g. during testing or future wiring).

**Fix (Option A — create the stub):**

```python
# accessibility_mgr/models/inventory.py
"""Legacy SQLAlchemy inventory models (stub — not used in active NiceGUI flow)."""
from __future__ import annotations
from sqlalchemy import Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.database import Base

class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    current_quantity: Mapped[float] = mapped_column(Float, default=0)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=True)

class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"))
    transaction_type: Mapped[str] = mapped_column(String(50))
    quantity: Mapped[float] = mapped_column(Float)
    previous_quantity: Mapped[float] = mapped_column(Float)
    new_quantity: Mapped[float] = mapped_column(Float)
    notes: Mapped[str] = mapped_column(Text, default="")
    project_id: Mapped[int] = mapped_column(Integer, nullable=True)
```

Also add to `models/__init__.py`:

```python
from .inventory import Category, InventoryItem, InventoryTransaction
```

**Fix (Option B — guard the imports):** Add `try/except ImportError` wrappers in `categories.py` and `inventory_service.py` since these legacy files are not used by the active app flow.

---

### 🟡 Fix #4 — `queries.py` / `schema.py`: Orphaned `print` workflow steps

**Files:** `accessibility_mgr/db/schema.py` (seed data), `accessibility_mgr/db/queries.py` (`_STEP_TABLES`)

The seed data in `_SCHEMA_SQL` inserts 5 workflow steps for `job_type = 'print'`:

```sql
INSERT OR IGNORE INTO workflow_step (job_type, step_key, ...) VALUES
    ('print','designed', ...),
    ('print','sliced', ...),
    ('print','printed', ...),
    ('print','inspected', ...),
    ('print','delivered', ...);
```

But `complete_step()` only supports `braille`, `lp_ebraille`, and `tactile`. Calling it with `"print"` raises `ValueError`. The `print_jobs_page` uses a `successful` boolean flag rather than discrete steps, so these seeded steps are never consumed.

**Recommended Fix (Option B — remove the orphaned seed rows):** Remove the 5 `('print', ...)` rows from the `INSERT OR IGNORE INTO workflow_step` block in `schema.py`. The print job model does not need step-level tracking since success/fail is sufficient.

If step-level tracking for print jobs is desired in future, add `"print": "print_job"` to `_STEP_TABLES` and `"print": ["designed", "sliced", "printed", "inspected", "delivered"]` to `_ALLOWED_STEPS`, and add a `_migrate()` step to add the boolean columns to `print_job`.

---

### 🟡 Fix #5 — `dashboard.py`: Fragile `__import__` in Quick Launch buttons

**File:** `accessibility_mgr/ui/dashboard.py`

The Quick Launch buttons use runtime `__import__` calls:

```python
ui.button("Braille Jobs", on_click=lambda: __import__(
    "accessibility_mgr.ui.braille_jobs", fromlist=["braille_jobs_page"]
).braille_jobs_page(content_area))
```

If any of these modules fail to import (e.g. a syntax error introduced during development), the button click silently does nothing. Since all these modules are already loaded at app startup via `PAGE_DEFINITIONS`, they are available in `sys.modules`.

**Fix:** Resolve the handlers at module load time from the already-populated `PAGES` list, or import at the top of `dashboard.py`:

```python
from accessibility_mgr.ui import braille_jobs, lp_ebraille, tactile_graphics
# then:
ui.button("Braille Jobs", on_click=lambda: braille_jobs.braille_jobs_page(content_area))
```

---

## Lower-Priority Improvements

### 🔵 Lineage page missing tactile and print jobs

`lineage_page()` only builds DAG edges for `braille` and `lp_ebraille` job types. Tactile graphics jobs and print jobs (which can have files linked via `job_file_link`) are invisible. Add equivalent loops for `list_tactile_jobs()` and `list_print_jobs()` in the edge-building section.

### 🔵 Structural map node UI missing

The `structural_map_node` table (METS `<structMap>/<div>` equivalent) has full CRUD support in `queries.py` (`add_struct_node`, `list_struct_nodes`, `delete_struct_node`) but there is no UI for it. Consider adding a "Structure" tab to the job detail views in `braille_jobs.py` and `lp_ebraille.py`.

### 🔵 Stub docstrings on inner functions

Virtually every `_do()`, `_save()`, `_del()`, `_edit()` nested function has an auto-generated stub docstring (`"""do. Parameters ---------- ...`). These add visual noise and no value. They should either be removed entirely or replaced with a single meaningful line.

### 🔵 Authentication page unreachable

`ui/authentication.py` and `services/auth_service.py` exist but `authentication_page` is not in `PAGE_DEFINITIONS`. Either add it as a placeholder Admin sub-tab, or add a comment explaining it is intentionally deferred.

---

## Test Coverage Gaps (30% of function groups covered)

The existing tests in `tests/test_queries.py` cover the happy path for filament CRUD, braille job workflow, metadata, LP jobs, pipeline/QA runs, and material categories. The following are untested:

| Gap                                                                     | Priority       |
| ----------------------------------------------------------------------- | -------------- |
| `add_paper / update_paper / delete_paper`                               | High           |
| `add_electronic / update_electronic / delete_electronic`                | High           |
| `add_printer / update_printer / delete_printer`                         | High           |
| `add_embosser / update_embosser / delete_embosser`                      | High           |
| `add_print_job` (including filament deduction side effect)              | High           |
| `add_tactile_job / complete_step("tactile") / get_tactile_job`          | High           |
| `ingest_file` (create temp file, ingest, verify checksum + stored_path) | High           |
| `link_file_to_job / list_files_for_job / unlink_file_from_job`          | Medium         |
| `log_backup / list_backup_log`                                          | Medium         |
| `backfill_metadata_keys`                                                | Medium         |
| `add_struct_node / list_struct_nodes / delete_struct_node`              | Low            |
| `delete_file_object` with absolute path (Fix #2 regression test)        | High after fix |

---

## Not-Yet-Implemented Features (Roadmap Items)

These are acknowledged as planned but not yet started:

| Feature                        | Notes                                                                                                                                                              |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Reporting & Analytics**      | No reports page exists. A logical home would be a new `reports.py` page wired into Overview group.                                                                 |
| **Authentication**             | NiceGUI's `app.on_connect` + session storage is the recommended approach.                                                                                          |
| **Preservation export**        | `package_service.py` has a stub `export_package()` that only uses SQLAlchemy assets. A SQLite-native version using `ingest_file` records would be straightforward. |
| **Derivative file lineage**    | `file_object` has no `parent_file_id` FK. Adding one + UI in `lineage_page` would enable true derivative chains.                                                   |
| **Structural map node editor** | Full CRUD is in `queries.py` — only a UI tab is needed.                                                                                                            |

---

## Summary Score

| Area                          | Status                                                      |
| ----------------------------- | ----------------------------------------------------------- |
| Page handler wiring           | ✅ All 17 wired correctly                                   |
| DB schema ↔ queries alignment | ✅ Fully consistent                                         |
| `__all__` ↔ definitions       | ✅ Fully consistent                                         |
| Phase 1 – Workflow Engine     | ✅ Complete (1 caveat)                                      |
| Phase 2 – File Ingestion      | ✅ Complete (1 bug)                                         |
| Phase 3 – Lineage Graphing    | 🟡 Partial (1 bug, missing tactile/print, no struct map UI) |
| Phase 4 – Metadata Schema     | ✅ Complete                                                 |
| Phase 5 – Search              | ✅ Complete                                                 |
| Phase 6 – Authentication      | ❌ Stub only                                                |
| Test coverage                 | 🟡 ~30% of function groups                                  |
| Broken/missing files          | 🟡 `models/inventory.py` missing                            |
| Orphaned seed data            | 🟡 Print workflow_steps                                     |
