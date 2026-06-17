# Configurable Categories

APM stores most dropdown options in the `material_category` table so
administrators can customise them without touching code.  Changes take effect
immediately and apply app-wide.

---

## 📂 Category Sections

| Section key | Used in | Description |
|---|---|---|
| `paper_type` | Braille Paper inventory | Sheet feed, pin feed, label types |
| `elec_cat` | Electronics inventory | Component categories |
| `elec_unit` | Electronics inventory | Quantity units (pcs, m, g …) |
| `braille_type` | Braille jobs | Literary, math, science, music |
| `tactile_type` | Tactile Graphics jobs | Thermoform, hand-tooled, embossed |
| `lp_type` | LP / eBraille / EPUB3 jobs | Large print, eBraille, EPUB3/DAISY |
| `filament_type` | Filament inventory | PLA, PETG, ABS, TPU … |
| `diameter_mm` | Filament inventory | 1.75 mm, 2.85 mm |
| `priority` | All job types | Low, Normal, High, Urgent |
| `file_use` | File objects | ORIGINAL, DERIVATIVE, INTERMEDIATE … |
| `delivery_method` | Delivery dialogs | Physical, Email, LMS, USB, Pickup … |
| `metadata_dublin_core` | Metadata editor | dc:title, dc:creator … |
| `metadata_ebraille_profile` | Metadata editor | grade_level, isbn, transcriber … |
| `metadata_mets_premis` | Metadata editor | mets:file_group, premis:event_type … |
| `braille_format` | File format pickers | BRF, BRL, EBRF, PDF … |
| `print_format` | File format pickers | 3MF, STL, G-Code |

---

## ➕ Adding a Category Value

1. Navigate to **Admin → Material Categories**.
2. Select the target section from the dropdown.
3. Click **+ Add**.
4. Enter a **Display Label** (shown in UI) and **Value** (slug stored in DB).
5. Set a **Sort Order** to control position in dropdowns.
6. Click **Save**.

---

## ✏️ Editing / Deactivating

Click **Deactivate** next to any value to hide it from dropdowns without
deleting history.  The value remains in the database and existing records are
unaffected.  Click **Activate** to restore it.

---

## 🗑️ Deleting

Deleting is implemented as a soft-delete (sets `active = 0`).  Values can be
re-activated at any time.  Physical rows are never removed so that historical
records remain valid.

---

## 🔑 Metadata Key Backfill

If operators have been entering metadata keys manually with typos (e.g.
`dc_title` instead of `dc:title`), use **Backfill Typo Keys**:

1. Go to **Admin → Metadata Options**.
2. Click **Backfill Typo Keys**.
3. A **dry-run preview** dialog shows every proposed rename and the number of
   affected rows.
4. Click **Confirm Backfill** to apply, or **Cancel** to abort.

The backfill uses fuzzy matching (difflib, 80 % similarity threshold) to map
non-approved keys to the closest approved key.  Keys with no good match are
listed as **skipped** and left unchanged.
