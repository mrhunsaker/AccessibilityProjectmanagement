"""
Data access layer — ALL SQL lives here.

Every public function uses parameterised queries ('?' placeholders).
No SQL strings are constructed outside this module.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import difflib
import re
import shutil
import uuid
import warnings
from pathlib import Path
from typing import Any, Optional

from .schema import ARTIFACTS_DIR, FILES_DIR, PRINTS_DIR, get_conn

__all__ = [
    # Filament
    "list_filaments", "add_filament", "update_filament", "delete_filament", "deduct_filament",
    # Paper
    "list_paper", "add_paper", "update_paper", "delete_paper",
    # Electronics
    "list_electronics", "add_electronic", "update_electronic", "delete_electronic",
    # Printers
    "list_printers", "add_printer", "update_printer", "delete_printer",
    # Embossers
    "list_embossers", "add_embosser", "update_embosser", "delete_embosser",
    # Print jobs
    "list_print_jobs", "add_print_job", "update_print_job", "delete_print_job",
    # Braille jobs
    "list_braille_jobs", "get_braille_job", "add_braille_job", "update_braille_job", "delete_braille_job",
    # LP/eBraille jobs
    "list_lp_jobs", "get_lp_job", "add_lp_job", "update_lp_job", "delete_lp_job",
    # Tactile graphics jobs
    "list_tactile_jobs", "get_tactile_job", "add_tactile_job", "update_tactile_job", "delete_tactile_job",
    # File objects
    "list_file_objects", "get_file_object", "ingest_file", "update_file_object", "delete_file_object",
    # Job-file links
    "link_file_to_job", "list_files_for_job", "unlink_file_from_job",
    # Events
    "log_event", "list_events_for_job",
    # Structural map
    "add_struct_node", "list_struct_nodes", "delete_struct_node",
    # Job metadata
    "set_job_metadata", "get_job_metadata", "list_job_metadata", "delete_job_metadata",
    "list_distinct_metadata_keys", "backfill_metadata_keys",
    # Lookup tables
    "list_material_categories", "add_material_category", "update_material_category",
    "set_material_category_active", "delete_material_category",
    "list_workflow_steps", "add_workflow_step", "update_workflow_step",
    "set_workflow_step_active", "delete_workflow_step",
    # Step helpers
    "complete_step", "revert_step",
    # QA
    "log_qa_run", "list_qa_runs",
    # Pipeline
    "start_pipeline_run", "finish_pipeline_run", "log_pipeline_step",
    "list_pipeline_runs", "list_pipeline_step_runs",
    # Backup log
    "log_backup", "list_backup_log",
    # Paths
    "ARTIFACTS_DIR", "FILES_DIR", "PRINTS_DIR",
]


# ── Internal helpers ──────────────────────────────────────────────────────────

# Tables that have an updated_at column and should receive automatic timestamp updates
_TABLES_WITH_UPDATED_AT = {
    "filament", "braille_paper", "electronics",
    "printer", "embosser",
    "print_job", "braille_job", "lp_ebraille_job", "tactile_graphics_job",
    "file_object", "job_metadata", "material_category", "workflow_step",
}

# All tables safe to use in dynamic UPDATE construction
_SAFE_TABLES = _TABLES_WITH_UPDATED_AT | {
    "structural_map_node",
}


def _sanitize_name(value: str) -> str:
    """Strip characters unsafe for file/directory names, preserving alphanumerics and hyphens."""
    return re.sub(r"[^\w\-]", "", value.replace(" ", "")) or "_"


def _rows(cur: Any) -> list[dict[str, Any]]:
    """ rows.
    
    Parameters
    ----------
    cur : Any
        cur parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    cols = [c[0] for c in cur.description]
    return [{cols[i]: row[i] for i in range(len(cols))} for row in cur.fetchall()]


def _build_update_sql(
    table: str,
    fields: dict[str, Any],
    allowed: set[str],
    has_updated_at: bool = True,
) -> tuple[str, list[Any]]:
    """Build a safe parameterised UPDATE statement.

    Column names are validated against `allowed`; values are always bound
    parameters, never interpolated.  When `has_updated_at` is True (default),
    ``updated_at = datetime('now')`` is appended automatically — pass False for
    tables that lack this column (printer, embosser in older DB schemas will
    receive the column via migration, but the flag remains for safety).
    """
    if table not in _SAFE_TABLES:
        raise ValueError(f"Disallowed table '{table}'")
    safe = {k: v for k, v in fields.items() if k in allowed}
    if not safe:
        raise ValueError(f"No valid fields to update in '{table}'")
    sets = ", ".join(f"{c} = ?" for c in safe)
    ts = ", updated_at = datetime('now')" if has_updated_at else ""
    return f"UPDATE {table} SET {sets}{ts} WHERE id = ?", list(safe.values())  # noqa: S608


def _sha256(path: Path) -> str:
    """ sha256.
    
    Parameters
    ----------
    path : Any
        path parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ── Filament ──────────────────────────────────────────────────────────────────

def list_filaments() -> list[dict[str, Any]]:
    """List filaments.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM filament ORDER BY brand, color"))


def add_filament(
    brand: str, color: str, filament_type: str,
    diameter_mm: float = 1.75, quantity_g: float = 0,
    cost_per_kg: Optional[float] = None, supplier: str = "", notes: str = "",
) -> int:
    """Add filament.
    
    Parameters
    ----------
    brand : Any
        brand parameter.
    
    color : Any
        color parameter.
    
    filament_type : Any
        filament_type parameter.
    
    diameter_mm : Any
        diameter_mm parameter.
    
    quantity_g : Any
        quantity_g parameter.
    
    cost_per_kg : Any
        cost_per_kg parameter.
    
    supplier : Any
        supplier parameter.
    
    notes : Any
        notes parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO filament (brand,color,filament_type,diameter_mm,quantity_g,"
            "cost_per_kg,supplier,notes) VALUES (?,?,?,?,?,?,?,?)",
            (brand, color, filament_type, diameter_mm, quantity_g, cost_per_kg, supplier, notes),
        )
        return int(cur.lastrowid)


def update_filament(row_id: int, **fields: Any) -> None:
    """Update filament.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    allowed = {"brand", "color", "filament_type", "diameter_mm", "quantity_g",
               "cost_per_kg", "supplier", "notes"}
    sql, vals = _build_update_sql("filament", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_filament(row_id: int) -> None:
    """Delete filament.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        conn.execute("DELETE FROM filament WHERE id = ?", (row_id,))


def deduct_filament(row_id: int, grams: float) -> None:
    """Deduct filament.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    grams : Any
        grams parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        conn.execute(
            "UPDATE filament SET quantity_g = MAX(0, quantity_g - ?), "
            "updated_at = datetime('now') WHERE id = ?",
            (grams, row_id),
        )


# ── Paper ─────────────────────────────────────────────────────────────────────

def list_paper() -> list[dict[str, Any]]:
    """List paper.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM braille_paper ORDER BY paper_type"))


def add_paper(
    paper_type: str, quantity: int,
    size: Optional[str] = None, label_type: Optional[str] = None,
    supplier: str = "", notes: str = "",
) -> int:
    """Add paper.
    
    Parameters
    ----------
    paper_type : Any
        paper_type parameter.
    
    quantity : Any
        quantity parameter.
    
    size : Any
        size parameter.
    
    label_type : Any
        label_type parameter.
    
    supplier : Any
        supplier parameter.
    
    notes : Any
        notes parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO braille_paper (paper_type,size,label_type,quantity,supplier,notes) "
            "VALUES (?,?,?,?,?,?)",
            (paper_type, size, label_type, quantity, supplier, notes),
        )
        return int(cur.lastrowid)


def update_paper(row_id: int, **fields: Any) -> None:
    """Update paper.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    allowed = {"paper_type", "size", "label_type", "quantity", "supplier", "notes"}
    sql, vals = _build_update_sql("braille_paper", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_paper(row_id: int) -> None:
    """Delete paper.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        conn.execute("DELETE FROM braille_paper WHERE id = ?", (row_id,))


# ── Electronics ───────────────────────────────────────────────────────────────

def list_electronics(category: Optional[str] = None) -> list[dict[str, Any]]:
    """List electronics.
    
    Parameters
    ----------
    category : Any
        category parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        if category:
            return _rows(conn.execute(
                "SELECT * FROM electronics WHERE category = ? ORDER BY name", (category,),
            ))
        return _rows(conn.execute("SELECT * FROM electronics ORDER BY category, name"))


def add_electronic(
    category: str, name: str, quantity: float,
    brand: Optional[str] = None, spec: Optional[str] = None,
    unit: str = "pcs", cost_each: Optional[float] = None,
    supplier: str = "", notes: str = "",
) -> int:
    """Add electronic.
    
    Parameters
    ----------
    category : Any
        category parameter.
    
    name : Any
        name parameter.
    
    quantity : Any
        quantity parameter.
    
    brand : Any
        brand parameter.
    
    spec : Any
        spec parameter.
    
    unit : Any
        unit parameter.
    
    cost_each : Any
        cost_each parameter.
    
    supplier : Any
        supplier parameter.
    
    notes : Any
        notes parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO electronics (category,name,brand,spec,quantity,unit,"
            "cost_each,supplier,notes) VALUES (?,?,?,?,?,?,?,?,?)",
            (category, name, brand, spec, quantity, unit, cost_each, supplier, notes),
        )
        return int(cur.lastrowid)


def update_electronic(row_id: int, **fields: Any) -> None:
    """Update electronic.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    allowed = {"category", "name", "brand", "spec", "quantity", "unit",
               "cost_each", "supplier", "notes"}
    sql, vals = _build_update_sql("electronics", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_electronic(row_id: int) -> None:
    """Delete electronic.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        conn.execute("DELETE FROM electronics WHERE id = ?", (row_id,))


# ── Printers ──────────────────────────────────────────────────────────────────

def list_printers() -> list[dict[str, Any]]:
    """List printers.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM printer ORDER BY name"))


def add_printer(name: str, model: str = "", notes: str = "") -> int:
    """Add printer.
    
    Parameters
    ----------
    name : Any
        name parameter.
    
    model : Any
        model parameter.
    
    notes : Any
        notes parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO printer (name,model,notes) VALUES (?,?,?)", (name, model, notes),
        )
        return int(cur.lastrowid)


def update_printer(row_id: int, **fields: Any) -> None:
    """Update a printer record.  printer now has updated_at after migration."""
    allowed = {"name", "model", "notes"}
    sql, vals = _build_update_sql("printer", fields, allowed, has_updated_at=True)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_printer(row_id: int) -> None:
    """Delete printer.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        conn.execute("DELETE FROM printer WHERE id = ?", (row_id,))


# ── Embossers ─────────────────────────────────────────────────────────────────

def list_embossers() -> list[dict[str, Any]]:
    """List embossers.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM embosser ORDER BY name"))


def add_embosser(name: str, model: str = "", paper_type: str = "", notes: str = "") -> int:
    """Add embosser.
    
    Parameters
    ----------
    name : Any
        name parameter.
    
    model : Any
        model parameter.
    
    paper_type : Any
        paper_type parameter.
    
    notes : Any
        notes parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO embosser (name,model,paper_type,notes) VALUES (?,?,?,?)",
            (name, model, paper_type, notes),
        )
        return int(cur.lastrowid)


def update_embosser(row_id: int, **fields: Any) -> None:
    """Update an embosser record.  embosser now has updated_at after migration."""
    allowed = {"name", "model", "paper_type", "notes"}
    sql, vals = _build_update_sql("embosser", fields, allowed, has_updated_at=True)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_embosser(row_id: int) -> None:
    """Delete embosser.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        conn.execute("DELETE FROM embosser WHERE id = ?", (row_id,))


# ── Print jobs ────────────────────────────────────────────────────────────────

def list_print_jobs() -> list[dict[str, Any]]:
    """List print jobs.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        return _rows(conn.execute("""
            SELECT pj.*,
                   p.name  AS printer_name,
                   f.brand || ' ' || f.color || ' ' || f.filament_type AS filament_desc
            FROM print_job pj
            LEFT JOIN printer  p ON p.id = pj.printer_id
            LEFT JOIN filament f ON f.id = pj.filament_id
            ORDER BY pj.printed_at DESC
        """))


def add_print_job(
    printer_id: int, filament_id: Optional[int], filament_used_g: float,
    file_source_path: Optional[str] = None, successful: int = 1,
    failure_reason: Optional[str] = None, object_name: str = "",
    requester: str = "", request_date: Optional[str] = None, notes: str = "",
) -> int:
    """Add print job.
    
    Parameters
    ----------
    printer_id : Any
        printer_id parameter.
    
    filament_id : Any
        filament_id parameter.
    
    filament_used_g : Any
        filament_used_g parameter.
    
    file_source_path : Any
        file_source_path parameter.
    
    successful : Any
        successful parameter.
    
    failure_reason : Any
        failure_reason parameter.
    
    object_name : Any
        object_name parameter.
    
    requester : Any
        requester parameter.
    
    request_date : Any
        request_date parameter.
    
    notes : Any
        notes parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    file_path: Optional[str] = None
    file_name: Optional[str] = None
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
                    f"Could not copy print file '{src}': {exc}", RuntimeWarning, stacklevel=2,
                )
        elif src == dest:
            file_path = str(dest.relative_to(PRINTS_DIR.parent))
            file_name = src.name

    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO print_job (printer_id,filament_id,filament_used_g,file_path,"
            "file_name,successful,failure_reason,object_name,requester,request_date,notes) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (printer_id, filament_id, filament_used_g, file_path, file_name,
             successful, failure_reason, object_name, requester, request_date, notes),
        )
        new_id = int(cur.lastrowid)

    if filament_id and filament_used_g:
        deduct_filament(filament_id, filament_used_g)

    log_event("print", new_id, "CREATE", "SUCCESS",
              detail=f"Print job created: {object_name or file_name or 'unnamed'}")
    return new_id


def update_print_job(row_id: int, **fields: Any) -> None:
    """Update mutable fields on a print job record."""
    allowed = {"printer_id", "filament_id", "filament_used_g", "successful",
               "failure_reason", "object_name", "requester", "request_date", "notes"}
    sql, vals = _build_update_sql("print_job", fields, allowed, has_updated_at=True)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_print_job(row_id: int) -> None:
    """Delete print job.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        conn.execute("DELETE FROM print_job WHERE id = ?", (row_id,))


# ── Braille jobs ──────────────────────────────────────────────────────────────

def list_braille_jobs() -> list[dict[str, Any]]:
    """List braille jobs.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        return _rows(conn.execute("""
            SELECT bj.*, e.name AS embosser_name, e.paper_type AS embosser_paper_type
            FROM braille_job bj
            LEFT JOIN embosser e ON e.id = bj.embosser_id
            ORDER BY bj.created_at DESC
        """))


def get_braille_job(row_id: int) -> Optional[dict[str, Any]]:
    """Get braille job.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        rows = _rows(conn.execute("""
            SELECT bj.*, e.name AS embosser_name, e.paper_type AS embosser_paper_type
            FROM braille_job bj
            LEFT JOIN embosser e ON e.id = bj.embosser_id
            WHERE bj.id = ?
        """, (row_id,)))
        return rows[0] if rows else None


def add_braille_job(
    title: str, braille_type: str,
    embosser_id: Optional[int] = None,
    requester: str = "", request_date: Optional[str] = None,
    due_date: Optional[str] = None, priority: str = "normal", notes: str = "",
) -> int:
    """Add braille job.
    
    Parameters
    ----------
    title : Any
        title parameter.
    
    braille_type : Any
        braille_type parameter.
    
    embosser_id : Any
        embosser_id parameter.
    
    requester : Any
        requester parameter.
    
    request_date : Any
        request_date parameter.
    
    due_date : Any
        due_date parameter.
    
    priority : Any
        priority parameter.
    
    notes : Any
        notes parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO braille_job (title,braille_type,embosser_id,requester,request_date,"
            "due_date,priority,notes) VALUES (?,?,?,?,?,?,?,?)",
            (title, braille_type, embosser_id, requester, request_date, due_date, priority, notes),
        )
        new_id = int(cur.lastrowid)
    log_event("braille", new_id, "CREATE", "SUCCESS", detail=f"Job created: {title}")
    return new_id


def update_braille_job(row_id: int, **fields: Any) -> None:
    """Update braille job.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    allowed = {"title", "braille_type", "embosser_id", "requester", "request_date", "due_date",
               "priority", "digitized", "formatted", "brailled", "proofread",
               "delivered", "notes"}
    sql, vals = _build_update_sql("braille_job", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_braille_job(row_id: int) -> None:
    """Delete braille job.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        conn.execute("DELETE FROM braille_job WHERE id = ?", (row_id,))


# ── LP/eBraille jobs ──────────────────────────────────────────────────────────

def list_lp_jobs(job_type: Optional[str] = None) -> list[dict[str, Any]]:
    """List lp jobs.
    
    Parameters
    ----------
    job_type : Any
        job_type parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        if job_type:
            return _rows(conn.execute(
                "SELECT * FROM lp_ebraille_job WHERE job_type = ? ORDER BY created_at DESC",
                (job_type,),
            ))
        return _rows(conn.execute("SELECT * FROM lp_ebraille_job ORDER BY created_at DESC"))


def get_lp_job(row_id: int) -> Optional[dict[str, Any]]:
    """Get lp job.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        rows = _rows(conn.execute("SELECT * FROM lp_ebraille_job WHERE id = ?", (row_id,)))
        return rows[0] if rows else None


def add_lp_job(
    title: str, job_type: str,
    requester: str = "", request_date: Optional[str] = None,
    due_date: Optional[str] = None, priority: str = "normal", notes: str = "",
) -> int:
    """Add lp job.
    
    Parameters
    ----------
    title : Any
        title parameter.
    
    job_type : Any
        job_type parameter.
    
    requester : Any
        requester parameter.
    
    request_date : Any
        request_date parameter.
    
    due_date : Any
        due_date parameter.
    
    priority : Any
        priority parameter.
    
    notes : Any
        notes parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO lp_ebraille_job (title,job_type,requester,request_date,"
            "due_date,priority,notes) VALUES (?,?,?,?,?,?,?)",
            (title, job_type, requester, request_date, due_date, priority, notes),
        )
        new_id = int(cur.lastrowid)
    log_event("lp_ebraille", new_id, "CREATE", "SUCCESS", detail=f"Job created: {title}")
    return new_id


def update_lp_job(row_id: int, **fields: Any) -> None:
    """Update lp job.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    allowed = {"title", "job_type", "requester", "request_date", "due_date",
               "priority", "digitized", "formatted", "converted", "proofread",
               "delivered", "notes"}
    sql, vals = _build_update_sql("lp_ebraille_job", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_lp_job(row_id: int) -> None:
    """Delete lp job.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        conn.execute("DELETE FROM lp_ebraille_job WHERE id = ?", (row_id,))


# ── Tactile graphics jobs ─────────────────────────────────────────────────────

def list_tactile_jobs() -> list[dict[str, Any]]:
    """List tactile jobs.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM tactile_graphics_job ORDER BY created_at DESC"))


def get_tactile_job(row_id: int) -> Optional[dict[str, Any]]:
    """Get tactile job.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        rows = _rows(conn.execute("SELECT * FROM tactile_graphics_job WHERE id = ?", (row_id,)))
        return rows[0] if rows else None


def add_tactile_job(
    title: str, tactile_type: str,
    requester: str = "", request_date: Optional[str] = None,
    due_date: Optional[str] = None, priority: str = "normal", notes: str = "",
) -> int:
    """Add tactile job.
    
    Parameters
    ----------
    title : Any
        title parameter.
    
    tactile_type : Any
        tactile_type parameter.
    
    requester : Any
        requester parameter.
    
    request_date : Any
        request_date parameter.
    
    due_date : Any
        due_date parameter.
    
    priority : Any
        priority parameter.
    
    notes : Any
        notes parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO tactile_graphics_job (title,tactile_type,requester,request_date,"
            "due_date,priority,notes) VALUES (?,?,?,?,?,?,?)",
            (title, tactile_type, requester, request_date, due_date, priority, notes),
        )
        new_id = int(cur.lastrowid)
    log_event("tactile", new_id, "CREATE", "SUCCESS", detail=f"Job created: {title}")
    return new_id


def update_tactile_job(row_id: int, **fields: Any) -> None:
    """Update tactile job.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    allowed = {"title", "tactile_type", "requester", "request_date", "due_date",
               "priority", "designed", "produced", "qa_reviewed", "delivered", "notes"}
    sql, vals = _build_update_sql("tactile_graphics_job", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_tactile_job(row_id: int) -> None:
    """Delete tactile job.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        conn.execute("DELETE FROM tactile_graphics_job WHERE id = ?", (row_id,))


# ── File objects ──────────────────────────────────────────────────────────────

def list_file_objects() -> list[dict[str, Any]]:
    """List file objects.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM file_object ORDER BY created_at DESC"))


def get_file_object(file_id: int) -> Optional[dict[str, Any]]:
    """Get file object.
    
    Parameters
    ----------
    file_id : Any
        file_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        rows = _rows(conn.execute("SELECT * FROM file_object WHERE id = ?", (file_id,)))
        return rows[0] if rows else None


def ingest_file(
    source_path: str,
    file_use: str = "MASTER",
    format_name: str = "",
    format_version: str = "",
    encoding: str = "",
    extra_metadata: Optional[dict[str, Any]] = None,
    project_title: str = "",
    student_initials: str = "",
    school_name: str = "",
    grade_level: str = "",
    subject: str = "",
) -> int:
    """Copy a file into the artifact store (preferred) or job-files store, compute SHA-256.

    When *project_title* is supplied the file is placed under::

        artifacts/<project_title>/<student_initials>_<school_name>_Grade<grade_level>_<subject><ext>

    The database stores the **absolute** path so the record always resolves
    regardless of the working directory.  The legacy UUID-named copy in
    ``job_files/`` is still used when no project context is provided.
    """
    src = Path(source_path)
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")

    file_uuid = str(uuid.uuid4())

    if project_title:
        # ── Artifact-based storage ────────────────────────────────────────
        project_dir = ARTIFACTS_DIR / _sanitize_name(project_title)
        project_dir.mkdir(parents=True, exist_ok=True)

        name_parts: list[str] = []
        if student_initials:
            name_parts.append(_sanitize_name(student_initials))
        if school_name:
            name_parts.append(_sanitize_name(school_name))
        if grade_level:
            name_parts.append(f"Grade{_sanitize_name(grade_level)}")
        if subject:
            name_parts.append(_sanitize_name(subject))

        artifact_stem = "_".join(name_parts) if name_parts else file_uuid
        dest = project_dir / f"{artifact_stem}{src.suffix}"
        # Avoid silent overwrites — append short UUID on collision
        if dest.exists():
            dest = project_dir / f"{artifact_stem}_{file_uuid[:8]}{src.suffix}"
        stored_path_val = str(dest)  # absolute path
    else:
        # ── Legacy UUID-based storage in job_files/ ───────────────────────
        dest = FILES_DIR / f"{file_uuid}{src.suffix}"
        stored_path_val = dest.name  # relative name, resolved via FILES_DIR

    shutil.copy2(src, dest)
    checksum = _sha256(dest)
    size_bytes = dest.stat().st_size
    mime_type = mimetypes.guess_type(src.name)[0] or "application/octet-stream"

    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO file_object (uuid,original_name,stored_path,mime_type,size_bytes,"
            "checksum_sha256,file_use,format_name,format_version,encoding,extra_metadata) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (file_uuid, src.name, stored_path_val, mime_type, size_bytes, checksum,
             file_use, format_name, format_version, encoding,
             json.dumps(extra_metadata) if extra_metadata else None),
        )
        return int(cur.lastrowid)


def update_file_object(file_id: int, **fields: Any) -> None:
    """Update file object.
    
    Parameters
    ----------
    file_id : Any
        file_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    allowed = {"file_use", "format_name", "format_version", "encoding", "extra_metadata"}
    sql, vals = _build_update_sql("file_object", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [file_id])


def delete_file_object(file_id: int) -> None:
    """Delete file object.
    
    Parameters
    ----------
    file_id : Any
        file_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    row = get_file_object(file_id)
    if row:
        stored = FILES_DIR / row["stored_path"]
        stored.unlink(missing_ok=True)
    with get_conn() as conn:
        conn.execute("DELETE FROM file_object WHERE id = ?", (file_id,))


# ── Job file links ────────────────────────────────────────────────────────────

def link_file_to_job(
    file_object_id: int, job_type: str, job_id: int,
    step_key: Optional[str] = None, sequence_num: int = 0,
) -> int:
    """Link file to job.
    
    Parameters
    ----------
    file_object_id : Any
        file_object_id parameter.
    
    job_type : Any
        job_type parameter.
    
    job_id : Any
        job_id parameter.
    
    step_key : Any
        step_key parameter.
    
    sequence_num : Any
        sequence_num parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO job_file_link (file_object_id,job_type,job_id,step_key,sequence_num) "
            "VALUES (?,?,?,?,?)",
            (file_object_id, job_type, job_id, step_key, sequence_num),
        )
        return int(cur.lastrowid)


def list_files_for_job(job_type: str, job_id: int) -> list[dict[str, Any]]:
    """List files for job.
    
    Parameters
    ----------
    job_type : Any
        job_type parameter.
    
    job_id : Any
        job_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        return _rows(conn.execute("""
            SELECT fo.*, jfl.id AS link_id, jfl.step_key, jfl.sequence_num
            FROM file_object fo
            JOIN job_file_link jfl ON jfl.file_object_id = fo.id
            WHERE jfl.job_type = ? AND jfl.job_id = ?
            ORDER BY jfl.sequence_num, fo.created_at
        """, (job_type, job_id)))


def unlink_file_from_job(link_id: int) -> None:
    """Unlink file from job.
    
    Parameters
    ----------
    link_id : Any
        link_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        conn.execute("DELETE FROM job_file_link WHERE id = ?", (link_id,))


# ── Metadata events ───────────────────────────────────────────────────────────

def log_event(
    job_type: str, job_id: int, event_type: str,
    event_outcome: str = "SUCCESS",
    step_key: Optional[str] = None,
    file_object_id: Optional[int] = None,
    agent: str = "system",
    detail: str = "",
    extra_metadata: Optional[dict[str, Any]] = None,
) -> int:
    """Log event.
    
    Parameters
    ----------
    job_type : Any
        job_type parameter.
    
    job_id : Any
        job_id parameter.
    
    event_type : Any
        event_type parameter.
    
    event_outcome : Any
        event_outcome parameter.
    
    step_key : Any
        step_key parameter.
    
    file_object_id : Any
        file_object_id parameter.
    
    agent : Any
        agent parameter.
    
    detail : Any
        detail parameter.
    
    extra_metadata : Any
        extra_metadata parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO metadata_event (job_type,job_id,event_type,event_outcome,"
            "step_key,file_object_id,agent,detail,extra_metadata) VALUES (?,?,?,?,?,?,?,?,?)",
            (job_type, job_id, event_type, event_outcome, step_key, file_object_id,
             agent, detail, json.dumps(extra_metadata) if extra_metadata else None),
        )
        return int(cur.lastrowid)


def list_events_for_job(job_type: str, job_id: int) -> list[dict[str, Any]]:
    """List events for job.
    
    Parameters
    ----------
    job_type : Any
        job_type parameter.
    
    job_id : Any
        job_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        return _rows(conn.execute("""
            SELECT me.*, fo.original_name AS file_name
            FROM metadata_event me
            LEFT JOIN file_object fo ON fo.id = me.file_object_id
            WHERE me.job_type = ? AND me.job_id = ?
            ORDER BY me.event_datetime ASC
        """, (job_type, job_id)))


# ── Structural map ────────────────────────────────────────────────────────────

def add_struct_node(
    job_type: str, job_id: int, label: str,
    parent_id: Optional[int] = None, div_type: str = "section",
    order_num: int = 0, file_object_id: Optional[int] = None,
) -> int:
    """Add struct node.
    
    Parameters
    ----------
    job_type : Any
        job_type parameter.
    
    job_id : Any
        job_id parameter.
    
    label : Any
        label parameter.
    
    parent_id : Any
        parent_id parameter.
    
    div_type : Any
        div_type parameter.
    
    order_num : Any
        order_num parameter.
    
    file_object_id : Any
        file_object_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO structural_map_node (job_type,job_id,parent_id,label,"
            "div_type,order_num,file_object_id) VALUES (?,?,?,?,?,?,?)",
            (job_type, job_id, parent_id, label, div_type, order_num, file_object_id),
        )
        return int(cur.lastrowid)


def list_struct_nodes(job_type: str, job_id: int) -> list[dict[str, Any]]:
    """List struct nodes.
    
    Parameters
    ----------
    job_type : Any
        job_type parameter.
    
    job_id : Any
        job_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        return _rows(conn.execute("""
            SELECT sn.*, fo.original_name AS file_name
            FROM structural_map_node sn
            LEFT JOIN file_object fo ON fo.id = sn.file_object_id
            WHERE sn.job_type = ? AND sn.job_id = ?
            ORDER BY sn.order_num
        """, (job_type, job_id)))


def delete_struct_node(node_id: int) -> None:
    """Delete struct node.
    
    Parameters
    ----------
    node_id : Any
        node_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        conn.execute("DELETE FROM structural_map_node WHERE id = ?", (node_id,))


# ── Job metadata ──────────────────────────────────────────────────────────────

def set_job_metadata(job_type: str, job_id: int, meta_key: str, meta_value: str) -> None:
    """Set job metadata.
    
    Parameters
    ----------
    job_type : Any
        job_type parameter.
    
    job_id : Any
        job_id parameter.
    
    meta_key : Any
        meta_key parameter.
    
    meta_value : Any
        meta_value parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO job_metadata (job_type,job_id,meta_key,meta_value) VALUES (?,?,?,?)
            ON CONFLICT(job_type,job_id,meta_key) DO UPDATE SET
                meta_value = excluded.meta_value,
                updated_at = datetime('now')
        """, (job_type, job_id, meta_key, meta_value))


def get_job_metadata(job_type: str, job_id: int, meta_key: str) -> Optional[str]:
    """Get job metadata.
    
    Parameters
    ----------
    job_type : Any
        job_type parameter.
    
    job_id : Any
        job_id parameter.
    
    meta_key : Any
        meta_key parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        rows = _rows(conn.execute(
            "SELECT meta_value FROM job_metadata WHERE job_type=? AND job_id=? AND meta_key=?",
            (job_type, job_id, meta_key),
        ))
        return rows[0]["meta_value"] if rows else None


def list_job_metadata(job_type: str, job_id: int) -> dict[str, str]:
    """List job metadata.
    
    Parameters
    ----------
    job_type : Any
        job_type parameter.
    
    job_id : Any
        job_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        rows = _rows(conn.execute(
            "SELECT meta_key, meta_value FROM job_metadata "
            "WHERE job_type=? AND job_id=? ORDER BY meta_key",
            (job_type, job_id),
        ))
        return {r["meta_key"]: r["meta_value"] for r in rows}


def delete_job_metadata(job_type: str, job_id: int, meta_key: str) -> None:
    """Delete job metadata.
    
    Parameters
    ----------
    job_type : Any
        job_type parameter.
    
    job_id : Any
        job_id parameter.
    
    meta_key : Any
        meta_key parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM job_metadata WHERE job_type=? AND job_id=? AND meta_key=?",
            (job_type, job_id, meta_key),
        )


def list_distinct_metadata_keys() -> list[dict[str, Any]]:
    """Return all metadata keys in use with occurrence counts."""
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT meta_key, COUNT(*) AS usage_count "
            "FROM job_metadata GROUP BY meta_key ORDER BY usage_count DESC, meta_key"
        ))


def backfill_metadata_keys(approved_keys: list[str]) -> dict[str, Any]:
    """Normalize and backfill typo'd metadata keys into approved keys.

    Strategy:
    - For each non-approved key, find the closest approved key by normalized form.
    - Move data to the matched key.
    - When source and target already exist for the same job row, merge values.
    """
    if not approved_keys:
        return {"updated_rows": 0, "deleted_rows": 0, "mappings": {}, "skipped_keys": []}

    def _norm(k: str) -> str:
        """ norm.
        
        Parameters
        ----------
        k : Any
            k parameter.
        
        Returns
        -------
        Any
            Function result.
        
        """
        k = k.strip().lower().replace(" ", "_").replace("-", "_")
        return re.sub(r"[^a-z0-9_:]", "", k)

    approved_set = set(approved_keys)
    norm_to_key = {_norm(k): k for k in approved_keys}
    norm_candidates = list(norm_to_key.keys())

    with get_conn() as conn:
        distinct = _rows(conn.execute("SELECT DISTINCT meta_key FROM job_metadata ORDER BY meta_key"))

        mappings: dict[str, str] = {}
        skipped: list[str] = []

        for row in distinct:
            source = row["meta_key"]
            if source in approved_set:
                continue
            nsrc = _norm(source)

            if nsrc in norm_to_key:
                mappings[source] = norm_to_key[nsrc]
                continue

            closest = difflib.get_close_matches(nsrc, norm_candidates, n=1, cutoff=0.8)
            if closest:
                mappings[source] = norm_to_key[closest[0]]
            else:
                skipped.append(source)

        updated_rows = 0
        deleted_rows = 0

        for source, target in mappings.items():
            if source == target:
                continue

            rows = _rows(conn.execute(
                "SELECT id, job_type, job_id, meta_value FROM job_metadata WHERE meta_key=?",
                (source,),
            ))

            for r in rows:
                existing = _rows(conn.execute(
                    "SELECT id, meta_value FROM job_metadata "
                    "WHERE job_type=? AND job_id=? AND meta_key=?",
                    (r["job_type"], r["job_id"], target),
                ))

                if not existing:
                    conn.execute(
                        "UPDATE job_metadata SET meta_key=?, updated_at=datetime('now') WHERE id=?",
                        (target, r["id"]),
                    )
                    updated_rows += 1
                    continue

                tgt_id = existing[0]["id"]
                tgt_val = existing[0].get("meta_value") or ""
                src_val = r.get("meta_value") or ""

                merged = tgt_val
                if src_val and src_val not in tgt_val:
                    merged = f"{tgt_val} | {src_val}" if tgt_val else src_val
                    conn.execute(
                        "UPDATE job_metadata SET meta_value=?, updated_at=datetime('now') WHERE id=?",
                        (merged, tgt_id),
                    )
                    updated_rows += 1

                conn.execute("DELETE FROM job_metadata WHERE id=?", (r["id"],))
                deleted_rows += 1

        return {
            "updated_rows": updated_rows,
            "deleted_rows": deleted_rows,
            "mappings": mappings,
            "skipped_keys": skipped,
        }


# ── Step helpers ──────────────────────────────────────────────────────────────

_STEP_TABLES: dict[str, str] = {
    "braille": "braille_job",
    "lp_ebraille": "lp_ebraille_job",
    "tactile": "tactile_graphics_job",
}
_ALLOWED_STEPS: dict[str, list[str]] = {
    "braille": ["digitized", "formatted", "brailled", "proofread", "delivered"],
    "lp_ebraille": ["digitized", "formatted", "converted", "proofread", "delivered"],
    "tactile": ["designed", "produced", "qa_reviewed", "delivered"],
}


def complete_step(job_type: str, job_id: int, step_key: str, agent: str = "user") -> None:
    """Complete step.
    
    Parameters
    ----------
    job_type : Any
        job_type parameter.
    
    job_id : Any
        job_id parameter.
    
    step_key : Any
        step_key parameter.
    
    agent : Any
        agent parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    table = _STEP_TABLES.get(job_type)
    if not table or step_key not in _ALLOWED_STEPS.get(job_type, []):
        raise ValueError(f"Unknown step '{step_key}' for job type '{job_type}'")
    with get_conn() as conn:
        conn.execute(
            f"UPDATE {table} SET {step_key} = 1, updated_at = datetime('now') WHERE id = ?",  # noqa: S608
            (job_id,),
        )
    log_event(job_type, job_id, "STEP_COMPLETE", "SUCCESS",
              step_key=step_key, agent=agent, detail=f"Step '{step_key}' marked complete")


def revert_step(
    job_type: str, job_id: int, step_key: str,
    agent: str = "user", reason: str = "",
) -> None:
    """Revert step.
    
    Parameters
    ----------
    job_type : Any
        job_type parameter.
    
    job_id : Any
        job_id parameter.
    
    step_key : Any
        step_key parameter.
    
    agent : Any
        agent parameter.
    
    reason : Any
        reason parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    table = _STEP_TABLES.get(job_type)
    if not table or step_key not in _ALLOWED_STEPS.get(job_type, []):
        raise ValueError(f"Unknown step '{step_key}' for job type '{job_type}'")
    with get_conn() as conn:
        conn.execute(
            f"UPDATE {table} SET {step_key} = 0, updated_at = datetime('now') WHERE id = ?",  # noqa: S608
            (job_id,),
        )
    log_event(job_type, job_id, "STEP_REVERT", "WARNING",
              step_key=step_key, agent=agent,
              detail=f"Step '{step_key}' reverted" + (f": {reason}" if reason else ""))


# ── Lookup tables ─────────────────────────────────────────────────────────────

def list_material_categories(
    section: Optional[str] = None, active_only: bool = True,
) -> list[dict[str, Any]]:
    """List material categories.
    
    Parameters
    ----------
    section : Any
        section parameter.
    
    active_only : Any
        active_only parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        filters: list[str] = []
        params: list[Any] = []
        if section:
            filters.append("section = ?")
            params.append(section)
        if active_only:
            filters.append("active = 1")
        where = ("WHERE " + " AND ".join(filters)) if filters else ""
        return _rows(conn.execute(
            f"SELECT * FROM material_category {where} ORDER BY section, sort_order, label",  # noqa: S608
            params,
        ))


def add_material_category(
    section: str, value: str, label: str, sort_order: int = 0,
) -> int:
    """Add material category.
    
    Parameters
    ----------
    section : Any
        section parameter.
    
    value : Any
        value parameter.
    
    label : Any
        label parameter.
    
    sort_order : Any
        sort_order parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO material_category (section,value,label,sort_order) VALUES (?,?,?,?)",
            (section, value, label, sort_order),
        )
        return int(cur.lastrowid)


def update_material_category(row_id: int, **fields: Any) -> None:
    """Update material category.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    allowed = {"section", "value", "label", "sort_order", "active"}
    sql, vals = _build_update_sql("material_category", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def set_material_category_active(row_id: int, active: int) -> None:
    """Set material category active.
    
    Parameters
    ----------
    row_id : Any
        row_id parameter.
    
    active : Any
        active parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        conn.execute(
            "UPDATE material_category SET active=?, updated_at=datetime('now') WHERE id=?",
            (active, row_id),
        )


def delete_material_category(row_id: int) -> None:
    """Soft-delete a material category (sets active=0)."""
    set_material_category_active(row_id, 0)


def list_workflow_steps(
    job_type: Optional[str] = None, active_only: bool = True,
) -> list[dict[str, Any]]:
    """List workflow steps.
    
    Parameters
    ----------
    job_type : Any
        job_type parameter.
    
    active_only : Any
        active_only parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        filters: list[str] = []
        params: list[Any] = []
        if job_type:
            filters.append("job_type = ?")
            params.append(job_type)
        if active_only:
            filters.append("active = 1")
        where = ("WHERE " + " AND ".join(filters)) if filters else ""
        return _rows(conn.execute(
            f"SELECT * FROM workflow_step {where} ORDER BY job_type, sort_order, label",  # noqa: S608
            params,
        ))


def add_workflow_step(
    job_type: str, step_key: str, label: str,
    description: str = "", sort_order: int = 0,
) -> int:
    """Add workflow step.
    
    Parameters
    ----------
    job_type : Any
        job_type parameter.
    
    step_key : Any
        step_key parameter.
    
    label : Any
        label parameter.
    
    description : Any
        description parameter.
    
    sort_order : Any
        sort_order parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO workflow_step (job_type,step_key,label,description,sort_order) "
            "VALUES (?,?,?,?,?)",
            (job_type, step_key, label, description, sort_order),
        )
        return int(cur.lastrowid)


def update_workflow_step(row_id: int, **fields: Any) -> None:
    """Update a workflow step record.  workflow_step.updated_at is guaranteed by schema/migration."""
    allowed = {"job_type", "step_key", "label", "description", "sort_order", "active"}
    sql, vals = _build_update_sql("workflow_step", fields, allowed, has_updated_at=True)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def set_workflow_step_active(row_id: int, active: int) -> None:
    """Enable or disable a workflow step.  Uses updated_at which now exists after migration."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE workflow_step SET active=?, updated_at=datetime('now') WHERE id=?",
            (active, row_id),
        )


def delete_workflow_step(row_id: int) -> None:
    """Soft-delete a workflow step (sets active=0)."""
    set_workflow_step_active(row_id, 0)


# ── QA runs ───────────────────────────────────────────────────────────────────

def log_qa_run(
    tool_name: str, command: str,
    success: bool, output: str,
    job_type: Optional[str] = None, job_id: Optional[int] = None,
) -> int:
    """Log qa run.
    
    Parameters
    ----------
    tool_name : Any
        tool_name parameter.
    
    command : Any
        command parameter.
    
    success : Any
        success parameter.
    
    output : Any
        output parameter.
    
    job_type : Any
        job_type parameter.
    
    job_id : Any
        job_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO qa_run (tool_name,command,job_type,job_id,success,output) "
            "VALUES (?,?,?,?,?,?)",
            (tool_name, command, job_type, job_id, 1 if success else 0, output),
        )
        return int(cur.lastrowid)


def list_qa_runs(
    tool_name: Optional[str] = None, limit: int = 100,
) -> list[dict[str, Any]]:
    """List qa runs.
    
    Parameters
    ----------
    tool_name : Any
        tool_name parameter.
    
    limit : Any
        limit parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        if tool_name:
            return _rows(conn.execute(
                "SELECT * FROM qa_run WHERE tool_name=? ORDER BY ran_at DESC LIMIT ?",
                (tool_name, limit),
            ))
        return _rows(conn.execute(
            "SELECT * FROM qa_run ORDER BY ran_at DESC LIMIT ?", (limit,),
        ))


# ── Pipeline runs ─────────────────────────────────────────────────────────────

def start_pipeline_run(pipeline_name: str) -> int:
    """Start pipeline run.
    
    Parameters
    ----------
    pipeline_name : Any
        pipeline_name parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO pipeline_run (pipeline_name,status) VALUES (?,?)",
            (pipeline_name, "running"),
        )
        return int(cur.lastrowid)


def finish_pipeline_run(run_id: int, status: str = "completed") -> None:
    """Finish pipeline run.
    
    Parameters
    ----------
    run_id : Any
        run_id parameter.
    
    status : Any
        status parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        conn.execute(
            "UPDATE pipeline_run SET status=?, finished_at=datetime('now') WHERE id=?",
            (status, run_id),
        )


def log_pipeline_step(
    pipeline_run_id: int, step_name: str, tool: str,
    command: str, success: bool, output: str,
) -> int:
    """Log pipeline step.
    
    Parameters
    ----------
    pipeline_run_id : Any
        pipeline_run_id parameter.
    
    step_name : Any
        step_name parameter.
    
    tool : Any
        tool parameter.
    
    command : Any
        command parameter.
    
    success : Any
        success parameter.
    
    output : Any
        output parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO pipeline_step_run (pipeline_run_id,step_name,tool,command,success,output) "
            "VALUES (?,?,?,?,?,?)",
            (pipeline_run_id, step_name, tool, command, 1 if success else 0, output),
        )
        return int(cur.lastrowid)


def list_pipeline_runs(limit: int = 50) -> list[dict[str, Any]]:
    """List pipeline runs.
    
    Parameters
    ----------
    limit : Any
        limit parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT * FROM pipeline_run ORDER BY started_at DESC LIMIT ?", (limit,),
        ))


def list_pipeline_step_runs(pipeline_run_id: int) -> list[dict[str, Any]]:
    """List pipeline step runs.
    
    Parameters
    ----------
    pipeline_run_id : Any
        pipeline_run_id parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT * FROM pipeline_step_run WHERE pipeline_run_id=? ORDER BY ran_at",
            (pipeline_run_id,),
        ))


# ── Backup log ────────────────────────────────────────────────────────────────

def log_backup(backup_path: str, size_bytes: int, trigger: str = "scheduled",
               status: str = "ok") -> int:
    """Record a completed backup in the backup_log table."""
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO backup_log (backup_path, size_bytes, trigger, status) VALUES (?,?,?,?)",
            (backup_path, size_bytes, trigger, status),
        )
        return int(cur.lastrowid)


def list_backup_log(limit: int = 50) -> list[dict[str, Any]]:
    """Return recent backup log entries, newest first."""
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT * FROM backup_log ORDER BY created_at DESC LIMIT ?", (limit,),
        ))
