"""
Accessible Materials Project Manager TUI
Built with Textual (https://textual.textualize.io)
"""
from __future__ import annotations
import sys
from pathlib import Path

# Allow running as `python app.py` from anywhere
sys.path.insert(0, str(Path(__file__).parent))

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Button, DataTable, Footer, Header, Input, Label,
    Select, Static, TabbedContent, TabPane, Checkbox, Rule,
)
from textual.reactive import reactive
from textual import on, events

import db as DB

# ── Palette / CSS ─────────────────────────────────────────────────────────────
APP_CSS = """
Screen {
    background: $surface;
}

Header {
    background: $primary-darken-2;
    color: $text;
}

Footer {
    background: $primary-darken-3;
}

/* Sidebar nav */
#sidebar {
    width: 22;
    background: $panel;
    border-right: solid $primary-darken-1;
    padding: 1 1;
}

#sidebar Button {
    width: 100%;
    margin-bottom: 1;
    background: $primary-darken-1;
    color: $text;
    border: none;
}

#sidebar Button:hover, #sidebar Button.-active {
    background: $primary;
}

#content {
    width: 1fr;
    padding: 1 2;
}

/* Modal dialogs */
ModalScreen {
    align: center middle;
}

#dialog {
    background: $surface;
    border: thick $primary;
    padding: 1 2;
    width: 70;
    max-height: 90%;
}

#dialog Label {
    margin-top: 1;
    color: $text-muted;
}

#dialog Input, #dialog Select {
    margin-bottom: 1;
}

#dialog-buttons {
    margin-top: 1;
    height: 3;
}

#dialog-buttons Button {
    margin-right: 1;
}

/* Tables */
DataTable {
    height: 1fr;
}

/* Step checkboxes */
.step-row {
    height: 3;
    margin-bottom: 0;
}

.section-title {
    color: $accent;
    text-style: bold;
    margin-top: 1;
    margin-bottom: 0;
}

.info-label {
    color: $text-muted;
    margin-right: 1;
}

.badge-ok {
    color: $success;
}

.badge-fail {
    color: $error;
}
"""

# ────────────────────────────────────────────────────────────────────────────────
#  Re-usable helper modals
# ────────────────────────────────────────────────────────────────────────────────

class ConfirmModal(ModalScreen):
    """Simple yes/no confirmation."""
    def __init__(self, message: str):
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label(self._message)
            with Horizontal(id="dialog-buttons"):
                yield Button("Yes — Delete", variant="error", id="yes")
                yield Button("Cancel", id="cancel")

    @on(Button.Pressed, "#yes")
    def confirm(self):
        self.dismiss(True)

    @on(Button.Pressed, "#cancel")
    def cancel(self):
        self.dismiss(False)


class MsgModal(ModalScreen):
    """One-line informational popup."""
    def __init__(self, message: str):
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label(self._message)
            yield Button("OK", variant="primary", id="ok")

    @on(Button.Pressed, "#ok")
    def close(self):
        self.dismiss()


# ────────────────────────────────────────────────────────────────────────────────
#  Filament
# ────────────────────────────────────────────────────────────────────────────────

class FilamentModal(ModalScreen):
    def __init__(self, row: dict | None = None):
        super().__init__()
        self._row = row or {}

    def compose(self) -> ComposeResult:
        r = self._row
        with Container(id="dialog"):
            yield Label("── Filament ─────────────────────────────")
            yield Label("Brand")
            yield Input(r.get("brand",""), id="brand", placeholder="e.g. Bambu, Hatchbox")
            yield Label("Color")
            yield Input(r.get("color",""), id="color", placeholder="e.g. Galaxy Black")
            yield Label("Type (PLA, PETG, ABS, TPU…)")
            yield Input(r.get("filament_type",""), id="ftype", placeholder="PLA")
            yield Label("Diameter mm")
            yield Input(str(r.get("diameter_mm","1.75")), id="diam", placeholder="1.75")
            yield Label("Quantity (g)")
            yield Input(str(r.get("quantity_g","0")), id="qty", placeholder="1000")
            yield Label("Notes")
            yield Input(r.get("notes",""), id="notes")
            with Horizontal(id="dialog-buttons"):
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", id="cancel")

    @on(Button.Pressed, "#save")
    def save(self):
        try:
            data = dict(
                brand=self.query_one("#brand", Input).value.strip(),
                color=self.query_one("#color", Input).value.strip(),
                filament_type=self.query_one("#ftype", Input).value.strip(),
                diameter_mm=float(self.query_one("#diam", Input).value or 1.75),
                quantity_g=float(self.query_one("#qty", Input).value or 0),
                notes=self.query_one("#notes", Input).value.strip(),
            )
            if not data["brand"] or not data["color"]:
                self.app.push_screen(MsgModal("Brand and Color are required."))
                return
            self.dismiss(data)
        except ValueError:
            self.app.push_screen(MsgModal("Invalid number in Diameter or Quantity."))

    @on(Button.Pressed, "#cancel")
    def cancel(self): self.dismiss(None)


class FilamentPanel(Container):
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("+ Add", id="add_fil", variant="success")
            yield Button("✎ Edit", id="edit_fil")
            yield Button("✕ Delete", id="del_fil", variant="error")
        yield DataTable(id="fil_table", zebra_stripes=True, cursor_type="row")

    def on_mount(self):
        t = self.query_one("#fil_table", DataTable)
        t.add_columns("ID", "Brand", "Color", "Type", "⌀mm", "Qty (g)", "Notes")
        self.refresh_table()

    def refresh_table(self):
        t = self.query_one("#fil_table", DataTable)
        t.clear()
        for r in DB.list_filaments():
            t.add_row(r["id"], r["brand"], r["color"], r["filament_type"],
                      r["diameter_mm"], r["quantity_g"], r.get("notes",""),
                      key=str(r["id"]))

    def _current_id(self):
        t = self.query_one("#fil_table", DataTable)
        if t.cursor_row < 0: return None
        row = t.get_row_at(t.cursor_row)
        return row[0] if row else None

    @on(Button.Pressed, "#add_fil")
    def add(self):
        def cb(data):
            if data: DB.add_filament(**data); self.refresh_table()
        self.app.push_screen(FilamentModal(), cb)

    @on(Button.Pressed, "#edit_fil")
    def edit(self):
        rid = self._current_id()
        if rid is None:
            self.app.push_screen(MsgModal("Select a row first.")); return
        rows = [r for r in DB.list_filaments() if r["id"] == rid]
        if not rows: return
        def cb(data):
            if data: DB.update_filament(rid, **data); self.refresh_table()
        self.app.push_screen(FilamentModal(rows[0]), cb)

    @on(Button.Pressed, "#del_fil")
    def delete(self):
        rid = self._current_id()
        if rid is None:
            self.app.push_screen(MsgModal("Select a row first.")); return
        def cb(ok):
            if ok: DB.delete_filament(rid); self.refresh_table()
        self.app.push_screen(ConfirmModal(f"Delete filament #{rid}?"), cb)


# ────────────────────────────────────────────────────────────────────────────────
#  Braille Paper
# ────────────────────────────────────────────────────────────────────────────────

PAPER_TYPES = [
    ("Sheet Feed 11.5×11", "sheet_feed_11.5x11"),
    ("Sheet Feed 8.5×11",  "sheet_feed_8.5x11"),
    ("Pin Feed 11.5×11",   "pin_feed_11.5x11"),
    ("Pin Feed Labels 8.5×11", "pin_feed_labels_8.5x11"),
    ("Generic Label",      "generic_label"),
]

class PaperModal(ModalScreen):
    def __init__(self, row: dict | None = None):
        super().__init__()
        self._row = row or {}

    def compose(self) -> ComposeResult:
        r = self._row
        opts = [(label, val) for label, val in PAPER_TYPES]
        cur = r.get("paper_type", PAPER_TYPES[0][1])
        with Container(id="dialog"):
            yield Label("── Braille Paper ────────────────────────")
            yield Label("Paper Type")
            yield Select(opts, value=cur, id="ptype")
            yield Label("Size (for generic labels, e.g. 4x2)")
            yield Input(r.get("size",""), id="size", placeholder="optional")
            yield Label("Label Type (e.g. removable, permanent)")
            yield Input(r.get("label_type",""), id="ltype", placeholder="optional")
            yield Label("Quantity (sheets / rolls)")
            yield Input(str(r.get("quantity","0")), id="qty")
            yield Label("Notes")
            yield Input(r.get("notes",""), id="notes")
            with Horizontal(id="dialog-buttons"):
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", id="cancel")

    @on(Button.Pressed, "#save")
    def save(self):
        try:
            data = dict(
                paper_type=self.query_one("#ptype", Select).value,
                size=self.query_one("#size", Input).value.strip() or None,
                label_type=self.query_one("#ltype", Input).value.strip() or None,
                quantity=int(self.query_one("#qty", Input).value or 0),
                notes=self.query_one("#notes", Input).value.strip(),
            )
            self.dismiss(data)
        except ValueError:
            self.app.push_screen(MsgModal("Quantity must be a whole number."))

    @on(Button.Pressed, "#cancel")
    def cancel(self): self.dismiss(None)


class PaperPanel(Container):
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("+ Add", id="add_pap", variant="success")
            yield Button("✎ Edit", id="edit_pap")
            yield Button("✕ Delete", id="del_pap", variant="error")
        yield DataTable(id="pap_table", zebra_stripes=True, cursor_type="row")

    def on_mount(self):
        t = self.query_one("#pap_table", DataTable)
        t.add_columns("ID","Type","Size","Label Type","Qty","Notes")
        self.refresh_table()

    def refresh_table(self):
        t = self.query_one("#pap_table", DataTable)
        t.clear()
        for r in DB.list_paper():
            t.add_row(r["id"], r["paper_type"], r.get("size","—"),
                      r.get("label_type","—"), r["quantity"], r.get("notes",""),
                      key=str(r["id"]))

    def _current_id(self):
        t = self.query_one("#pap_table", DataTable)
        if t.cursor_row < 0: return None
        row = t.get_row_at(t.cursor_row)
        return row[0] if row else None

    @on(Button.Pressed, "#add_pap")
    def add(self):
        def cb(data):
            if data: DB.add_paper(**data); self.refresh_table()
        self.app.push_screen(PaperModal(), cb)

    @on(Button.Pressed, "#edit_pap")
    def edit(self):
        rid = self._current_id()
        if rid is None:
            self.app.push_screen(MsgModal("Select a row first.")); return
        rows = [r for r in DB.list_paper() if r["id"] == rid]
        if not rows: return
        def cb(data):
            if data: DB.update_paper(rid, **data); self.refresh_table()
        self.app.push_screen(PaperModal(rows[0]), cb)

    @on(Button.Pressed, "#del_pap")
    def delete(self):
        rid = self._current_id()
        if rid is None:
            self.app.push_screen(MsgModal("Select a row first.")); return
        def cb(ok):
            if ok: DB.delete_paper(rid); self.refresh_table()
        self.app.push_screen(ConfirmModal(f"Delete paper supply #{rid}?"), cb)


# ────────────────────────────────────────────────────────────────────────────────
#  Electronics
# ────────────────────────────────────────────────────────────────────────────────

ELEC_CATS = [
    ("TRRS Trinkey / Micro:bit Board", "board"),
    ("Microswitch",                    "microswitch"),
    ("Wire",                           "wire"),
    ("Mono Jack",                      "mono_jack"),
    ("Bolt / Nut",                     "bolt_nut"),
    ("Hex Screw",                      "hex_screw"),
    ("Solder",                         "solder"),
    ("Other",                          "other"),
]
ELEC_UNITS = [("pcs","pcs"),("m","m"),("g","g"),("roll","roll"),("ft","ft")]


class ElecModal(ModalScreen):
    def __init__(self, row: dict | None = None):
        super().__init__()
        self._row = row or {}

    def compose(self) -> ComposeResult:
        r = self._row
        with Container(id="dialog"):
            yield Label("── Electronics Supply ───────────────────")
            yield Label("Category")
            yield Select(ELEC_CATS, value=r.get("category","board"), id="cat")
            yield Label("Name / Description")
            yield Input(r.get("name",""), id="name", placeholder="e.g. TRRS Trinkey NeoPixel")
            yield Label("Brand")
            yield Input(r.get("brand",""), id="brand", placeholder="optional")
            yield Label("Spec (size, gauge, ohms…)")
            yield Input(r.get("spec",""), id="spec", placeholder="optional")
            yield Label("Quantity")
            yield Input(str(r.get("quantity","0")), id="qty")
            yield Label("Unit")
            yield Select(ELEC_UNITS, value=r.get("unit","pcs"), id="unit")
            yield Label("Notes")
            yield Input(r.get("notes",""), id="notes")
            with Horizontal(id="dialog-buttons"):
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", id="cancel")

    @on(Button.Pressed, "#save")
    def save(self):
        try:
            data = dict(
                category=self.query_one("#cat", Select).value,
                name=self.query_one("#name", Input).value.strip(),
                brand=self.query_one("#brand", Input).value.strip() or None,
                spec=self.query_one("#spec", Input).value.strip() or None,
                quantity=float(self.query_one("#qty", Input).value or 0),
                unit=self.query_one("#unit", Select).value,
                notes=self.query_one("#notes", Input).value.strip(),
            )
            if not data["name"]:
                self.app.push_screen(MsgModal("Name is required.")); return
            self.dismiss(data)
        except ValueError:
            self.app.push_screen(MsgModal("Quantity must be a number."))

    @on(Button.Pressed, "#cancel")
    def cancel(self): self.dismiss(None)


class ElecPanel(Container):
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("+ Add", id="add_elec", variant="success")
            yield Button("✎ Edit", id="edit_elec")
            yield Button("✕ Delete", id="del_elec", variant="error")
        yield DataTable(id="elec_table", zebra_stripes=True, cursor_type="row")

    def on_mount(self):
        t = self.query_one("#elec_table", DataTable)
        t.add_columns("ID","Category","Name","Brand","Spec","Qty","Unit","Notes")
        self.refresh_table()

    def refresh_table(self):
        t = self.query_one("#elec_table", DataTable)
        t.clear()
        for r in DB.list_electronics():
            t.add_row(r["id"], r["category"], r["name"], r.get("brand","—"),
                      r.get("spec","—"), r["quantity"], r["unit"],
                      r.get("notes",""), key=str(r["id"]))

    def _current_id(self):
        t = self.query_one("#elec_table", DataTable)
        if t.cursor_row < 0: return None
        row = t.get_row_at(t.cursor_row)
        return row[0] if row else None

    @on(Button.Pressed, "#add_elec")
    def add(self):
        def cb(data):
            if data: DB.add_electronic(**data); self.refresh_table()
        self.app.push_screen(ElecModal(), cb)

    @on(Button.Pressed, "#edit_elec")
    def edit(self):
        rid = self._current_id()
        if rid is None:
            self.app.push_screen(MsgModal("Select a row first.")); return
        rows = [r for r in DB.list_electronics() if r["id"] == rid]
        if not rows: return
        def cb(data):
            if data: DB.update_electronic(rid, **data); self.refresh_table()
        self.app.push_screen(ElecModal(rows[0]), cb)

    @on(Button.Pressed, "#del_elec")
    def delete(self):
        rid = self._current_id()
        if rid is None:
            self.app.push_screen(MsgModal("Select a row first.")); return
        def cb(ok):
            if ok: DB.delete_electronic(rid); self.refresh_table()
        self.app.push_screen(ConfirmModal(f"Delete electronics item #{rid}?"), cb)


# ────────────────────────────────────────────────────────────────────────────────
#  3-D Print Jobs
# ────────────────────────────────────────────────────────────────────────────────

class PrintJobModal(ModalScreen):
    def __init__(self, row: dict | None = None):
        super().__init__()
        self._row = row or {}

    def compose(self) -> ComposeResult:
        r = self._row
        printers = [(p["name"], str(p["id"])) for p in DB.list_printers()]
        filaments = [
            (f"{f['brand']} {f['color']} {f['filament_type']} ({f['quantity_g']}g)", str(f["id"]))
            for f in DB.list_filaments()
        ]
        filaments = [("— None —", "")] + filaments
        with Container(id="dialog"):
            yield Label("── 3-D Print Job ────────────────────────")
            yield Label("Printer")
            yield Select(printers, value=str(r.get("printer_id", printers[0][1] if printers else "")), id="printer")
            yield Label("Filament used")
            yield Select(filaments, value=str(r.get("filament_id","")) if r.get("filament_id") else "", id="filament")
            yield Label("Filament used (g)")
            yield Input(str(r.get("filament_used_g","0")), id="grams")
            yield Label("3MF / STL file path (leave blank to skip)")
            yield Input(r.get("file_path",""), id="fpath", placeholder="/path/to/file.3mf")
            yield Label("Successful?")
            with Horizontal(classes="step-row"):
                yield Checkbox("Yes — successful print", bool(r.get("successful",1)), id="success")
            yield Label("Failure reason (if failed)")
            yield Input(r.get("failure_reason","") or "", id="fail_reason")
            yield Label("Notes")
            yield Input(r.get("notes",""), id="notes")
            with Horizontal(id="dialog-buttons"):
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", id="cancel")

    @on(Button.Pressed, "#save")
    def save(self):
        try:
            fil_raw = self.query_one("#filament", Select).value
            data = dict(
                printer_id=int(self.query_one("#printer", Select).value),
                filament_id=int(fil_raw) if fil_raw else None,
                filament_used_g=float(self.query_one("#grams", Input).value or 0),
                file_source_path=self.query_one("#fpath", Input).value.strip() or None,
                successful=1 if self.query_one("#success", Checkbox).value else 0,
                failure_reason=self.query_one("#fail_reason", Input).value.strip() or None,
                notes=self.query_one("#notes", Input).value.strip(),
            )
            self.dismiss(data)
        except (ValueError, Exception) as e:
            self.app.push_screen(MsgModal(f"Error: {e}"))

    @on(Button.Pressed, "#cancel")
    def cancel(self): self.dismiss(None)


class PrintJobPanel(Container):
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("+ Log Print", id="add_pj", variant="success")
            yield Button("✕ Delete", id="del_pj", variant="error")
            yield Button("📁 Open Files Folder", id="open_folder")
        yield DataTable(id="pj_table", zebra_stripes=True, cursor_type="row")

    def on_mount(self):
        t = self.query_one("#pj_table", DataTable)
        t.add_columns("ID","Date","Printer","Filament","Used(g)","File","OK?","Notes")
        self.refresh_table()

    def refresh_table(self):
        t = self.query_one("#pj_table", DataTable)
        t.clear()
        for r in DB.list_print_jobs():
            ok = "✔ Yes" if r["successful"] else "✘ No"
            t.add_row(r["id"], r["printed_at"][:10], r["printer_name"],
                      r.get("filament_desc","—"), r.get("filament_used_g","—"),
                      r.get("file_name","—"), ok, r.get("notes",""),
                      key=str(r["id"]))

    def _current_id(self):
        t = self.query_one("#pj_table", DataTable)
        if t.cursor_row < 0: return None
        row = t.get_row_at(t.cursor_row)
        return row[0] if row else None

    @on(Button.Pressed, "#add_pj")
    def add(self):
        def cb(data):
            if data: DB.add_print_job(**data); self.refresh_table()
        self.app.push_screen(PrintJobModal(), cb)

    @on(Button.Pressed, "#del_pj")
    def delete(self):
        rid = self._current_id()
        if rid is None:
            self.app.push_screen(MsgModal("Select a row first.")); return
        def cb(ok):
            if ok: DB.delete_print_job(rid); self.refresh_table()
        self.app.push_screen(ConfirmModal(f"Delete print job #{rid}?"), cb)

    @on(Button.Pressed, "#open_folder")
    def open_folder(self):
        import subprocess, os
        folder = str(DB.PRINTS_DIR)
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            elif sys.platform == "win32":
                os.startfile(folder)
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception:
            pass
        self.app.push_screen(MsgModal(f"Files folder:\n{folder}"))


# ────────────────────────────────────────────────────────────────────────────────
#  Braille Jobs
# ────────────────────────────────────────────────────────────────────────────────

BRAILLE_TYPES = [
    ("Literary","literary"),
    ("Math","math"),
    ("Science","science"),
    ("Music","music"),
]
BRAILLE_STEPS = ["digitized","formatted","brailled","proofread","delivered"]


class BrailleJobModal(ModalScreen):
    def __init__(self, row: dict | None = None):
        super().__init__()
        self._row = row or {}

    def compose(self) -> ComposeResult:
        r = self._row
        with Container(id="dialog"):
            yield Label("── Braille Job ──────────────────────────")
            yield Label("Title / Description")
            yield Input(r.get("title",""), id="title", placeholder="e.g. Math Worksheet Ch3")
            yield Label("Braille Type")
            yield Select(BRAILLE_TYPES, value=r.get("braille_type","literary"), id="btype")
            yield Label("Progress Steps")
            for step in BRAILLE_STEPS:
                yield Checkbox(step.capitalize(), bool(r.get(step,0)), id=f"step_{step}")
            yield Label("Notes")
            yield Input(r.get("notes",""), id="notes")
            with Horizontal(id="dialog-buttons"):
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", id="cancel")

    @on(Button.Pressed, "#save")
    def save(self):
        steps = {step: (1 if self.query_one(f"#step_{step}", Checkbox).value else 0)
                 for step in BRAILLE_STEPS}
        data = dict(
            title=self.query_one("#title", Input).value.strip(),
            braille_type=self.query_one("#btype", Select).value,
            notes=self.query_one("#notes", Input).value.strip(),
            **steps
        )
        if not data["title"]:
            self.app.push_screen(MsgModal("Title is required.")); return
        self.dismiss(data)

    @on(Button.Pressed, "#cancel")
    def cancel(self): self.dismiss(None)


def _progress_bar(row: dict, steps: list[str]) -> str:
    done = sum(1 for s in steps if row.get(s))
    total = len(steps)
    filled = "█" * done
    empty  = "░" * (total - done)
    return f"{filled}{empty} {done}/{total}"


class BrailleJobPanel(Container):
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("+ New Job", id="add_bj", variant="success")
            yield Button("✎ Edit / Update Steps", id="edit_bj")
            yield Button("✕ Delete", id="del_bj", variant="error")
        yield DataTable(id="bj_table", zebra_stripes=True, cursor_type="row")

    def on_mount(self):
        t = self.query_one("#bj_table", DataTable)
        t.add_columns("ID","Title","Type","Progress","Notes","Created")
        self.refresh_table()

    def refresh_table(self):
        t = self.query_one("#bj_table", DataTable)
        t.clear()
        for r in DB.list_braille_jobs():
            prog = _progress_bar(r, BRAILLE_STEPS)
            t.add_row(r["id"], r["title"], r["braille_type"], prog,
                      r.get("notes",""), r["created_at"][:10], key=str(r["id"]))

    def _current_id(self):
        t = self.query_one("#bj_table", DataTable)
        if t.cursor_row < 0: return None
        row = t.get_row_at(t.cursor_row)
        return row[0] if row else None

    @on(Button.Pressed, "#add_bj")
    def add(self):
        def cb(data):
            if data:
                steps = {s: data.pop(s) for s in BRAILLE_STEPS}
                DB.add_braille_job(**{k:v for k,v in data.items()
                                      if k in ["title","braille_type","notes"]})
                jobs = DB.list_braille_jobs()
                if jobs: DB.update_braille_job(jobs[0]["id"], **steps)
                self.refresh_table()
        self.app.push_screen(BrailleJobModal(), cb)

    @on(Button.Pressed, "#edit_bj")
    def edit(self):
        rid = self._current_id()
        if rid is None:
            self.app.push_screen(MsgModal("Select a row first.")); return
        rows = [r for r in DB.list_braille_jobs() if r["id"] == rid]
        if not rows: return
        def cb(data):
            if data: DB.update_braille_job(rid, **data); self.refresh_table()
        self.app.push_screen(BrailleJobModal(rows[0]), cb)

    @on(Button.Pressed, "#del_bj")
    def delete(self):
        rid = self._current_id()
        if rid is None:
            self.app.push_screen(MsgModal("Select a row first.")); return
        def cb(ok):
            if ok: DB.delete_braille_job(rid); self.refresh_table()
        self.app.push_screen(ConfirmModal(f"Delete braille job #{rid}?"), cb)


# ────────────────────────────────────────────────────────────────────────────────
#  Large Print / eBraille Jobs
# ────────────────────────────────────────────────────────────────────────────────

LP_TYPES  = [("Large Print","large_print"),("eBraille","ebraille")]
LP_STEPS  = ["digitized","formatted","converted","proofread","delivered"]
LP_LABELS = {"converted": "eBraille / To Large Print"}


class LPJobModal(ModalScreen):
    def __init__(self, row: dict | None = None):
        super().__init__()
        self._row = row or {}

    def compose(self) -> ComposeResult:
        r = self._row
        with Container(id="dialog"):
            yield Label("── Large Print / eBraille Job ───────────")
            yield Label("Title / Description")
            yield Input(r.get("title",""), id="title", placeholder="e.g. Science Textbook Ch7")
            yield Label("Job Type")
            yield Select(LP_TYPES, value=r.get("job_type","large_print"), id="jtype")
            yield Label("Progress Steps")
            for step in LP_STEPS:
                label = LP_LABELS.get(step, step.capitalize())
                yield Checkbox(label, bool(r.get(step,0)), id=f"step_{step}")
            yield Label("Notes")
            yield Input(r.get("notes",""), id="notes")
            with Horizontal(id="dialog-buttons"):
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", id="cancel")

    @on(Button.Pressed, "#save")
    def save(self):
        steps = {step: (1 if self.query_one(f"#step_{step}", Checkbox).value else 0)
                 for step in LP_STEPS}
        data = dict(
            title=self.query_one("#title", Input).value.strip(),
            job_type=self.query_one("#jtype", Select).value,
            notes=self.query_one("#notes", Input).value.strip(),
            **steps
        )
        if not data["title"]:
            self.app.push_screen(MsgModal("Title is required.")); return
        self.dismiss(data)

    @on(Button.Pressed, "#cancel")
    def cancel(self): self.dismiss(None)


class LPJobPanel(Container):
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("+ New Job", id="add_lj", variant="success")
            yield Button("✎ Edit / Update Steps", id="edit_lj")
            yield Button("✕ Delete", id="del_lj", variant="error")
        yield DataTable(id="lj_table", zebra_stripes=True, cursor_type="row")

    def on_mount(self):
        t = self.query_one("#lj_table", DataTable)
        t.add_columns("ID","Title","Type","Progress","Notes","Created")
        self.refresh_table()

    def refresh_table(self):
        t = self.query_one("#lj_table", DataTable)
        t.clear()
        for r in DB.list_lp_jobs():
            prog = _progress_bar(r, LP_STEPS)
            t.add_row(r["id"], r["title"], r["job_type"], prog,
                      r.get("notes",""), r["created_at"][:10], key=str(r["id"]))

    def _current_id(self):
        t = self.query_one("#lj_table", DataTable)
        if t.cursor_row < 0: return None
        row = t.get_row_at(t.cursor_row)
        return row[0] if row else None

    @on(Button.Pressed, "#add_lj")
    def add(self):
        def cb(data):
            if data:
                steps = {s: data.pop(s) for s in LP_STEPS}
                DB.add_lp_job(**{k:v for k,v in data.items()
                                 if k in ["title","job_type","notes"]})
                jobs = DB.list_lp_jobs()
                if jobs: DB.update_lp_job(jobs[0]["id"], **steps)
                self.refresh_table()
        self.app.push_screen(LPJobModal(), cb)

    @on(Button.Pressed, "#edit_lj")
    def edit(self):
        rid = self._current_id()
        if rid is None:
            self.app.push_screen(MsgModal("Select a row first.")); return
        rows = [r for r in DB.list_lp_jobs() if r["id"] == rid]
        if not rows: return
        def cb(data):
            if data: DB.update_lp_job(rid, **data); self.refresh_table()
        self.app.push_screen(LPJobModal(rows[0]), cb)

    @on(Button.Pressed, "#del_lj")
    def delete(self):
        rid = self._current_id()
        if rid is None:
            self.app.push_screen(MsgModal("Select a row first.")); return
        def cb(ok):
            if ok: DB.delete_lp_job(rid); self.refresh_table()
        self.app.push_screen(ConfirmModal(f"Delete LP/eBraille job #{rid}?"), cb)


# ────────────────────────────────────────────────────────────────────────────────
#  Main App
# ────────────────────────────────────────────────────────────────────────────────

SECTIONS = [
    ("🧵  Filament",       "filament"),
    ("📄  Braille Paper",  "paper"),
    ("⚡  Electronics",    "electronics"),
    ("🖨️  3-D Print Jobs", "printjobs"),
    ("⠿  Braille Jobs",    "braille"),
    ("🔠  LP / eBraille",  "lp"),
]


class MainApp(App):
    CSS = APP_CSS
    TITLE = "Braille & Maker Studio — Project Manager"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+r", "refresh", "Refresh"),
    ]

    current_section: reactive[str] = reactive("filament")

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Static("SECTIONS", classes="section-title")
                for label, key in SECTIONS:
                    yield Button(label, id=f"nav_{key}")
            with ScrollableContainer(id="content"):
                yield FilamentPanel(id="panel_filament")
                yield PaperPanel(id="panel_paper")
                yield ElecPanel(id="panel_electronics")
                yield PrintJobPanel(id="panel_printjobs")
                yield BrailleJobPanel(id="panel_braille")
                yield LPJobPanel(id="panel_lp")
        yield Footer()

    def on_mount(self):
        self._show_section("filament")

    def _show_section(self, key: str):
        for _, k in SECTIONS:
            panel = self.query_one(f"#panel_{k}")
            panel.display = (k == key)
        self.current_section = key

    @on(Button.Pressed)
    def handle_nav(self, event: Button.Pressed):
        bid = event.button.id or ""
        if bid.startswith("nav_"):
            self._show_section(bid[4:])

    def action_refresh(self):
        panel = self.query_one(f"#panel_{self.current_section}")
        if hasattr(panel, "refresh_table"):
            panel.refresh_table()


# ────────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    DB.init_db()
    app = MainApp()
    app.run()
