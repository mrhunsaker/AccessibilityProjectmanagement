# Accessibility Project Manager

Accessibility Project Manager is a Python-based production management system
for accessibility-focused maker and transcription workflows.

The application combines:

- Braille production tracking
- Large print and eBraille workflow management
- 3-D print job management
- Inventory and materials tracking
- SQLite-backed operational records
- NiceGUI web frontend

The project originally started as a Textual TUI application and is now being
migrated into a modular NiceGUI interface while preserving the original
workflow model.

---

# Core Features

## Dashboard

The dashboard provides operational visibility across the studio:

- Active braille jobs
- LP/eBraille jobs
- Recent print jobs
- Inventory alerts
- Low filament warnings
- Urgent production items
- Workflow completion status

---

## Inventory Management

Tracks production materials and consumables.

### Filament

Tracks 3-D printer filament inventory.

Supported metadata includes:

- Brand
- Color
- Filament type
- Diameter
- Remaining grams

Filament quantities are automatically decremented when print jobs are logged.

### Braille Paper

Tracks:

- Sheet feed paper
- Pin feed paper
- Label stock
- Specialty braille media

### Electronics

Tracks electronics and assembly components used in accessibility hardware
projects.

Examples include:

- Microcontrollers
- TRRS components
- Wiring
- Switches
- Fasteners
- Solder
- Connectors

---

# Production Workflow Tracking

## Braille Jobs

Tracks multi-stage braille production workflows.

Workflow stages:

1. Digitized
2. Formatted
3. Brailled
4. Proofread
5. Delivered

Supports:

- Job priorities
- Progress tracking
- Workflow completion metrics
- Job categorization

Supported categories include:

- Literary
- Math
- Science
- Music

---

## LP / eBraille Jobs

Tracks large-print and electronic braille production.

Workflow stages:

1. Digitized
2. Formatted
3. Converted
4. Proofread
5. Delivered

---

## 3-D Print Jobs

Tracks fabrication and printer usage.

Features include:

- Printer selection
- Filament usage logging
- Success/failure tracking
- Failure reason tracking
- Linked print files
- Print history

Supported print file types:

- `.3mf`
- `.stl`
- `.gcode`

Print assets are stored in the `prints_files/` directory.

---

# Technology Stack

| Component | Technology |
|---|---|
| Frontend | NiceGUI |
| Original UI | Textual |
| Database | SQLite |
| Language | Python 3.9+ |
| Package Management | uv |

---

# Running the Application

## Install Dependencies

```bash
uv sync
```

---

## Run the NiceGUI Frontend

```bash
uv run python accessibility_mgr/app.py
```

The application launches a local NiceGUI web server.

---

# Database

The application automatically initializes a SQLite database on startup.

Default database:

```text
project_manager.db
```

The database uses:

- WAL journaling
- Foreign key enforcement
- Structured relational tables

---

# Repository Structure

```text
accessibility_mgr/
├── app.py                # NiceGUI frontend entrypoint
├── appTUI.py             # Original Textual TUI application
├── db/
│   ├── database.py       # Database initialization
│   ├── queries.py        # Data access layer
│   └── schema.py         # Schema definitions
├── ui/
│   ├── dashboard.py
│   ├── inventory.py
│   ├── categories.py
│   ├── print_jobs.py
│   ├── braille_jobs.py
│   ├── lp_jobs.py
│   └── transactions.py
└── prints_files/
```

---

# Current Status

The NiceGUI frontend is under active development and is replacing the original
terminal interface incrementally.

Current priorities:

- Complete migration of TUI workflows into NiceGUI
- Expand CRUD interfaces
- Improve accessibility compliance
- Add reporting and analytics
- Add authentication and multi-user support

---

# Accessibility Goals

This project is designed for accessibility-focused production environments and
prioritizes:

- Keyboard accessibility
- High-contrast interfaces
- Screen-reader compatibility
- Efficient operator workflows
- Reduced operational friction for adaptive production teams
