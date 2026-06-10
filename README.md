# Accessibility Project Management

A NiceGUI-based workflow and inventory platform for accessibility production teams.

The application manages production tracking for braille, large print, eBraille, EPUB3/DAISY, tactile graphics, and 3‑D printing workflows. It combines job management, file ingestion, metadata tracking, QA tooling integration, and consumables inventory into a single local web application backed by SQLite.

---

## Current Project Status

This project is currently an **alpha-stage operational prototype**.

The repository contains:

- A working NiceGUI application shell
- Multi-page production workflow interfaces
- SQLite-backed persistence
- File ingestion and metadata management
- Inventory tracking modules
- QA and automation integration points
- Background backup services
- Configurable workflow and metadata administration

Several features are implemented as workflow scaffolding and administrative structure rather than fully automated production pipelines.

---

## What the Application Currently Does

### Production Workflow Tracking

The application provides dedicated workflow pages for:

- Braille jobs
- Large print jobs
- eBraille jobs
# Accessibility Project Manager

A NiceGUI-based local web application for accessibility production teams. It manages braille, large print, eBraille, EPUB3/DAISY, tactile graphics, and 3-D printing workflows, with student records, file ingestion, metadata management, QA tooling, inventory, backups, and an API surface backed by SQLite.

## What the application does

### Production tracking

Dedicated pages track each workflow lifecycle with step completion, reversion, delivery capture, and event logging:

- Braille
- Large Print
- eBraille
- EPUB3 / DAISY
- Tactile Graphics
- 3-D Print

Each job can store Dublin Core, eBraille profile, and METS/PREMIS-aligned metadata, support step-level file attachments, and link to a student record.

### File ingestion and preservation

Files can be ingested from a local path or browser upload. The system computes SHA-256 checksums, stores size and MIME type, copies files into `artifacts/<Project Title>/...`, records file-use classification, and logs PREMIS-style ingest events.

### Search and reports

Search covers job tables, metadata, students, file records, and the event log. A 64-character hex string triggers an exact checksum match. Reports filter by school, grade, type, status, date range, and student, and export as CSV.

### Inventory management

- Filament: brand, colour, type, diameter, quantity, cost per kg, supplier
- Braille paper: paper type, size, label type, quantity, supplier
- Electronics: configurable categories for boards, switches, wire, jacks, and similar components

Low-stock warnings are shown for filament and paper inventory.

### Operations and API

The dashboard includes quick navigation cards, a quick-create launcher, and an upcoming deadlines widget. The REST API is mounted under `/api` and can be protected with `ACCESSMAN_API_AUTH_REQUIRED=1` and `ACCESSMAN_API_KEY=...`.

### QA and automation

The application integrates external tooling such as DAISY Ace, EPUBCheck, Liblouis, BRLTTY, Pandoc, and DAISY Pipeline 2. Runs are stored in the database and can be associated with jobs.

### Provenance and lineage

Significant operations write typed events to `metadata_event`, including create, update, delete, step completion, ingest, metadata update, QA run, delivery, and note entries. The Lineage Viewer shows file-to-job relationships and provenance history.

### Administration

Admin pages manage material categories, workflow steps, printers, embossers, metadata options, backups, and other configuration data.

### Backups

SQLite backups run automatically after startup and on a weekly schedule. Backups are written to `backups/accessibility_manager_YYYYMMDD_HHMMSS.db` and the most recent entries are kept by the retention policy.

## Application architecture

The app runs locally on `http://localhost:8765`. Database location is configurable with `ACCESSMAN_DB_PATH`; if unset, a user-data-directory default is used.

| Layer | Technology |
|---|---|
| UI framework | NiceGUI |
| Database | SQLite with WAL journaling |
| Language | Python 3.9+ |
| Package manager | uv |

## Repository structure

```text
accessibility_mgr/
├── app.py
├── api/
├── db/
├── services/
└── ui/
```

Runtime storage directories created by the application include:

```text
artifacts/
job_files/
prints_files/
backups/
```

## Installation

```bash
uv sync
uv run AccessMan
```

Or directly:

```bash
uv run python accessibility_mgr/app.py
```

## External tool configuration

Copy `tools.ini.example` to `tools.ini` at the project root to configure custom paths or add extra `PATH` directories.

## License

MIT License
The Lineage Viewer renders a Mermaid graph of file-to-job relationships across all production types, and displays the full provenance timeline.
