# Data Flow

---

## Job Creation

```
User (UI form)
  │
  ▼
ui/<job_type>.py  _job_dialog() on_save()
  │
  ▼
db/queries.py  add_braille_job() / add_lp_job() / etc.
  │  ├── INSERT INTO <job_table>
  │  └── log_event("CREATE", "SUCCESS")
  ▼
SQLite  accessibility_manager.db
```

---

## File Ingestion

```
User provides path or uploads file
  │
  ▼
ui/ingestion.py  (or _ingest_dialog() in job panels)
  │
  ▼
db/queries.py  ingest_file()
  │  ├── Resolve source path (must be inside FILES_DIR — SEC-004)
  │  ├── Copy to artifacts/<ProjectTitle>/<name>.<ext>
  │  ├── Compute SHA-256 checksum
  │  ├── INSERT INTO file_object
  │  └── (optional) link_file_to_job() + log_event("INGEST")
  ▼
Filesystem  ~/.local/share/accessibility_mgr/artifacts/
SQLite     file_object, job_file_link, metadata_event
```

---

## Step Completion

```
User clicks "Mark Done"
  │
  ▼
ui/<job_type>.py  _complete()
  │  └── if step == "delivered":  open_delivery_dialog()
  │       else: Q.complete_step(job_type, job_id, step)
  │
  ▼
db/queries.py  complete_step()
  │  ├── UPDATE <table> SET <step>=1, <step>_date=datetime('now')
  │  └── log_event("STEP_COMPLETE")
  ▼
SQLite
```

---

## Delivery

```
User fills delivery dialog
  │
  ▼
ui/delivery_dialog.py  _confirm()
  │
  ▼
db/queries.py  record_delivery()
  │  ├── UPDATE <table> SET delivered=1, delivery_date=..., delivery_method=...
  │  └── log_event("DELIVERY")
  ▼
SQLite
```

---

## Search

```
User types query
  │
  ▼
ui/search.py  _execute()
  │
  ▼
db/queries.py  search_all(query)
  │  ├── Try FTS5 virtual tables (fast)
  │  └── Fallback: LIKE queries on all tables
  │
  ▼
Returns dict keyed by category:
  braille_jobs, lp_jobs, tactile_jobs, print_jobs,
  files, metadata, events, students
```

---

## REST API

```
External caller
  │  POST /api/workflows/enqueue
  ▼
api/platform_api.py  enqueue_workflow()
  │  └── _require_api_auth() via X-API-Key header
  │
  ▼
services/singletons.py  queue.enqueue()
  ├── WorkflowQueueService (in-memory)
  └── (shared with UI workflow monitor)
```
