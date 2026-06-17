# Printers & Embossers

APM ships with seed data for three embossers and two 3-D printers.  Add,
edit, or delete devices under **Admin → Printers** and **Admin → Embossers**.

---

## 🖨️ 3-D Printers

### Seed Devices

| Name | Model |
|------|-------|
| BambuLabs P1S | P1S |
| Sovol SV08 Max | SV08 Max |

### Adding a Printer

1. Go to **Admin → Printers**.
2. Click **+ Add Printer**.
3. Enter **Printer Name** (required, must be unique) and optional **Model** and **Notes**.
4. Click **Save**.

Printers are referenced by print jobs.  A printer **cannot be deleted** while
it has associated print jobs — remove or reassign those jobs first.

---

## 🖊️ Embossers

### Seed Devices

| Name | Model | Paper Feed |
|------|-------|-----------|
| Index-D V5 Embosser | Index-D V5 | Pin Feed 11.5×11 |
| ViewPlus Columbia Embosser | Columbia | Pin Feed 11.5×11 |
| ViewPlus Delta Embosser | Delta | Sheet Feed 11.5×11 |

### Adding an Embosser

1. Go to **Admin → Embossers**.
2. Click **+ Add Embosser**.
3. Enter **Name** (required, unique), **Model**, **Paper Feed Type**, and **Notes**.
4. Click **Save**.

The **Paper Feed Type** dropdown is populated from the `paper_type` material
category.  Add new paper types under **Admin → Material Categories → Paper Types**
before creating an embosser that uses them.

---

## ✏️ Editing Devices

Click **Edit** next to any device to open the edit dialog.  All fields can be
changed.  The device name must remain unique within its table.

---

## 🗑️ Deleting Devices

Click **✕** next to a device.  A confirmation dialog is shown.

- **Embossers**: Cannot be deleted if referenced by braille jobs.  Unassign
  the embosser from those jobs first, or leave the embosser and deactivate the
  jobs instead.
- **Printers**: Cannot be deleted while print jobs reference them.

---

## 🔗 Linking to Jobs

When creating or editing a **Braille Job**, the embosser selector is populated
from the embossers table.  When creating a **3-D Print Job**, the printer
selector shows all configured printers.
