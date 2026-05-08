# Braille & Maker Studio — Project Manager

A terminal-based (TUI) project management and inventory app for a braille /
3-D printing production environment.

---

## Requirements

| Requirement | Version                    |
| ----------- | -------------------------- |
| Python      | 3.11 +                     |
| textual     | auto-installed by launcher |

---

## Quick Start

### Linux / macOS

```bash
chmod +x run.sh
./run.sh
```

### Windows

```
run.bat
```

### Manual (any platform)

```bash
pip install textual
python app.py
```

---

## Navigation

The left sidebar contains six sections. Click or press the button to switch.

| Shortcut | Action                         |
| -------- | ------------------------------ |
| `Q`      | Quit                           |
| `Ctrl+R` | Refresh current table          |
| `↑ ↓`    | Move cursor in tables          |
| `Tab`    | Move between fields in dialogs |
| `Enter`  | Activate focused button        |

---

## Sections

### 🧵 Filament

Tracks 3-D printer filament stock.

| Field    | Description                                                            |
| -------- | ---------------------------------------------------------------------- |
| Brand    | Manufacturer (Bambu, Hatchbox, …)                                      |
| Color    | Color name                                                             |
| Type     | PLA, PETG, ABS, TPU, …                                                 |
| Diameter | 1.75 mm or 2.85 mm                                                     |
| Qty (g)  | Grams remaining — automatically decremented when a print job is logged |

### 📄 Braille Paper

Tracks paper and label supplies.

- **Sheet Feed 11.5×11** — standard braille sheet
- **Sheet Feed 8.5×11**
- **Pin Feed 11.5×11**
- **Pin Feed Labels 8.5×11**
- **Generic Label** — enter size and type (removable, permanent, etc.)

### ⚡ Electronics

Tracks all electronics components.

Categories: TRRS Trinkey / Micro:bit boards, Microswitches, Wire, Mono Jacks,
Bolts/Nuts, Hex Screws, Solder, Other.

Each item stores brand, spec (size/gauge/resistance), quantity, and unit (pcs, m, g, roll, ft).

### 🖨️ 3-D Print Jobs

Logs every print run.

- Choose printer: **BambuLabs P1S** or **Sovol SV08 Max**
- Select filament from inventory (quantity auto-deducted on save)
- Record grams used, success/failure, and failure reason
- Optionally attach a `.3mf` / `.stl` / `.gcode` file — it is copied into the
  `prints_files/` folder and indexed in the database
- Click **📁 Open Files Folder** to browse all indexed print files

### ⠿ Braille Jobs

Tracks braille transcription work.

Types: Literary · Math · Science · Music

Steps (check off as completed):

1. Digitized
2. Formatted
3. Brailled
4. Proofread
5. Delivered

Progress is shown as a visual bar: `███░░ 3/5`

### 🔠 LP / eBraille Jobs

Tracks large print and eBraille production.

Steps:

1. Digitized
2. Formatted
3. eBraille / Converted to Large Print
4. Proofread
5. Delivered

---

## Database

- File: `project_manager.db` (SQLite, created automatically on first run)
- Print files: `prints_files/` folder (created automatically)
- Schema uses `PRAGMA foreign_keys = ON` and `journal_mode = WAL` for safety

### Tables

| Table             | Purpose                                  |
| ----------------- | ---------------------------------------- |
| `filament`        | Filament inventory                       |
| `braille_paper`   | Paper & label supplies                   |
| `electronics`     | Electronics components                   |
| `printer`         | Printer reference (seeded automatically) |
| `print_job`       | 3-D print log                            |
| `braille_job`     | Braille transcription tracking           |
| `lp_ebraille_job` | Large print / eBraille tracking          |

You can query or back up the database with any SQLite tool:

```bash
sqlite3 project_manager.db ".tables"
sqlite3 project_manager.db "SELECT * FROM filament;"
```

---

## File Structure

```
braille_mgr/
├── app.py              ← Main TUI application
├── run.sh              ← Linux/macOS launcher
├── run.bat             ← Windows launcher
├── README.md           ← This file
├── db/
│   ├── __init__.py
│   ├── schema.py       ← DB init & connection
│   └── queries.py      ← All data access functions
└── prints_files/       ← Auto-created; stores indexed print files
```
