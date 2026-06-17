# Local Development Setup

---

## Prerequisites

- Python ≥ 3.12
- [uv](https://docs.astral.sh/uv/) (package manager)
- Git

---

## 1. Clone & Install

```bash
git clone https://github.com/mrhunsaker/AccessibilityProjectManagement.git
cd AccessibilityProjectManagement
uv sync
```

---

## 2. Minimal `.secrets`

For local development with authentication disabled:

```ini
STORAGE_SECRET=dev-only-insecure-secret-change-me
ACCESSMAN_UNPROTECTED=1
ACCESSMAN_DEV=1
```

> **Never** use `ACCESSMAN_UNPROTECTED=1` in a shared or production environment.

---

## 3. Run the App

```bash
uv run AccessMan
```

Open [http://localhost:8765](http://localhost:8765).

---

## 4. External Tool Paths (optional)

Copy and edit the tool configuration:

```bash
cp tools.ini.example tools.ini
```

Edit `tools.ini` to point to installed accessibility tools (DAISY Ace,
EPUBCheck, LibLouis, etc.).  APM works without them — QA tools will report
"not on PATH" warnings instead of failing.

---

## 5. Database Location

The development database is created at:

```
~/.local/share/accessibility_mgr/accessibility_manager.db
```

Override with `ACCESSMAN_DB_PATH` in `.secrets` to use a project-local path:

```ini
ACCESSMAN_DB_PATH=./dev.db
```

---

## 6. Seed Inventory Data (optional)

If you have a CSV export of existing inventory, import it:

```bash
uv run python -m accessibility_mgr.db.seed_import path/to/inventory.csv --dry-run
uv run python -m accessibility_mgr.db.seed_import path/to/inventory.csv
```

---

## 7. Running Without uv

```bash
pip install -e .
AccessMan
```
