# Accessibility Project Management

Accessibility Project Management is a NiceGUI-based production system for accessibility workflows. The documentation is generated with MkDocs and the Python API reference is built from docstrings using mkdocstrings.

## What this documentation covers

- Application startup and UI navigation
- Database schema and query helpers
- Services that coordinate workflow execution and tool discovery
- UI pages, dialogs, and shared components
- Legacy SQLAlchemy data models
- Artifact-based ingestion and file placement conventions
- Metadata governance options and admin tooling
- EPUB3/DAISY production and DAISY pipeline orchestration

## Recent updates

- Ingestion routes source files to `artifacts/<Project Title>/` with structured
  filenames and preservation-aware metadata linkage.
- Metadata entry is constrained to governed option sets, with Dublin Core field
  examples and option popups in editing dialogs.
- EPUB3/DAISY jobs are exposed as a dedicated production workflow.
- DAISY Pipeline is exposed under Pipelines (not QA Tooling).
- Electronics inventory now renders all categories, including empty sections,
  and supports inline creation of new categories from the component dialog.

## Local documentation workflow

1. Install the docs dependencies with `uv sync --group docs`.
2. Preview the site with `uv run mkdocs serve`.
3. Build the static site with `uv run mkdocs build --strict`.

## Published site

The GitHub Actions workflow deploys the site to:

- [https://mrhunsaker.github.io/AccessibilityProjectmanagement](https://mrhunsaker.github.io/AccessibilityProjectmanagement)
