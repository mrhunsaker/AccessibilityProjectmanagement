# Accessibility Project Manager

A production management system for accessibility materials studios — tracking the full lifecycle of braille, large print, eBraille, EPUB3/DAISY, tactile graphics, and 3-D printed accessibility materials from initial request through auditable delivery.

---

## Purpose

This application is the operational hub for teams that produce and distribute accessible materials for students and patrons with print disabilities. Every job — whether a braille transcription, a large print document, an eBraille or EPUB3/DAISY file, a tactile graphic, or a 3-D printed assistive device — is tracked through its complete production lifecycle, with a full audit trail attached to every step, every file, and every metadata change.

The goal is to be able to answer, at any time and from any piece of identifying information:

- What materials were produced for this student / school / grade / subject?
- Where is every file associated with this job, and what happened to it?
- Who did what, with which tool, at which step, and when?
- What is the current production status of every active job?
- What consumables were used, and what is remaining in stock?

---

## Core Concepts

### Jobs

A **job** is the fundamental unit of work. Every request for accessible materials creates a job of the appropriate type. Jobs progress through defined workflow stages, and every stage completion — or reversion — is recorded as a PREMIS-style event in the event log.

| Job Type | Workflow Stages |
|---|---|
| Braille | Digitized → Formatted → Brailled → Proofread → Delivered |
| Large Print | Digitized → Formatted → Converted → Proofread → Delivered |
| eBraille | Digitized → Formatted → Converted → Proofread → Delivered |
| EPUB3 / DAISY | Digitized → Formatted → Converted → Proofread → Delivered |
| Tactile Graphics | Designed → Produced → QA Reviewed → Delivered |
| 3-D Print | (logged per print run with filament tracking) |

Each job carries:
- Title, requester, request date, due date, priority
- Workflow step completion status
- Linked files with preservation metadata
- Dublin Core and extended descriptive metadata
- A full provenance event log

### Files and Preservation

Files are ingested — not just referenced — into a structured artifact store. When a file is attached to a job at any stage, the system:

1. Copies the file into `artifacts/<Project Title>/` with a standardized filename derived from project, student, school, grade, and subject metadata.
2. Computes a SHA-256 checksum for fixity verification.
3. Records the MIME type, file size, format name, format version, encoding/code table, file use classification, and any tools or processes applied.
4. Logs a PREMIS INGEST event in the job's event log.

This means the database always knows exactly where every file is, what it contains, and how it got there.

### Metadata

Descriptive metadata follows three governed vocabularies, all managed through the Admin panel and stored in the `job_metadata` table:

- **Dublin Core** (15-element set): `dc:title`, `dc:creator`, `dc:subject`, `dc:language`, etc.
- **eBraille Production Profile**: `grade_level`, `subject_area`, `isbn`, `transcriber`, `braille_code`, `contracted_status`, `nemeth_used`, `tactile_graphics_present`, etc.
- **METS / PREMIS**: `mets:file_group`, `premis:event_type`, `premis:agent`, `premis:storage_location`, etc.

Metadata keys are enforced from an approved list to prevent typos and inconsistent records. An admin backfill tool can detect and normalize non-standard keys already in the database.

### Audit Trail

Every meaningful action generates a record in the `metadata_event` table:

- Job created
- Workflow step completed or reverted
- File ingested and linked
- Manual note added by an operator
- QA tool run
- Pipeline executed

Events carry the event type, outcome, agent, timestamp, linked file (if any), and free-text detail. This creates a complete, time-ordered provenance chain for every job.

---

## Production Workflows

### Braille Jobs

Tracks braille transcription from initial receipt of a source document through embossed or electronic delivery. Supports braille types: Literary, Math (Nemeth), Science, Music.

Each job can be linked to a specific embosser (Index, ViewPlus, etc.) and paper type. Files can be attached at any workflow stage — for example, attaching the source PDF at Digitized, a BRF at Brailled, and a final copy at Delivered — each with format, encoding, and tool provenance recorded.

### Large Print Jobs

Tracks large print document production. Format output is typically PDF or DOCX, produced from a source document and proofread before delivery.

### eBraille Jobs

Tracks electronic braille (BRF, EBRF, or PEF) file production, typically produced in BrailleBlaster or similar tools. Separate from embossed braille jobs so each workflow is independently trackable.

### EPUB3 / DAISY Jobs

Tracks accessible digital publication production, including both EPUB3 with accessibility metadata and DAISY talking book formats. Integrates with the QA toolchain (DAISY Ace, EPUBCheck) for automated accessibility validation.

### Tactile Graphics Jobs

Tracks production of tactile graphics by method: Thermoform/SWELL, Hand Tooled, or Embossed Figures. Four-stage workflow: Designed → Produced → QA Reviewed → Delivered.

### 3-D Print Jobs

Logs each print run against a specific printer and filament spool. Records:
- Object name and linked print file (.3mf, .stl, .gcode)
- Filament used (grams, automatically deducted from inventory)
- Success/failure status and failure reason
- Requester and request date

Print files are stored in `prints_files/` and referenced in the database record.

---

## Inventory Management

### Filament

Tracks 3-D printer filament by brand, color, type, and diameter. Quantity is automatically decremented when a print job is logged. Low-stock warnings appear on the dashboard and in the inventory view.

### Braille Paper

Tracks sheet feed, pin feed, label stock, and specialty media by type, size, and quantity.

### Electronics

Tracks components used in adaptive switch and accessibility hardware assembly projects: microcontrollers, TRRS components, wire, switches, fasteners, solder, connectors, and custom categories. All configured categories are always shown, even when empty.

---

## File Organization

```
artifacts/
└── <Project Title>/
    └── <StudentInitials>_<SchoolName>_Grade<N>_<Subject>.<ext>

prints_files/
└── <original filename>

job_files/
└── <uuid>.<ext>          (legacy fallback when no project context is given)

backups/
└── accessibility_manager_<YYYYMMDD_HHMMSS>.db
```

The `artifacts/` directory is the primary storage location for all production files. The structured naming convention — derived from the project title, student initials, school name, grade level, and subject — makes it possible to locate any file on disk without querying the database.

The database stores the absolute path to every file, so records always resolve regardless of working directory.

---

## Database Structure

SQLite database (`accessibility_manager.db`) with WAL journaling and foreign key enforcement.

| Table | Purpose |
|---|---|
| `braille_job` | Braille transcription jobs and workflow step status |
| `lp_ebraille_job` | Large print, eBraille, and EPUB3/DAISY jobs |
| `tactile_graphics_job` | Tactile graphics jobs |
| `print_job` | 3-D print job log |
| `file_object` | Every ingested file with checksum, path, format, and use |
| `job_file_link` | Links files to jobs at specific workflow steps |
| `metadata_event` | PREMIS-style event log for all job actions |
| `job_metadata` | Dublin Core and extended descriptive metadata (key/value) |
| `structural_map_node` | METS-inspired structural map for complex documents |
| `filament` | Filament inventory |
| `braille_paper` | Paper and label stock |
| `electronics` | Electronics and hardware components |
| `printer` | 3-D printer registry |
| `embosser` | Braille embosser registry |
| `material_category` | Configurable lookup values for all dropdowns |
| `workflow_step` | Configurable workflow step definitions |
| `qa_run` | QA tool execution history |
| `pipeline_run` | Multi-step pipeline execution records |
| `pipeline_step_run` | Individual step results within a pipeline run |
| `backup_log` | Automated and manual backup history |

---

## QA and Automation

### QA Tooling

Run accessibility validation tools directly from the QA page. Every run is persisted with the full command, output, and success/failure status.

| Tool | Domain |
|---|---|
| DAISY Ace | EPUB accessibility (WCAG) |
| EPUBCheck | EPUB structural conformance |
| Liblouis / file2brl | Braille translation verification |
| BRLTTY | Braille device validation |
| Pandoc | Document conversion and format check |
| ANZAGG Validation | Tactile and accessible 3-D print review (manual) |

### Pipelines

Multi-step automated workflows that chain tools together. Each pipeline run logs every step result and overall pass/fail to the database.

Available pipelines:
- **DAISY Pipeline** — DAISY Pipeline 2 task execution
- **Accessible EPUB Pipeline** — Pandoc conversion → EPUBCheck → DAISY Ace
- **Braille Production Pipeline** — Liblouis translation → BRLTTY device check

---

## System Dependencies

The following tools must be installed and on your PATH:

```bash
# DAISY Ace (EPUB accessibility checker)
npm install @daisy/ace -g

# EPUBCheck
brew install epubcheck          # macOS
# or download from https://github.com/w3c/epubcheck/releases

# LibLouis
sudo apt-get install liblouis-bin liblouis-dev    # Ubuntu/Debian
brew install liblouis                             # macOS

# DAISY Pipeline 2
# Download from https://daisy.org/activities/software/pipeline/
```

Verify all tools:
```bash
ace --version
pipeline2 --version
epubcheck --version
lou_translate --version
```

### Configuring Non-Standard Paths (`tools.ini`)

If any tool is installed in a non-standard location, create `tools.ini` in the project root:

```ini
[tools]
ace       = ace
epubcheck = epubcheck
pipeline  = pipeline2
liblouis  = lou_translate

[paths]
extra =
    /opt/daisy-pipeline2/bin
    /usr/local/share/npm/bin
```

Use `tools_service.resolve("ace")` anywhere in the codebase to get the confirmed executable path before invoking a tool.

---

## Installation and Running

### Install Python Dependencies

```bash
uv sync
```

### Run the Application

```bash
uv run python accessibility_mgr/app.py
```

Or use the launcher scripts:

```bash
# Linux / macOS
./accessibility_mgr/run.sh

# Windows
accessibility_mgr\run.bat
```

The application starts a local NiceGUI web server at `http://localhost:8765`.

### Seed Inventory from CSV

Import an initial inventory from a CSV purchase list:

```bash
# Preview without writing
uv run AccessMan-seed inventory.csv --dry-run

# Import, replacing any existing inventory
uv run AccessMan-seed inventory.csv --replace-existing

# Import with filament cost calculation
uv run AccessMan-seed inventory.csv --replace-existing \
    --filament-spool-cost 9.99 --filament-spool-grams 1000 --verify-totals

# Check current totals without importing
uv run AccessMan-seed inventory.csv --verify-only
```

---

## Backups

The application runs an automatic weekly database backup in the background. Backups are stored in `backups/` as `accessibility_manager_<YYYYMMDD_HHMMSS>.db`, with the 10 most recent copies retained. Backup history is logged to the `backup_log` table.

To trigger a manual backup from Python:

```python
from accessibility_mgr.services.backup_service import BackupService
path = BackupService.run_backup(trigger="manual")
```

---

## Admin Settings

The Admin panel manages all configurable lookup data that drives dropdowns throughout the application:

- **Material Categories** — paper types, electronics categories, filament types, diameters, priorities, file use classifications, braille types, tactile methods, LP/eBraille types
- **Metadata Options** — add or remove allowed Dublin Core, eBraille profile, and METS/PREMIS metadata keys; run the typo backfill tool to normalize non-standard keys already in the database
- **Workflow Steps** — add, reorder, activate, or deactivate steps for any job type
- **Printers** — register and manage 3-D printers
- **Embossers** — register and manage braille embossers with paper type assignments

---

## Navigation

| Section | Pages |
|---|---|
| Overview | Dashboard, Search |
| Production | Braille Jobs, Large Print Jobs, eBraille Jobs, EPUB3/DAISY Jobs, Tactile Graphics, 3-D Print Jobs |
| Inventory | Filament, Braille Paper, Electronics |
| Metadata & Files | File Ingestion, Metadata Editor, Lineage Viewer |
| QA & Automation | QA Tooling, Pipelines |
| Admin | Admin Settings |

The **Search** page performs full-text search across job titles, requester names, filenames, and metadata values simultaneously, returning results grouped by type.

The **Lineage Viewer** generates a Mermaid provenance graph showing which files are linked to which jobs, alongside the unified provenance timeline.

---

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | NiceGUI |
| Database | SQLite (WAL mode, foreign keys enforced) |
| Language | Python 3.9+ |
| Package Management | uv |
| Metadata Standards | Dublin Core, METS, PREMIS, eBraille profile |

---

## Repository Structure

```
accessibility_mgr/
├── app.py                    # Application entry point and page registry
├── db/
│   ├── schema.py             # Schema definitions, migrations, directory paths
│   ├── queries.py            # All SQL — parameterized data access layer
│   └── seed_import.py        # CSV inventory seeder
├── ui/
│   ├── dashboard.py          # Studio overview and quick-launch
│   ├── braille_jobs.py       # Braille job CRUD and detail view
│   ├── lp_ebraille.py        # Large print, eBraille, EPUB3/DAISY jobs
│   ├── tactile_graphics.py   # Tactile graphics jobs
│   ├── print_jobs.py         # 3-D print job log
│   ├── inventory_panels.py   # Filament, paper, and electronics inventory
│   ├── ingestion.py          # File ingestion with preservation metadata
│   ├── metadata_editor.py    # Standalone metadata editor for any job
│   ├── metadata_options.py   # Metadata vocabulary catalog
│   ├── lineage.py            # File lineage and provenance graph
│   ├── search.py             # Cross-system full-text search
│   ├── qa.py                 # QA tool execution and history
│   ├── pipelines.py          # Multi-step pipeline orchestration
│   ├── admin.py              # Admin settings panel
│   └── components.py         # Shared UI helpers
├── services/
│   ├── backup_service.py     # Automated weekly database backup
│   ├── pipeline_service.py   # Pipeline definitions and execution
│   ├── qa_service.py         # QA tool registry and execution
│   ├── preservation_service.py # SHA-256 fixity and PREMIS event recording
│   ├── tools_service.py      # External tool path resolution
│   └── execution_service.py  # Subprocess execution wrapper
├── artifacts/                # Primary file store (structured by project)
├── prints_files/             # 3-D print file store
├── job_files/                # Legacy UUID-based file store
└── backups/                  # Automated database backups
```

---

## Documentation

The project documentation is generated with MkDocs:

```bash
uv sync --group docs
uv run mkdocs serve          # preview locally
uv run mkdocs build --strict # build static site
```

Published at: <https://mrhunsaker.github.io/AccessibilityProjectmanagement>

---

## Current Status

Active development. The NiceGUI frontend is the primary interface. All core production workflows, inventory management, file ingestion, metadata editing, QA tooling, and pipeline orchestration are implemented.

Planned additions:
- Authentication and role-based access control
- Reporting and analytics exports
- Batch operations across multiple jobs
- Notification system for due date alerts and SLA tracking
- Enhanced accessibility compliance in the UI itself
