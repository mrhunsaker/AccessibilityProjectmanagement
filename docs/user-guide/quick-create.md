# Quick Create

The **Quick Create** button on the Dashboard lets you create any job type with
the minimum required fields, then navigate directly to that job type's page.

---

## 🖱️ Opening Quick Create

- Click the floating **+** (add) button in the bottom-right corner of the
  Dashboard.
- Or press `Ctrl+N` anywhere on the Dashboard.

---

## 📋 Fields

| Field | Required | Notes |
|-------|----------|-------|
| Job Type | Yes | Braille, Large Print, eBraille, EPUB3/DAISY, Tactile, 3-D Print |
| Title | Yes | Used as the job name; 3-D Print uses this as object name |
| Requester | No | Pre-filled in the full job form if provided |

---

## 🚀 What Happens After Save

APM creates the job with sensible defaults:

| Job type | Defaults applied |
|----------|-----------------|
| Braille | `braille_type = literary`, `priority = normal` |
| Large Print / eBraille / EPUB3 | `job_type` set to selection, `priority = normal` |
| Tactile | `tactile_type = thermoform_swell`, `priority = normal` |
| 3-D Print | Uses first configured printer; `filament_used_g = 0` |

After creation, APM navigates to the appropriate job list page so you can
open the new job and fill in full details.

---

## ⚠️ 3-D Print Requirements

Quick Create for 3-D Print requires at least one printer to be configured
(**Admin → Printers**).  If no printers exist, an error notification appears.

---

## ✏️ Editing After Creation

All fields set by Quick Create can be changed by opening the job and clicking
**Edit**.  The quick create form intentionally omits student linking, due
dates, embosser selection, and metadata — add these in the full edit dialog.
