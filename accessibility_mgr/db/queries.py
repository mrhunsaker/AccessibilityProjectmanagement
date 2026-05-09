"""Data access helpers for the Accessibility Materials Project Manager."""

from __future__ import annotations

import shutil
import warnings
from pathlib import Path
from typing import Any

from .schema import PRINTS_DIR, get_conn

__all__ = [
    "list_filaments",
    "add_filament",
    "update_filament",
    "delete_filament",
    "deduct_filament",
    "list_paper",
    "add_paper",
    "update_paper",
    "delete_paper",
    "list_electronics",
    "add_electronic",
    "update_electronic",
    "delete_electronic",
    "list_printers",
    "add_printer",
    "update_printer",
    "delete_printer",
    "list_print_jobs",
    "add_print_job",
    "update_print_job",
    "delete_print_job",
    "list_print_files",
    "list_braille_jobs",
    "add_braille_job",
    "update_braille_job",
    "delete_braille_job",
    "list_lp_jobs",
    "add_lp_job",
    "update_lp_job",
    "delete_lp_job",
    "list_material_categories",
    "add_material_category",
    "update_material_category",
    "set_material_category_active",
    "delete_material_category",
    "list_workflow_steps",
    "add_workflow_step",
    "update_workflow_step",
    "set_workflow_step_active",
    "delete_workflow_step",
]


def _rows(cur: Any) -> list[dict[str, Any]]:
    """Convert sqlite cursor rows to plain dictionaries."""
    cols = [col[0] for col in cur.description]
    out: list[dict[str, Any]] = []
    for row in cur.fetchall():
        out.append({cols[idx]: row[idx] for idx in range(len(cols))})
    return out


def _build_update_sql(
    table: str,
    fields: dict[str, Any],
    allowed: set[str],
    include_updated_at: bool = True,
) -> tuple[str, list[Any]]:
    """Build a parameterized UPDATE SQL statement for allow-listed fields."""
    safe = {k: v for k, v in fields.items() if k in allowed}
    if not safe:
        raise ValueError(f"No valid fields to update in table '{table}'")

    allowed_tables = {
        "filament",
        "braille_paper",
        "electronics",
        "braille_job",
        "lp_ebraille_job",
        "material_category",
        "workflow_step",
        "print_job",
    }
    if table not in allowed_tables:
        raise ValueError(f"Disallowed table '{table}' for update")

    sets = ", ".join(f"{column} = ?" for column in safe)
    if include_updated_at:
        sql = f"UPDATE {table} SET {sets}, updated_at = datetime('now') WHERE id = ?"
    else:
        sql = f"UPDATE {table} SET {sets} WHERE id = ?"
    return sql, list(safe.values())


def list_filaments() -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM filament ORDER BY brand, color"))


def add_filament(
    brand: str,
    color: str,
    filament_type: str,
    diameter_mm: float = 1.75,
    quantity_g: float = 0,
    notes: str = "",
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO filament (brand,color,filament_type,diameter_mm,quantity_g,notes) VALUES (?,?,?,?,?,?)",
            (brand, color, filament_type, diameter_mm, quantity_g, notes),
        )
        return int(cur.lastrowid)


def update_filament(row_id: int, **fields: Any) -> None:
    allowed = {"brand", "color", "filament_type", "diameter_mm", "quantity_g", "notes"}
    sql, vals = _build_update_sql("filament", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_filament(row_id: int) -> None:
    """Delete filament; raises sqlite3.IntegrityError if referenced by print jobs."""
    with get_conn() as conn:
        conn.execute("DELETE FROM filament WHERE id=?", (row_id,))


def deduct_filament(row_id: int, grams: float) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE filament SET quantity_g = MAX(0, quantity_g - ?), updated_at=datetime('now') WHERE id=?",
            (grams, row_id),
        )


def list_paper() -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM braille_paper ORDER BY paper_type"))


def add_paper(
    paper_type: str,
    quantity: int,
    size: str | None = None,
    label_type: str | None = None,
    notes: str = "",
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO braille_paper (paper_type,size,label_type,quantity,notes) VALUES (?,?,?,?,?)",
            (paper_type, size, label_type, quantity, notes),
        )
        return int(cur.lastrowid)


def update_paper(row_id: int, **fields: Any) -> None:
    allowed = {"paper_type", "size", "label_type", "quantity", "notes"}
    sql, vals = _build_update_sql("braille_paper", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_paper(row_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM braille_paper WHERE id=?", (row_id,))


def list_electronics(category: str | None = None) -> list[dict[str, Any]]:
    with get_conn() as conn:
        if category:
            return _rows(
                conn.execute("SELECT * FROM electronics WHERE category=? ORDER BY name", (category,))
            )
        return _rows(conn.execute("SELECT * FROM electronics ORDER BY category, name"))


def add_electronic(
    category: str,
    name: str,
    quantity: float,
    brand: str | None = None,
    spec: str | None = None,
    unit: str = "pcs",
    notes: str = "",
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO electronics (category,name,brand,spec,quantity,unit,notes) VALUES (?,?,?,?,?,?,?)",
            (category, name, brand, spec, quantity, unit, notes),
        )
        return int(cur.lastrowid)


def update_electronic(row_id: int, **fields: Any) -> None:
    allowed = {"category", "name", "brand", "spec", "quantity", "unit", "notes"}
    sql, vals = _build_update_sql("electronics", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_electronic(row_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM electronics WHERE id=?", (row_id,))


def list_printers() -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM printer ORDER BY name"))


def add_printer(name: str) -> int:
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO printer (name) VALUES (?)", (name,))
        return int(cur.lastrowid)


def update_printer(row_id: int, name: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE printer SET name=? WHERE id=?", (name, row_id))


def delete_printer(row_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM printer WHERE id=?", (row_id,))


def list_print_jobs() -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(
            conn.execute(
                """
                SELECT pj.*, p.name AS printer_name,
                       f.brand || ' ' || f.color || ' ' || f.filament_type AS filament_desc
                FROM print_job pj
                LEFT JOIN printer p ON p.id = pj.printer_id
                LEFT JOIN filament f ON f.id = pj.filament_id
                ORDER BY pj.printed_at DESC
                """
            )
        )


def add_print_job(
    printer_id: int,
    filament_id: int | None,
    filament_used_g: float,
    file_source_path: str | None = None,
    successful: int = 1,
    failure_reason: str | None = None,
    notes: str = "",
) -> int:
    """Log a print job, optionally copying an attached file. Returns new row id."""
    file_path: str | None = None
    file_name: str | None = None

    if file_source_path:
        src = Path(file_source_path)
        dest = PRINTS_DIR / src.name
        if src.exists() and src != dest:
            try:
                shutil.copy2(src, dest)
                file_path = str(dest.relative_to(PRINTS_DIR.parent))
                file_name = src.name
            except OSError as exc:
                warnings.warn(
                    f"Could not copy print file '{src}' to '{dest}': {exc}",
                    RuntimeWarning,
                    stacklevel=2,
                )
        elif src == dest:
            file_path = str(dest.relative_to(PRINTS_DIR.parent))
            file_name = src.name

    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO print_job
               (printer_id,filament_id,filament_used_g,file_path,file_name,successful,failure_reason,notes)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                printer_id,
                filament_id,
                filament_used_g,
                file_path,
                file_name,
                successful,
                failure_reason,
                notes,
            ),
        )
        new_id = int(cur.lastrowid)

    if filament_id and filament_used_g:
        deduct_filament(filament_id, filament_used_g)

    return new_id


def update_print_job(row_id: int, **fields: Any) -> None:
    allowed = {
        "printer_id",
        "filament_id",
        "filament_used_g",
        "successful",
        "failure_reason",
        "notes",
    }
    sql, vals = _build_update_sql("print_job", fields, allowed, include_updated_at=False)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_print_job(row_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM print_job WHERE id=?", (row_id,))


def list_print_files() -> list[Path]:
    return sorted(PRINTS_DIR.glob("*"))


def list_braille_jobs() -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM braille_job ORDER BY created_at DESC"))


def add_braille_job(title: str, braille_type: str, notes: str = "") -> int:
    """Insert a braille job and return the new row id."""
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO braille_job (title,braille_type,notes) VALUES (?,?,?)",
            (title, braille_type, notes),
        )
        return int(cur.lastrowid)


def update_braille_job(row_id: int, **fields: Any) -> None:
    allowed = {
        "title",
        "braille_type",
        "digitized",
        "formatted",
        "brailled",
        "proofread",
        "delivered",
        "notes",
    }
    sql, vals = _build_update_sql("braille_job", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_braille_job(row_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM braille_job WHERE id=?", (row_id,))


def list_lp_jobs() -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM lp_ebraille_job ORDER BY created_at DESC"))


def add_lp_job(title: str, job_type: str, notes: str = "") -> int:
    """Insert an LP/eBraille job and return the new row id."""
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO lp_ebraille_job (title,job_type,notes) VALUES (?,?,?)",
            (title, job_type, notes),
        )
        return int(cur.lastrowid)


def update_lp_job(row_id: int, **fields: Any) -> None:
    allowed = {
        "title",
        "job_type",
        "digitized",
        "formatted",
        "converted",
        "proofread",
        "delivered",
        "notes",
    }
    sql, vals = _build_update_sql("lp_ebraille_job", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_lp_job(row_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM lp_ebraille_job WHERE id=?", (row_id,))


def list_material_categories(
    section: str | None = None,
    active_only: bool = True,
) -> list[dict[str, Any]]:
    with get_conn() as conn:
        filters: list[str] = []
        params: list[Any] = []
        if section:
            filters.append("section = ?")
            params.append(section)
        if active_only:
            filters.append("active = 1")

        where = ""
        if filters:
            where = "WHERE " + " AND ".join(filters)

        return _rows(
            conn.execute(
                f"SELECT * FROM material_category {where} ORDER BY section, sort_order, label",
                params,
            )
        )


def add_material_category(section: str, value: str, label: str, sort_order: int = 0) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO material_category (section, value, label, sort_order) VALUES (?,?,?,?)",
            (section, value, label, sort_order),
        )
        return int(cur.lastrowid)


def update_material_category(row_id: int, **fields: Any) -> None:
    allowed = {"section", "value", "label", "sort_order", "active"}
    sql, vals = _build_update_sql("material_category", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def set_material_category_active(row_id: int, active: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE material_category SET active=?, updated_at=datetime('now') WHERE id=?",
            (active, row_id),
        )


def delete_material_category(row_id: int) -> None:
    """Soft-delete a material category (active=0)."""
    set_material_category_active(row_id, 0)


def list_workflow_steps(
    job_type: str | None = None,
    active_only: bool = True,
) -> list[dict[str, Any]]:
    with get_conn() as conn:
        filters: list[str] = []
        params: list[Any] = []
        if job_type:
            filters.append("job_type = ?")
            params.append(job_type)
        if active_only:
            filters.append("active = 1")

        where = ""
        if filters:
            where = "WHERE " + " AND ".join(filters)

        return _rows(
            conn.execute(
                f"SELECT * FROM workflow_step {where} ORDER BY job_type, sort_order, label",
                params,
            )
        )


def add_workflow_step(job_type: str, step_key: str, label: str, sort_order: int = 0) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO workflow_step (job_type, step_key, label, sort_order) VALUES (?,?,?,?)",
            (job_type, step_key, label, sort_order),
        )
        return int(cur.lastrowid)


def update_workflow_step(row_id: int, **fields: Any) -> None:
    allowed = {"job_type", "step_key", "label", "sort_order", "active"}
    sql, vals = _build_update_sql("workflow_step", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def set_workflow_step_active(row_id: int, active: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE workflow_step SET active=?, updated_at=datetime('now') WHERE id=?",
            (active, row_id),
        )


def delete_workflow_step(row_id: int) -> None:
    """Soft-delete a workflow step (active=0)."""
    set_workflow_step_active(row_id, 0)
