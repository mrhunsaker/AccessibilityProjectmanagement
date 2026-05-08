"""
Data-access helpers — thin wrappers around raw SQL.
All functions return plain dicts or lists of dicts for easy use in the TUI.
"""
from __future__ import annotations
import shutil
from pathlib import Path
from .schema import get_conn, PRINTS_DIR

# ── Utility ─────────────────────────────────────────────────────────────────

def _rows(cur) -> list[dict]:
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

def _touch_updated(conn, table: str, row_id: int):
    conn.execute(
        f"UPDATE {table} SET updated_at = datetime('now') WHERE id = ?", (row_id,)
    )

# ── Filament ─────────────────────────────────────────────────────────────────

def list_filaments() -> list[dict]:
    with get_conn() as c:
        return _rows(c.execute(
            "SELECT * FROM filament ORDER BY brand, color"
        ))

def add_filament(brand, color, filament_type, diameter_mm=1.75, quantity_g=0, notes=""):
    with get_conn() as c:
        c.execute(
            "INSERT INTO filament (brand,color,filament_type,diameter_mm,quantity_g,notes) VALUES (?,?,?,?,?,?)",
            (brand, color, filament_type, diameter_mm, quantity_g, notes)
        )

def update_filament(row_id: int, **fields):
    allowed = {"brand","color","filament_type","diameter_mm","quantity_g","notes"}
    sets = ", ".join(f"{k}=?" for k in fields if k in allowed)
    vals = [v for k,v in fields.items() if k in allowed] + [row_id]
    with get_conn() as c:
        c.execute(f"UPDATE filament SET {sets}, updated_at=datetime('now') WHERE id=?", vals)

def delete_filament(row_id: int):
    with get_conn() as c:
        c.execute("DELETE FROM filament WHERE id=?", (row_id,))

def deduct_filament(row_id: int, grams: float):
    with get_conn() as c:
        c.execute(
            "UPDATE filament SET quantity_g = MAX(0, quantity_g - ?), updated_at=datetime('now') WHERE id=?",
            (grams, row_id)
        )

# ── Braille Paper ─────────────────────────────────────────────────────────────

def list_paper() -> list[dict]:
    with get_conn() as c:
        return _rows(c.execute("SELECT * FROM braille_paper ORDER BY paper_type"))

def add_paper(paper_type, quantity, size=None, label_type=None, notes=""):
    with get_conn() as c:
        c.execute(
            "INSERT INTO braille_paper (paper_type,size,label_type,quantity,notes) VALUES (?,?,?,?,?)",
            (paper_type, size, label_type, quantity, notes)
        )

def update_paper(row_id: int, **fields):
    allowed = {"paper_type","size","label_type","quantity","notes"}
    sets = ", ".join(f"{k}=?" for k in fields if k in allowed)
    vals = [v for k,v in fields.items() if k in allowed] + [row_id]
    with get_conn() as c:
        c.execute(f"UPDATE braille_paper SET {sets}, updated_at=datetime('now') WHERE id=?", vals)

def delete_paper(row_id: int):
    with get_conn() as c:
        c.execute("DELETE FROM braille_paper WHERE id=?", (row_id,))

# ── Electronics ───────────────────────────────────────────────────────────────

def list_electronics(category=None) -> list[dict]:
    with get_conn() as c:
        if category:
            return _rows(c.execute(
                "SELECT * FROM electronics WHERE category=? ORDER BY name", (category,)
            ))
        return _rows(c.execute("SELECT * FROM electronics ORDER BY category, name"))

def add_electronic(category, name, quantity, brand=None, spec=None, unit="pcs", notes=""):
    with get_conn() as c:
        c.execute(
            "INSERT INTO electronics (category,name,brand,spec,quantity,unit,notes) VALUES (?,?,?,?,?,?,?)",
            (category, name, brand, spec, quantity, unit, notes)
        )

def update_electronic(row_id: int, **fields):
    allowed = {"category","name","brand","spec","quantity","unit","notes"}
    sets = ", ".join(f"{k}=?" for k in fields if k in allowed)
    vals = [v for k,v in fields.items() if k in allowed] + [row_id]
    with get_conn() as c:
        c.execute(f"UPDATE electronics SET {sets}, updated_at=datetime('now') WHERE id=?", vals)

def delete_electronic(row_id: int):
    with get_conn() as c:
        c.execute("DELETE FROM electronics WHERE id=?", (row_id,))

# ── Printers ──────────────────────────────────────────────────────────────────

def list_printers() -> list[dict]:
    with get_conn() as c:
        return _rows(c.execute("SELECT * FROM printer ORDER BY name"))

# ── Print Jobs ────────────────────────────────────────────────────────────────

def list_print_jobs() -> list[dict]:
    with get_conn() as c:
        return _rows(c.execute("""
            SELECT pj.*, p.name AS printer_name,
                   f.brand || ' ' || f.color || ' ' || f.filament_type AS filament_desc
            FROM print_job pj
            JOIN printer p ON p.id = pj.printer_id
            LEFT JOIN filament f ON f.id = pj.filament_id
            ORDER BY pj.printed_at DESC
        """))

def add_print_job(printer_id, filament_id, filament_used_g, file_source_path=None,
                  successful=1, failure_reason=None, notes=""):
    file_path = None
    file_name = None
    if file_source_path:
        src = Path(file_source_path)
        dest = PRINTS_DIR / src.name
        if src.exists() and src != dest:
            shutil.copy2(src, dest)
        file_path = str(dest.relative_to(PRINTS_DIR.parent))
        file_name = src.name

    with get_conn() as c:
        c.execute(
            """INSERT INTO print_job
               (printer_id,filament_id,filament_used_g,file_path,file_name,successful,failure_reason,notes)
               VALUES (?,?,?,?,?,?,?,?)""",
            (printer_id, filament_id, filament_used_g, file_path, file_name,
             successful, failure_reason, notes)
        )
    if filament_id and filament_used_g:
        deduct_filament(filament_id, filament_used_g)

def delete_print_job(row_id: int):
    with get_conn() as c:
        c.execute("DELETE FROM print_job WHERE id=?", (row_id,))

def list_print_files() -> list[Path]:
    return sorted(PRINTS_DIR.glob("*"))

# ── Braille Jobs ──────────────────────────────────────────────────────────────

def list_braille_jobs() -> list[dict]:
    with get_conn() as c:
        return _rows(c.execute(
            "SELECT * FROM braille_job ORDER BY created_at DESC"
        ))

def add_braille_job(title, braille_type, notes=""):
    with get_conn() as c:
        c.execute(
            "INSERT INTO braille_job (title,braille_type,notes) VALUES (?,?,?)",
            (title, braille_type, notes)
        )

def update_braille_job(row_id: int, **fields):
    allowed = {"title","braille_type","digitized","formatted","brailled","proofread","delivered","notes"}
    sets = ", ".join(f"{k}=?" for k in fields if k in allowed)
    vals = [v for k,v in fields.items() if k in allowed] + [row_id]
    with get_conn() as c:
        c.execute(f"UPDATE braille_job SET {sets}, updated_at=datetime('now') WHERE id=?", vals)

def delete_braille_job(row_id: int):
    with get_conn() as c:
        c.execute("DELETE FROM braille_job WHERE id=?", (row_id,))

# ── LP / eBraille Jobs ────────────────────────────────────────────────────────

def list_lp_jobs() -> list[dict]:
    with get_conn() as c:
        return _rows(c.execute(
            "SELECT * FROM lp_ebraille_job ORDER BY created_at DESC"
        ))

def add_lp_job(title, job_type, notes=""):
    with get_conn() as c:
        c.execute(
            "INSERT INTO lp_ebraille_job (title,job_type,notes) VALUES (?,?,?)",
            (title, job_type, notes)
        )

def update_lp_job(row_id: int, **fields):
    allowed = {"title","job_type","digitized","formatted","converted","proofread","delivered","notes"}
    sets = ", ".join(f"{k}=?" for k in fields if k in allowed)
    vals = [v for k,v in fields.items() if k in allowed] + [row_id]
    with get_conn() as c:
        c.execute(f"UPDATE lp_ebraille_job SET {sets}, updated_at=datetime('now') WHERE id=?", vals)

def delete_lp_job(row_id: int):
    with get_conn() as c:
        c.execute("DELETE FROM lp_ebraille_job WHERE id=?", (row_id,))
