# Style Guide

This document describes the coding conventions for Braille & Maker Studio.
Tooling enforces most of these automatically via Ruff — this guide explains
the *why* behind the choices.

---

## Python Version Target

Code must be compatible with **Python 3.9**. Do not use syntax or standard
library APIs introduced in 3.10 or later without a compatibility shim.

Common pitfalls:
- `match` / `case` statements → use `if/elif` chains (3.10+)
- `X | Y` union type hints in signatures → use `Union[X, Y]` or `Optional[X]` (3.10+)
- `tomllib` → not available until 3.11; use `tomli` as a backport if needed

---

## Formatting

- **Line length**: 99 characters (configured in `pyproject.toml`)
- **Indentation**: 4 spaces — no tabs
- **Quotes**: double quotes for all strings
- **Trailing commas**: yes, in multi-line collections and function signatures
- Formatting is handled automatically by `ruff format` — run it before every commit

---

## Imports

Order (enforced by Ruff's `isort` rules):

```python
# 1. Standard library
import os
import sqlite3
from pathlib import Path

# 2. Third-party
from textual.app import App, ComposeResult
from textual.widgets import Button, DataTable

# 3. Local / first-party
from braille_mgr.db import queries as Q
```

- No wildcard imports (`from module import *`)
- Group imports with a blank line between each tier
- Prefer `from x import y` over `import x` when only one or two names are used

---

## Naming

| Kind | Convention | Example |
|------|-----------|---------|
| Module | `snake_case` | `queries.py` |
| Class | `PascalCase` | `FilamentPanel` |
| Function / method | `snake_case` | `refresh_table()` |
| Variable | `snake_case` | `row_id` |
| Constant / config | `UPPER_SNAKE` | `BRAILLE_STEPS` |
| Private helper | leading underscore | `_current_id()` |
| Textual widget ID | `snake_case` string | `"fil_table"` |

---

## Type Annotations

- Annotate **all** public function signatures (parameters and return types).
- Use `from __future__ import annotations` at the top of every module to enable
  postponed evaluation and allow forward references.
- Use `Optional[X]` / `X | None` (Python 3.9 compatible form: `Optional[X]`)
  for nullable values.
- `dict` and `list` builtins are preferred over `Dict`/`List` from `typing`
  for Python 3.9+ (e.g. `list[dict]` is fine).

---

## Database Layer

- **All SQL lives in `db/queries.py`**. No SQL strings outside that module.
- Use parameterized queries (`?` placeholders) at all times — never f-string or
  `.format()` a SQL string with user data.
- Every write function should handle the `updated_at` timestamp via SQL
  (`datetime('now')`) rather than Python-side datetime objects, so the
  timestamp reflects the DB server time consistently.
- Use `PRAGMA foreign_keys = ON` at connection time (already set in `schema.py`).

---

## Textual UI Conventions

- Each major inventory category gets its own `Panel` class (a `Container`
  subclass). Panels own their `DataTable` and all CRUD button handlers.
- Modal dialogs are `ModalScreen` subclasses. They `dismiss(data)` with a dict
  on save and `dismiss(None)` on cancel. The caller decides what to do with
  the result.
- Widget IDs use `snake_case` with a short prefix indicating the panel:
  `fil_table`, `add_fil`, `pap_table`, etc.
- Do not put business logic inside event handlers — delegate to a query
  helper immediately.
- CSS lives in the `APP_CSS` string at the top of `app.py`. Use Textual's
  design token variables (`$primary`, `$surface`, `$text-muted`, etc.) rather
  than hard-coded colors so the app respects user themes.

---

## Error Handling

- Catch specific exceptions, never bare `except:` or `except Exception:` unless
  you re-raise or log explicitly.
- User-facing errors should be shown via the `MsgModal` dialog, not printed to
  stdout.
- Database errors that are unrecoverable should propagate to the top-level app
  handler and display a clear message before exiting.

---

## Documentation

- Every module should have a top-level docstring explaining its purpose.
- Public functions and classes need a one-line docstring at minimum.
- Comments explain *why*, not *what* — the code should be readable enough that
  the *what* is obvious.

---

## Git Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) spec:

```
<type>(<scope>): <short summary>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(db): add deduct_filament helper for auto-decrement on print jobs
fix(ui): prevent crash when no filament rows exist in print job modal
docs: update CONTRIBUTING with uv sync instructions
chore: bump textual to 0.82.0
```

- Subject line: imperative mood, no period, ≤72 characters
- Reference issues with `Closes #123` in the footer
