# Changelog

All notable changes to this project will be documented in this file.

The format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

# 2026-09-07

## Added

### CSV Bulk Import for Students
- Added `student_import.py` service with CSV template generation, preview, and single-transaction import
- Added a downloadable CSV template via the students page (served in memory, `students_template.csv`)
- Added a **+ BULK IMPORT** button next to **+ Add Student** that opens a native file picker (`.csv`)
- Added an import preview dialog that buckets rows into **to add** / **to skip** / **errors** before committing
- Students are de-duplicated on the `(first_name, last_name)` business key (case-insensitive); duplicates in the file and existing database rows are skipped, never overwritten
- Rows missing a first or last name are reported as row-level errors rather than silently skipped
- Added `tests/test_student_import.py` covering add, in-file and database de-duplication, invalid-row errors, and template output (4 tests)

### GLOW (ACB Large Print Toolkit) Integration
- Registered GLOW as a CLI QA tool (`glow = acb-large-print`) in `qa_service.py` and the Execution Service allow-list
- Added a **Large Print (ACB/GLOW) Pipeline** in `pipeline_service.py`
- Added `run_glow_audit` and GLOW binary discovery to `toolchain_binaries.py`
- Added a GLOW card to the binary integrations dashboard

### FIDO (DAISY Labs AI) Integration
- Registered FIDO as a **manual-review** QA tool (`manual_review=True`) since it has no stable CLI
- Documented FIDO's desktop-only workflow in `tools.ini` / `tools.ini.example`

### File Picker Dialogs
- Added a reusable `file_picker` component that stages selected files into `FILES_DIR` (`components.py`)
- Replaced manual file-path typing in job attach dialogs and the print job model-file dialog

### Open Project Folder
- Added an **Open Project Folder** affordance to job Files cards via the `open_folder` helper

## Changed

- Configured `tools.ini` and `tools.ini.example` with `glow = acb-large-print` and a commented `# fido =` entry
- Updated README and MkDocs documentation to cover GLOW/FIDO integration
- Documented the CSV bulk-import workflow in the Students user guide

---

# 2026-08-20

## Added

### Interactive Setup Assistant
- Added `setup.py` interactive terminal setup assistant (OS detection, prerequisite checks, `.secrets` creation with auto-generated secrets, `tools.ini` setup from example, validation)
- Added `setup.sh` launcher for macOS/Linux
- Added `setup.bat` launcher for Windows

### Auto-Setup Integration
- App now auto-runs `setup.py` when `.secrets` is missing on first launch

## Changed

- `load_secrets()` in `app.py` no longer crashes on missing `.secrets`; instead launches the setup assistant automatically
- Updated README.md quick-start to reflect new auto-setup flow
- Updated MkDocs installation, configuration, troubleshooting, and deployment docs

---

# 2026-07-15

## Added

### Test Suite
- Created `tests/conftest.py` with shared database fixtures
- Created `tests/test_services.py` with 60 service-layer tests (RBAC, authentication, SLA monitoring, workflow DAG, persistent queue/analytics/provenance, artifact retention, audit log, event stream, distributed workers, multi-tenant, metadata validation, compliance reporting, execution service, worker runtime, base analytics, base provenance, workflow queue)
- Created `tests/test_api.py` with 16 API endpoint tests (healthcheck, workflow listing/enqueue, analytics summary, provenance events, API key authentication enforcement)

### Build Infrastructure
- Added `sys._MEIPASS` detection in `app.py` for PyInstaller frozen-mode favicon resolution
- Added `version.py` for dynamic date-based versioning (YYYY.M.D format)
- Added `_base_path()` and `_get_version()` helpers in `app.py`

### API Security
- Added RBAC permission-gated FastAPI dependencies (`_dep_workflow_read`, `_dep_workflow_manage`, `_dep_analytics_view`, `_dep_governance_manage`)
- Added `governance.manage` permission to the operator role

### Workflow Queue Service
- Fleshed out `workflow_queue.py` with full `WorkflowQueueService` implementation (in-memory priority queue with `enqueue`, `next_job`, `complete_job`, `fail_job`, `list_jobs`)

## Changed

### Build Scripts
- Fixed `--add-data` paths in `build_linux.sh`, `build_macos.sh`, `build_windows.bat` (resources directory is at project root, not under `accessibility_mgr/`)
- Fixed `--icon` path in `build_windows.bat` to `resources\icons\icon.ico`
- Removed `--icon=...favicon.icns` from `build_macos.sh` (no `.icns` file exists)
- Fixed `build_windows.bat` entry point path to use backslash

### Containerfile
- Fixed build order: copy full source before `uv pip install` (hatchling needs source to build wheel)
- Replaced `curl`-based healthcheck with Python `urllib.request` (curl not in `python:3.12-slim`)
- Removed premature `COPY tools.ini.example tools.ini`

### podman-compose.yml
- Removed deprecated `version: '3.8'` key

### Dynamic Versioning
- Replaced hardcoded `version = "2026.6.9"` with `dynamic = ["version"]` using hatchling `code` source
- FastAPI app version now reads from `importlib.metadata` at runtime
- Health endpoint now includes `version` field

### License
- Changed classifier in `pyproject.toml` from `MIT License` to `Apache Software License`
- Updated `docs/index.md` and `docs/project/contributors.md` to reference Apache 2.0
- Replaced MIT license text in `docs/license.md` with Apache 2.0 summary

### Documentation Accessibility
- Removed all unicode emoji from 35 markdown files in `docs/`
- Replaced checkmark symbols (`✅`, `❌`) with text (`Yes`, `No`) in table cells
- All section headers are now plain ASCII text

### Service Fixes
- Added `conn.row_factory = sqlite3.Row` to `_connect()` in 7 services: `sla_monitoring.py`, `workflow_dag.py`, `artifact_retention.py`, `audit_log.py`, `event_stream.py`, `distributed_workers.py`, `multi_tenant.py`

### Technical Debt
- Wired `ACCESSMAN_LOG_LEVEL` environment variable into `app.py` logging setup
- Fixed `CHANGELOG.md` references to `CHANGES.md` in `docs/project/release-process.md`
- Synced `CHANGES.md` content into `docs/changelog.md`

## Removed

- Removed unused `json` import from `sla_monitoring.py`
- Removed unused `dataclasses.asdict` import from `sla_monitoring.py` and `workflow_dag.py`
- Removed unused `dataclasses.field` import from `workflow_queue.py`

---

# 2026-05-17

## Added

### Enterprise Workflow Orchestration
- Persistent SQLite-backed workflow queue
- Workflow DAG orchestration engine
- Workflow dependency resolution
- Workflow replay and recovery engine
- Distributed reconciliation service
- Worker heartbeat monitoring
- Worker failover detection
- SLA monitoring infrastructure
- Distributed worker registry

### Accessibility Automation
- Production DAISY Ace binary integration
- Production EPUBCheck integration
- Secure subprocess sandboxing layer
- Accessibility toolchain telemetry
- Artifact capture orchestration
- Timeout-controlled binary execution
- Binary integration monitoring dashboard

### CI/CD Accessibility Governance
- GitHub Actions accessibility validation workflow
- CI/CD accessibility validation orchestration
- Accessibility severity-threshold policy engine
- Release-blocking governance enforcement
- Automated EPUB accessibility validation
- Pipeline execution telemetry
- CI/CD governance dashboard

### Security and Identity
- Tenant-aware RBAC enforcement
- Authentication middleware
- API token validation
- Credential vault abstraction
- Permission evaluation engine
- Multi-tenant organization infrastructure
- Tenant membership management

### Reliability Infrastructure
- Webhook retry engine
- Dead-letter queue support
- Persistent event store
- Signed event persistence
- Artifact retention lifecycle management
- Automated artifact cleanup
- Distributed orchestration telemetry

### Governance and Compliance
- Operational provenance registry
- Audit-grade event tracking
- Governance workflow telemetry
- Compliance-oriented workflow orchestration
- Operational analytics persistence

## Changed

- Expanded repository architecture from NiceGUI workflow application into enterprise accessibility governance platform
- Transitioned orchestration layer from in-memory execution to durable distributed workflow infrastructure
- Transitioned accessibility tooling from execution stubs to production binary integration model
- Expanded CI/CD support into deployable accessibility governance automation
- Expanded RBAC implementation into tenant-aware authorization model
- Expanded operational telemetry into audit-grade event persistence architecture
- Expanded reliability infrastructure with replay/recovery semantics and distributed reconciliation

## Planned

- Real encrypted KMS/HSM-backed secret storage
- Queue partitioning and distributed workload balancing
- Tenant-aware API authorization middleware
- Signed governance export generation
- Immutable compliance snapshot exports
- Workflow auto-remediation routing
- Adaptive orchestration retry policies
- Distributed auto-scaling workers

---

# 2026-05-09

## Added

- Initial NiceGUI application shell
- Dynamic page loading for UI modules
- Sidebar-based navigation
- Responsive content layout
- Dashboard integration
- Graceful handling for incomplete UI modules
- Application-wide color/theme configuration
- Header/status display components
- Architecture and workflow audit documentation
- LLM remediation prompt specification (`prompt.json`)
- Asset Registry NiceGUI page
- Metadata workflow visibility dashboard
- METS-inspired asset management concepts
- Metadata lineage planning documentation

## Changed

- Replaced placeholder `app.py` implementation with a functional NiceGUI frontend
- Updated project documentation to reflect current architecture
- Updated README to document NiceGUI migration strategy
- Updated repository structure documentation
- Clarified technology stack and workflow functionality
- Expanded application shell to include metadata-oriented workflows
- Expanded project scope toward preservation-oriented accessibility production

## Planned

- Full migration from Textual TUI to NiceGUI
- CRUD interfaces for all production workflows
- Reporting and analytics
- Authentication support
- Accessibility auditing improvements
- Multi-user operation support
- Full metadata lineage tracking
- Asset version graph visualization
- Preservation export tooling
- Workflow automation pipelines
