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
- EPUB3 / DAISY jobs
- Tactile graphics jobs
- 3‑D print jobs
- Student production history

Each workflow type is tracked independently through configurable production stages.

### Inventory Management

The system includes inventory management for:

- 3‑D printer filament
- Braille paper and media stock
- Electronics and accessibility hardware components

### File Ingestion and Metadata

The application supports:

- Structured file ingestion
- Persistent file path tracking
- SHA‑256 checksum generation
- Metadata editing
- File/job linkage
- Provenance and lineage visualization

### QA and Automation

The platform includes interfaces and execution hooks for external accessibility tooling including:

- DAISY Ace
- EPUBCheck
- Liblouis
- BRLTTY
- Pandoc
- DAISY Pipeline 2

Pipeline execution history and QA runs are stored in the database.

### Administration

Administrative pages allow configuration of:

- Workflow steps
- Metadata vocabularies
- Material categories
- Printers and embossers
- Backup management

---

## Application Architecture

### Frontend

- NiceGUI
- Component-driven page modules
- Sidebar navigation grouped by workflow domain

### Backend

- Python 3.9+
- SQLite database
- SQLAlchemy

### Services

Implemented services include:

- Database initialization
- Tool path resolution
- Automated backup scheduling
- Inventory seeding/import utilities

---

## Implemented Navigation Structure

### Overview

- Dashboard
- Search
- Reports

### Production

- Students
- Braille Jobs
- Large Print Jobs
- eBraille Jobs
- EPUB3 / DAISY Jobs
- Tactile Graphics
- 3‑D Print Jobs

### Inventory

- Filament
- Braille Paper
- Electronics

### Metadata & Files

- File Ingestion
- Metadata Editor
- Lineage Viewer

### QA & Automation

- QA Tooling
- Pipelines

### Admin

- Admin Settings

---

## Repository Structure

```text
accessibility_mgr/
├── app.py                  # NiceGUI application entry point
├── db/                     # Database schema and persistence
├── services/               # Backup, tools, and utility services
├── ui/                     # Page modules and interface logic
└── resources/              # Static resources and icons
```

Runtime storage directories created by the application include:

```text
artifacts/
prints_files/
job_files/
backups/
```

---

## Installation

### Install Dependencies

```bash
uv sync
```

### Run the Application

```bash
uv run python accessibility_mgr/app.py
```

Or:

```bash
uv run AccessMan
```

The application runs locally on:

```text
http://localhost:8765
```

---

## Optional External Tooling

Some QA and pipeline functionality depends on external utilities being installed separately.

Supported integrations currently include:

- DAISY Ace
- EPUBCheck
- Liblouis
- BRLTTY
- Pandoc
- DAISY Pipeline 2

Tool paths can be configured through `tools.ini`.

---

## Database

The application uses SQLite with WAL journaling enabled.

Core persisted domains include:

- Jobs
- Files
- Metadata
- Event history
- Inventory
- Workflow definitions
- QA runs
- Pipeline runs
- Backup logs

---

## Development Notes

Current implementation emphasis is on:

- Operational workflow organization
- Traceability and audit history
- Accessibility production recordkeeping
- Preservation-oriented file handling
- Local-first deployment

The codebase is organized around modular NiceGUI pages and service-layer utilities.

---

## License

MIT License
