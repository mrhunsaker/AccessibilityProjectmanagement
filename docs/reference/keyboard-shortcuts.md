# Keyboard Shortcuts

---

## Global

| Shortcut | Action | Notes |
|----------|--------|-------|
| `Escape` | Close open dialog | Works in any modal dialog |
| `Ctrl+N` | Open Quick Create dialog | From the Dashboard |

---

## Job List Pages (Braille, LP/eBraille, Tactile, Print)

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | Open New Job dialog |
| `Enter` (in search field) | Execute search / filter |

---

## Search Page

| Shortcut | Action |
|----------|--------|
| `Enter` (in search input) | Execute search |

---

## Dialogs

| Shortcut | Action |
|----------|--------|
| `Enter` | Submit form (in password field on login page) |
| `Escape` | Close dialog |

---

## Notes

- `Ctrl+N` is intentionally guarded with the `Ctrl` modifier so that typing
  the letter **n** in a text field does not accidentally open the create dialog.
  Earlier versions used a bare `N` keydown (FUN-003/FUN-004/FUN-008 fixes).

- Keyboard event handlers are registered with NiceGUI's `ui.keyboard()`.  Each
  handler checks `getattr(e, "ctrlKey", False)` before acting.

- Dialogs capture `Escape` via JavaScript that hides all open Quasar
  `q-dialog` components.
