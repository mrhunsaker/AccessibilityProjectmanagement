# Release Guide

This document describes how to cut a new release of Braille & Maker Studio.

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`):

| Increment | When                                                            |
| --------- | --------------------------------------------------------------- |
| `MAJOR`   | Breaking change to the DB schema, file layout, or CLI interface |
| `MINOR`   | New feature added in a backward-compatible way                  |
| `PATCH`   | Bug fix or documentation update                                 |

The authoritative version lives in **`pyproject.toml`** under `[project] version`.

---

## Release Checklist

### 1. Prepare

- [ ] All changes for this release are merged into `main`
- [ ] `uv run ruff check .` passes with no errors
- [ ] `uv run pytest` passes
- [ ] The **Unreleased** section of this file is complete

### 2. Bump the version

Edit `pyproject.toml`:

```toml
[project]
version = "X.Y.Z"
```

### 3. Update this file

Move the content under **Unreleased** into a new dated section:

```markdown
## [X.Y.Z] — YYYY-MM-DD
```

### 4. Commit and tag

```bash
git add pyproject.toml RELEASING.md
git commit -m "chore: release vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin main --tags
```

### 5. Build and publish (optional — if distributing via PyPI)

```bash
uv build
uv publish
```

`uv build` produces a wheel and sdist in `dist/`. `uv publish` uploads to PyPI
using credentials from `~/.config/uv/credentials.toml` or environment variables
`UV_PUBLISH_USERNAME` / `UV_PUBLISH_PASSWORD`.

### 6. Create a GitHub Release

- Go to **Releases → Draft a new release**
- Select the tag `vX.Y.Z`
- Paste the changelog section for this version into the description
- Attach the built wheel from `dist/` if distributing binaries
- Publish

---

## Database Schema Migrations

Braille & Maker Studio uses plain SQLite with no migration framework. If a
release changes the schema:

1. Document the migration SQL in the release notes under a **Migration** heading.
2. Provide a one-time migration script in `scripts/migrate_X_Y_Z.py` that
   users run manually before launching the new version.
3. Increment the `MAJOR` version.

Example migration note format:

````markdown
### Migration

Run before first launch of vX.Y.Z:

```bash
uv run python scripts/migrate_X_Y_Z.py
```
````

Or manually in sqlite3:

```sql
ALTER TABLE filament ADD COLUMN supplier TEXT;
```

---

## Changelog

All notable changes to this project are documented here.
Format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added

- Initial project scaffold: TUI application with six inventory/workflow panels
- SQLite database with tables for filament, braille paper, electronics,
  printers, print jobs, braille jobs, and LP/eBraille jobs
- BambuLabs P1S and Sovol SV08 Max pre-seeded as printer options
- Automatic filament gram deduction when a print job is logged
- Print file indexing: attached `.3mf`/`.stl` files copied to `prints_files/`
  and recorded in the database
- Progress tracking with visual bar (`███░░ 3/5`) for braille and LP/eBraille jobs
- `run.sh` (Linux/macOS) and `run.bat` (Windows) launcher scripts
- `pyproject.toml` configured for `uv`, `ruff`, `mypy`, and `pytest`

### Changed

- *(nothing yet)*

### Fixed

- *(nothing yet)*

### Removed

- *(nothing yet)*

---

## [2026.5.6] — 2026-05-06

### Added

- Initial project scaffold: TUI application with six inventory/workflow panels
- SQLite database with tables for filament, braille paper, electronics, printers, print jobs, braille jobs, and LP/eBraille jobs
- BambuLabs P1S and Sovol SV08 Max pre-seeded as printer options
- Automatic filament gram deduction when a print job is logged
- Print file indexing: attached .3mf/.stl files copied to prints_files/ and recorded in the database
- Progress tracking with visual bar (#.. 3/5 style) for braille and LP/eBraille jobs
- run.sh (Linux/macOS) and run.bat (Windows) launcher scripts
- pyproject.toml configured for uv, ruff, mypy, and pytest
- Console script entry point: uv run AccessMan
- Dynamic material categories and workflow steps tables for user-extensible options
- Admin panel for managing material categories, workflow steps, and printers

```
