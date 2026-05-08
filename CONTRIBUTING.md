# Contributing to Braille & Maker Studio

Thank you for taking the time to contribute! This document explains how to get
the project running locally, how to submit changes, and what the review process
looks like.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Workflow](#development-workflow)
3. [Project Structure](#project-structure)
4. [Coding Standards](#coding-standards)
5. [Running Tests](#running-tests)
6. [Submitting a Pull Request](#submitting-a-pull-request)
7. [Reporting Bugs](#reporting-bugs)
8. [Requesting Features](#requesting-features)

---

## Getting Started

### Prerequisites

- Python 3.9 or newer
- [uv](https://github.com/astral-sh/uv) — fast Python package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/youruser/braille-maker-studio.git
cd braille-maker-studio

# Create a virtual environment and install all dependencies (including dev extras)
uv sync --extra dev

# Run the app
uv run braille-studio
# or directly:
uv run python braille_mgr/app.py
```

### Textual live-reload (during UI development)

```bash
uv run textual run --dev braille_mgr/app.py
```

This enables the Textual devtools panel for live CSS editing and event inspection.

---

## Development Workflow

1. **Fork** the repository and create a branch from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```
2. Make your changes, keeping commits small and focused.
3. Run lint and tests before pushing (see below).
4. Open a Pull Request against `main`.

Branch naming conventions:

| Prefix | Use for |
|--------|---------|
| `feat/` | New features |
| `fix/` | Bug fixes |
| `docs/` | Documentation only |
| `refactor/` | Code restructuring without behavior change |
| `chore/` | Tooling, CI, dependency updates |

---

## Project Structure

```
.                          ← repo root (pyproject.toml lives here)
└── braille_mgr/
    ├── app.py             ← Textual TUI entry point
    ├── db/
    │   ├── schema.py      ← SQLite schema & connection helper
    │   └── queries.py     ← Data-access layer (no SQL outside this file)
    ├── ui/                ← Reserved for future panel/screen split-out
    └── prints_files/      ← Auto-created; stores indexed 3-D print files
```

All database logic must go through `db/queries.py`. The TUI panels in `app.py`
call query helpers only — they do not construct SQL strings directly.

---

## Coding Standards

This project uses **Ruff** for linting and formatting. Configuration lives in
`pyproject.toml` under `[tool.ruff]`.

```bash
# Check
uv run ruff check .

# Auto-fix
uv run ruff check . --fix

# Format
uv run ruff format .
```

Type annotations are encouraged for all new public functions. Run mypy with:

```bash
uv run mypy braille_mgr/
```

Key style rules (see also `STYLE.md`):

- Line length: **99 characters**
- Strings: **double quotes**
- Imports: standard library → third-party → local, separated by blank lines
- No bare `except:` — always catch a specific exception type
- All user-visible strings must be plain ASCII or Unicode — no raw escape codes

---

## Running Tests

```bash
uv run pytest
```

Tests live in `tests/`. When adding a new query helper in `db/queries.py`,
please add a corresponding test in `tests/test_queries.py`.

---

## Submitting a Pull Request

1. Ensure `ruff check .` reports no errors.
2. Ensure `pytest` passes.
3. Update `RELEASING.md` under the **Unreleased** section with a short
   description of your change.
4. Fill in the pull request template fully — incomplete PRs may be closed.
5. At least one maintainer approval is required before merging.

---

## Reporting Bugs

Open an issue and include:

- Your operating system and Python version (`python --version`)
- Steps to reproduce
- What you expected to happen vs. what actually happened
- Any traceback or error output (paste as a code block)

---

## Requesting Features

Open an issue with the `enhancement` label. Describe the problem you're trying
to solve rather than jumping straight to a solution — this helps us find the
best approach together.
