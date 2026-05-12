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

## Core Features

## Dashboard

The dashboard provides operational visibility across the studio:

- Active braille jobs
- Large print, eBraille, tactile graphics, and 3D print jobs
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

Category behavior:

- All configured electronics categories are shown on the page, even when empty.
- Empty category sections display a "No components in this category." message.
- In Add/Edit Component dialogs, selecting `EMPTY` prompts for a required new
  category name.
- Newly entered categories are written to the `material_category` table and are
  immediately available in the UI.

Examples include:

- Microcontrollers
- TRRS components
- Wiring
- Switches
- Fasteners
- Solder
- Connectors

---

## Production Workflow Tracking

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

## Large Print / eBraille Jobs

Tracks large-print and electronic braille production.

Also includes an `EPUB3 / DAISY` workflow type for accessible digital delivery.

Workflow stages:

1. Digitized
2. Formatted
3. Converted
4. Proofread
5. Delivered

---

## Tactile Graphics Jobs

Tracks tactile graphics production.

Methods:

- Thermoform / SWELL
- Hand Tooled
- Embossed Figures

Workflow stages:

1. Designed
2. Created
3. Proofread
4. Delivered

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

## Technology Stack

| Component          | Technology  |
| ------------------ | ----------- |
| Frontend           | NiceGUI     |
| Original UI        | Textual     |
| Database           | SQLite      |
| Language           | Python 3.9+ |
| Package Management | uv          |

---

## Running the Application

## Recent Workflow and Metadata Updates

- File ingestion now copies assets into `artifacts/<Project Title>/` with
  structured naming based on project/student/school/grade/subject metadata.
- Ingested file records are linked to the artifact path in the database for
  centralized file traceability.
- Metadata entry uses governed option sets (including Dublin Core and
  eBraille-profile fields), with helper examples and option popups in UI forms.
- Admin includes metadata option management and typo-key backfill tooling.
- `EPUB3 / DAISY Jobs` is available as a first-class production page.
- `DAISY Pipeline` is classified under Pipelines instead of QA Tooling.

## System Dependencies

The application requires the following system tools to be installed and available on your PATH:

### Ace (Accessibility Checker for EPUB)

Install via npm:

```bash
npm install @daisy/ace -g
```

### DAISY Pipeline

Download and install from [DAISY Pipeline](https://daisy.org/activities/software/pipeline/) or install via package manager.

### EPUBCheck

Download from [EPUBCheck releases](https://github.com/w3c/epubcheck/releases) or install via package manager.

For macOS or Linux (via Homebrew):

```bash
brew install epubcheck
```

### LibLouis

Install the Braille translation library.

For Ubuntu/Debian:

```bash
sudo apt-get install liblouis-bin liblouis-dev
```

For macOS (via Homebrew):

```bash
brew install liblouis
```

Verify all tools are on your PATH:

```bash
ace --version
pipeline2 --version
epubcheck --version
lou_translate --version
```

---

## Configuring Tool Paths (`tools.ini`)

If any of the tools above are installed with non-standard executable names or
in directories not on your login PATH (common with GUI app launchers), create or
edit `tools.ini` in the project root.

The file is created automatically with defaults on first use. To customise:

```ini
[tools]
# Set to the exact executable name or a full absolute path
ace       = ace             # or /usr/local/bin/ace
epubcheck = epubcheck       # or /opt/epubcheck/bin/epubcheck
pipeline  = pipeline2       # DAISY Pipeline 2 CLI is usually "pipeline2"
liblouis  = lou_translate   # or file2brl, lou_checktable, etc.

[paths]
# Directories to prepend to PATH at startup (one per line, indent continuations)
extra =
    /opt/daisy-pipeline2/bin
    /usr/local/share/npm/bin
```

At startup the app:

1. Reads `tools.ini`.
2. Prepends every directory listed under `[paths] extra` to `PATH`.
3. Resolves each tool via `shutil.which()` (after the PATH update) or directly
   if an absolute path is given.
4. Logs a warning for any tool that cannot be found (the app still starts).

Use `tools_service.resolve("ace")` / `resolve("epubcheck")` /
`resolve("pipeline")` / `resolve("liblouis")` anywhere in the codebase to
get the confirmed absolute path for a tool before invoking it.

---

## Install Python Dependencies

```bash
uv sync
```

### Optional: Run a docstring quality pass

The project follows NumPy-style docstring conventions for modules, classes,
and functions. If you are validating docstrings locally, run your preferred
linting/checking tools after dependency sync.

---

## Run the NiceGUI Frontend

```bash
uv run python accessibility_mgr/app.py
```

## Seed Inventory From CSV

Use the seed importer to load a large initial inventory/purchase list from CSV.

```bash
uv run AccessMan-seed Purchase_Needs_Adaptive_Switches_with_inventory.csv --dry-run
uv run AccessMan-seed Purchase_Needs_Adaptive_Switches_with_inventory.csv --replace-existing
uv run AccessMan-seed Purchase_Needs_Adaptive_Switches_with_inventory.csv --replace-existing --filament-spool-cost 9.99 --filament-spool-grams 1000 --verify-totals
uv run AccessMan-seed Purchase_Needs_Adaptive_Switches_with_inventory.csv --verify-only
```

Notes:

- `--dry-run` parses and reports counts without writing data.
- `--replace-existing` clears `electronics`, `filament`, and `braille_paper` before import.
- Filament spool counts are converted to grams using `--filament-spool-grams` (default `1000`).
- Use `--filament-spool-cost` to set a default spool price and auto-calculate `cost_per_kg`.
- Use `--verify-totals` to print post-import table totals.
- Use `--verify-only` to print totals without importing.

The application launches a local NiceGUI web server.

---

## Documentation Site

The project documentation is generated with MkDocs and published to:

<https://mrhunsaker.github.io/AccessibilityProjectmanagement>

To preview or build the documentation locally:

```bash
uv sync --group docs
uv run mkdocs serve
uv run mkdocs build --strict
```

The published site pulls its API reference from the docstrings in the Python
modules under `accessibility_mgr/`.

---

## Database

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

## Repository Structure

```text
accessibility_mgr/
├── app.py                # NiceGUI frontend entrypoint
├── db/
│   ├── database.py       # Database initialization
│   ├── queries.py        # Data access layer
│   └── schema.py         # Schema definitions
├── ui/
│   ├── dashboard.py
│   ├── inventory_panels.py
│   ├── categories.py
│   ├── print_jobs.py
│   ├── braille_jobs.py
│   ├── lp_ebraille.py
│   ├── pipelines.py
│   ├── qa.py
│   └── metadata_editor.py
├── services/
│   ├── pipeline_service.py
│   ├── qa_service.py
│   └── tools_service.py
├── job_files/
├── artifacts/
└── prints_files/
```

---

## Current Status

The NiceGUI frontend is under active development and is replacing the original
terminal interface incrementally.

Current priorities:

- Complete migration of TUI workflows into NiceGUI
- Expand CRUD interfaces
- Improve accessibility compliance
- Add reporting and analytics
- Add authentication and multi-user support

---

## Accessibility Goals

This project is designed for accessibility-focused production environments and
prioritizes:

- Keyboard accessibility
- High-contrast interfaces
- Screen-reader compatibility
- Efficient operator workflows
- Reduced operational friction for adaptive production teams
