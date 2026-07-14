# Code Structure

```
AccessibilityProjectManagement/
├── accessibility_mgr/
│   ├── __init__.py          # Legacy import aliases (db, services, ui)
│   ├── app.py               # NiceGUI entry point, page registry, startup
│   ├── api/
│   │   └── platform_api.py  # FastAPI app mounted at /api
│   ├── db/
│   │   ├── schema.py        # CREATE TABLE, migrations, init_db()
│   │   ├── queries.py       # All SQL — CRUD + search + reporting
│   │   └── seed_import.py   # CSV inventory import CLI
│   ├── integrations/
│   │   └── cicd_hooks.py    # CI/CD accessibility validation hooks
│   ├── services/
│   │   ├── singletons.py    # Shared service instances (SQLite-backed)
│   │   ├── authentication.py
│   │   ├── backup_service.py
│   │   ├── pipeline_service.py
│   │   ├── qa_service.py
│   │   ├── execution_service.py
│   │   ├── tools_service.py
│   │   ├── persistent_queue.py
│   │   ├── persistent_analytics.py
│   │   ├── persistent_provenance.py
│   │   └── ...              # Analytics, provenance, SLA, etc.
│   └── ui/
│       ├── components.py    # Shared badges, dialogs, progress bars
│       ├── job_components.py # Shared metadata editor, event log
│       ├── delivery_dialog.py
│       ├── metadata_options.py
│       ├── dashboard.py
│       ├── braille_jobs.py
│       ├── lp_ebraille.py
│       ├── tactile_graphics.py
│       ├── print_jobs.py
│       ├── reports.py
│       ├── search.py
│       ├── ingestion.py
│       ├── lineage.py
│       ├── qa.py
│       ├── pipelines.py
│       ├── admin.py
│       └── ...
├── docs/                    # MkDocs documentation
├── resources/icons/         # SVG favicon
├── tools.ini.example        # Tool path configuration template
└── .secrets                 # Runtime secrets (never committed)
```

---

## Key Design Principles

**Single SQL module** — all database queries live in `db/queries.py`.
No SQL strings appear outside this file.  All user values are bound via `?`
placeholders.

**Allow-list updates** — `_build_update_sql()` validates column names against
an explicit `allowed` set before constructing any UPDATE statement.

**Singleton services** — `services/singletons.py` exports shared instances
of `PersistentWorkflowQueue`, `PersistentAnalyticsService`,
`PersistentProvenanceRegistry`, and `AuthenticationService` so the UI and
REST API share the same durable state.

**Page registry** — `PAGE_DEFINITIONS` in `app.py` is the single source of
truth for navigation structure.  Adding a page only requires adding an entry
there; the sidebar is generated automatically.
