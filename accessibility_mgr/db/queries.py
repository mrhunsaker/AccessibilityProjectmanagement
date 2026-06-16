"""
Data access layer — ALL SQL lives here.

Every public function uses parameterised queries ('?' placeholders).
No SQL strings are constructed outside this module.

Changes applied (see fix_specs.json):
  FIX-001  update_* functions now log FIELD_UPDATE events before returning.
  FIX-002  delete_* functions now log DELETE events before executing.
  FIX-007  'print' added to _STEP_TABLES / _ALLOWED_STEPS; get_print_job added.
  FIX-009  search_all() replaces in-memory Python filtering.
  FIX-010  Student CRUD + list_jobs_for_student added.
  FIX-015  report_jobs() added.
  FIX-016  Delivery columns added to allowed sets for all update functions.
  FIX-017  preview_backfill_metadata_keys() added.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import difflib
import re
import sqlite3
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
    "list_print_jobs", "get_print_job", "add_print_job", "update_print_job", "delete_print_job",
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
    "list_distinct_metadata_keys", "backfill_metadata_keys", "preview_backfill_metadata_keys",
    # Lookup tables
    "list_material_categories", "add_material_category", "update_material_category",
    "set_material_category_active", "delete_material_category",
    "list_workflow_steps", "add_workflow_step", "update_workflow_step",
    "set_workflow_step_active", "delete_workflow_step",
    # Step helpers
    "complete_step", "revert_step",
    # Delivery helper
    "record_delivery",
    # QA
    "log_qa_run", "list_qa_runs",
    # Pipeline
    "start_pipeline_run", "finish_pipeline_run", "log_pipeline_step",
    "list_pipeline_runs", "list_pipeline_step_runs",
    # Backup log
    "log_backup", "list_backup_log",
    # Students
    "list_students", "get_student", "add_student", "update_student", "delete_student",
    "list_jobs_for_student", "count_jobs_for_students",
    "list_students_page",
    # Search & reports
    "search_all", "report_jobs",
    # Paths
    "ARTIFACTS_DIR", "FILES_DIR", "PRINTS_DIR",
]


# ── Internal helpers ──────────────────────────────────────────────────────────

_TABLES_WITH_UPDATED_AT = {
    "filament", "braille_paper", "electronics",
    "printer", "embosser",
    "print_job", "braille_job", "lp_ebraille_job", "tactile_graphics_job",
    "file_object", "job_metadata", "material_category", "workflow_step",
    "student",
}

_SAFE_TABLES = _TABLES_WITH_UPDATED_AT | {"structural_map_node"}


def _sanitize_name(value: str) -> str:
    """Strip characters unsafe for file/directory names."""
    cleaned = re.sub(r"[^\w\-]", "", value.replace(" ", ""))
    return cleaned[:60]


def _rows(cur: Any) -> list[dict[str, Any]]:
    cols = [c[0] for c in cur.description]
    return [{cols[i]: row[i] for i in range(len(cols))} for row in cur.fetchall()]


def _build_update_sql(
    table: str,
    fields: dict[str, Any],
    allowed: set[str],
    has_updated_at: bool = True,
) -> tuple[str, list[Any]]:
    if table not in _SAFE_TABLES:
        raise ValueError(f"Disallowed table '{table}'")
    safe = {k: v for k, v in fields.items() if k in allowed}
    if not safe:
        raise ValueError(f"No valid fields to update in '{table}'")
    sets = ", ".join(f"{c} = ?" for c in safe)
    ts = ", updated_at = datetime('now')" if has_updated_at else ""
    return f"UPDATE {table} SET {sets}{ts} WHERE id = ?", list(safe.values())  # noqa: S608 - table/columns are validated against allow-lists.


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _delete_job_orphans(conn: sqlite3.Connection, job_type: str, job_id: int) -> None:
    """Remove child rows in polymorphic tables after a job is deleted."""
    conn.execute(
        "DELETE FROM job_file_link WHERE job_type = ? AND job_id = ?", (job_type, job_id)
    )
    conn.execute(
        "DELETE FROM job_metadata WHERE job_type = ? AND job_id = ?", (job_type, job_id)
    )
    conn.execute(
        "DELETE FROM structural_map_node WHERE job_type = ? AND job_id = ?", (job_type, job_id)
    )
    # metadata_event rows are preserved as a permanent audit trail.


# ── Filament ──────────────────────────────────────────────────────────────────

def list_filaments() -> list[dict[str, Any]]:
    """Return all filament records ordered by brand and colour."""
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM filament ORDER BY brand, color"))


def add_filament(
    brand: str, color: str, filament_type: str,
    diameter_mm: float = 1.75, quantity_g: float = 0,
    cost_per_kg: Optional[float] = None, supplier: str = "", notes: str = "",
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO filament (brand,color,filament_type,diameter_mm,quantity_g,"
            "cost_per_kg,supplier,notes) VALUES (?,?,?,?,?,?,?,?)",
            (brand, color, filament_type, diameter_mm, quantity_g, cost_per_kg, supplier, notes),
        )
        return int(cur.lastrowid)


def update_filament(row_id: int, **fields: Any) -> None:
    allowed = {"brand", "color", "filament_type", "diameter_mm", "quantity_g",
               "cost_per_kg", "supplier", "notes"}
    sql, vals = _build_update_sql("filament", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_filament(row_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM filament WHERE id = ?", (row_id,))


def deduct_filament(row_id: int, grams: float) -> None:
    """Deduct *grams* from filament stock.

    FUN-011: grams must be strictly positive.  Zero is a no-op; negative values
    would silently *add* stock (MAX(0, qty - negative) = qty + |negative|).
    """
    if grams <= 0:
        raise ValueError(f"grams must be positive, got {grams!r}")
    with get_conn() as conn:
        conn.execute(
            "UPDATE filament SET quantity_g = MAX(0, quantity_g - ?), "
            "updated_at = datetime('now') WHERE id = ?",
            (grams, row_id),
        )


# ── Paper ─────────────────────────────────────────────────────────────────────

def list_paper() -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM braille_paper ORDER BY paper_type"))


def add_paper(
    paper_type: str, quantity: int,
    size: Optional[str] = None, label_type: Optional[str] = None,
    supplier: str = "", notes: str = "",
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO braille_paper (paper_type,size,label_type,quantity,supplier,notes) "
            "VALUES (?,?,?,?,?,?)",
            (paper_type, size, label_type, quantity, supplier, notes),
        )
        return int(cur.lastrowid)


def update_paper(row_id: int, **fields: Any) -> None:
    allowed = {"paper_type", "size", "label_type", "quantity", "supplier", "notes"}
    sql, vals = _build_update_sql("braille_paper", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_paper(row_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM braille_paper WHERE id = ?", (row_id,))


# ── Electronics ───────────────────────────────────────────────────────────────

def list_electronics(category: Optional[str] = None) -> list[dict[str, Any]]:
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
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO electronics (category,name,brand,spec,quantity,unit,"
            "cost_each,supplier,notes) VALUES (?,?,?,?,?,?,?,?,?)",
            (category, name, brand, spec, quantity, unit, cost_each, supplier, notes),
        )
        return int(cur.lastrowid)


def update_electronic(row_id: int, **fields: Any) -> None:
    allowed = {"category", "name", "brand", "spec", "quantity", "unit",
               "cost_each", "supplier", "notes"}
    sql, vals = _build_update_sql("electronics", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_electronic(row_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM electronics WHERE id = ?", (row_id,))


# ── Printers ──────────────────────────────────────────────────────────────────

def list_printers() -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM printer ORDER BY name"))


def add_printer(name: str, model: str = "", notes: str = "") -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO printer (name,model,notes) VALUES (?,?,?)", (name, model, notes),
        )
        return int(cur.lastrowid)


def update_printer(row_id: int, **fields: Any) -> None:
    allowed = {"name", "model", "notes"}
    sql, vals = _build_update_sql("printer", fields, allowed, has_updated_at=True)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_printer(row_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM printer WHERE id = ?", (row_id,))


# ── Embossers ─────────────────────────────────────────────────────────────────

def list_embossers() -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM embosser ORDER BY name"))


def add_embosser(name: str, model: str = "", paper_type: str = "", notes: str = "") -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO embosser (name,model,paper_type,notes) VALUES (?,?,?,?)",
            (name, model, paper_type, notes),
        )
        return int(cur.lastrowid)


def update_embosser(row_id: int, **fields: Any) -> None:
    allowed = {"name", "model", "paper_type", "notes"}
    sql, vals = _build_update_sql("embosser", fields, allowed, has_updated_at=True)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_embosser(row_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM embosser WHERE id = ?", (row_id,))


# ── Print jobs ────────────────────────────────────────────────────────────────

def list_print_jobs(
    limit: Optional[int] = None,
    offset: int = 0,
    search: Optional[str] = None,
    priority: Optional[str] = None,
) -> list[dict[str, Any]]:
    filters: list[str] = []
    params: list[Any] = []
    if search:
        term = f"%{search}%"
        filters.append("(pj.object_name LIKE ? OR pj.requester LIKE ?)")
        params.extend([term, term])
    if priority:
        filters.append("pj.priority = ?")
        params.append(priority)
    where = ("WHERE " + " AND ".join(filters)) if filters else ""
    with get_conn() as conn:
        sql = f"""
            SELECT pj.*,
                   p.name  AS printer_name,
                   f.brand || ' ' || f.color || ' ' || f.filament_type AS filament_desc
            FROM print_job pj
            LEFT JOIN printer  p ON p.id = pj.printer_id
            LEFT JOIN filament f ON f.id = pj.filament_id
            {where}
            ORDER BY pj.printed_at DESC
        """  # noqa: S608 - where fragments are built from fixed SQL; values are parameterised.
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, max(0, offset)])
        return _rows(conn.execute(sql, params))


def get_print_job(row_id: int) -> Optional[dict[str, Any]]:
    """Fetch a single print job by id (FIX-001: needed for pre-update snapshot)."""
    with get_conn() as conn:
        rows = _rows(conn.execute("""
            SELECT pj.*,
                   p.name  AS printer_name,
                   f.brand || ' ' || f.color || ' ' || f.filament_type AS filament_desc
            FROM print_job pj
            LEFT JOIN printer  p ON p.id = pj.printer_id
            LEFT JOIN filament f ON f.id = pj.filament_id
            WHERE pj.id = ?
        """, (row_id,)))
        return rows[0] if rows else None


def add_print_job(
    printer_id: int, filament_id: Optional[int], filament_used_g: float,
    file_source_path: Optional[str] = None, successful: int = 1,
    failure_reason: Optional[str] = None, object_name: str = "",
    requester: str = "", request_date: Optional[str] = None, notes: str = "",
    student_id: Optional[int] = None,
) -> int:
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
            "file_name,successful,failure_reason,object_name,requester,request_date,notes,student_id) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (printer_id, filament_id, filament_used_g, file_path, file_name,
             successful, failure_reason, object_name, requester, request_date, notes, student_id),
        )
        new_id = int(cur.lastrowid)

    if filament_id and filament_used_g:
        deduct_filament(filament_id, filament_used_g)

    log_event("print", new_id, "CREATE", "SUCCESS",
              detail=f"Print job created: {object_name or file_name or 'unnamed'}")
    return new_id


def update_print_job(row_id: int, **fields: Any) -> None:
    """Update a print job and log a FIELD_UPDATE audit event (FIX-001, FIX-016)."""
    # FIX-001: snapshot before update
    old = get_print_job(row_id)
    allowed = {
        "printer_id", "filament_id", "filament_used_g", "successful",
        "failure_reason", "object_name", "requester", "request_date", "notes",
        "student_id",
        # FIX-007: step columns
        "designed", "sliced", "printed", "inspected", "delivered",
        # FIX-016: delivery columns
        "delivery_date", "delivery_method", "delivery_recipient", "delivery_notes",
    }
    sql, vals = _build_update_sql("print_job", fields, allowed, has_updated_at=True)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])
    # FIX-001: log what changed
    log_event(
        "print", row_id, "FIELD_UPDATE", "SUCCESS",
        agent="system",
        detail=f"Updated fields: {list(fields.keys())}",
        extra_metadata={
            "changed_fields": list(fields.keys()),
            "previous_values": {k: old.get(k) for k in fields if old},
        },
    )


def delete_print_job(row_id: int) -> None:
    """Delete a print job, logging a DELETE audit event first (FIX-002)."""
    old = get_print_job(row_id)
    if old:
        log_event(
            "print", row_id, "DELETE", "SUCCESS",
            agent="system",
            detail=f"Print job deleted: {old.get('object_name') or old.get('file_name') or 'unnamed'}",
            extra_metadata={k: old.get(k) for k in
                            ["object_name", "printer_id", "filament_used_g", "successful", "printed_at"]},
        )
    with get_conn() as conn:
        conn.execute("DELETE FROM print_job WHERE id = ?", (row_id,))
        _delete_job_orphans(conn, "print", row_id)


# ── Braille jobs ──────────────────────────────────────────────────────────────

def list_braille_jobs(
    limit: Optional[int] = None,
    offset: int = 0,
    search: Optional[str] = None,
    braille_type: Optional[str] = None,
    priority: Optional[str] = None,
) -> list[dict[str, Any]]:
    filters: list[str] = []
    params: list[Any] = []
    if search:
        term = f"%{search}%"
        filters.append("(bj.title LIKE ? OR bj.requester LIKE ?)")
        params.extend([term, term])
    if braille_type:
        filters.append("bj.braille_type = ?")
        params.append(braille_type)
    if priority:
        filters.append("bj.priority = ?")
        params.append(priority)
    where = ("WHERE " + " AND ".join(filters)) if filters else ""
    with get_conn() as conn:
        sql = f"""
            SELECT bj.*, e.name AS embosser_name, e.paper_type AS embosser_paper_type
            FROM braille_job bj
            LEFT JOIN embosser e ON e.id = bj.embosser_id
            {where}
            ORDER BY bj.created_at DESC
        """  # noqa: S608 - where fragments are built from fixed SQL; values are parameterised.
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, max(0, offset)])
        return _rows(conn.execute(sql, params))


def get_braille_job(row_id: int) -> Optional[dict[str, Any]]:
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
    student_id: Optional[int] = None,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO braille_job (title,braille_type,embosser_id,requester,request_date,"
            "due_date,priority,notes,student_id) VALUES (?,?,?,?,?,?,?,?,?)",
            (title, braille_type, embosser_id, requester, request_date, due_date, priority,
             notes, student_id),
        )
        new_id = int(cur.lastrowid)
    log_event("braille", new_id, "CREATE", "SUCCESS", detail=f"Job created: {title}")
    return new_id


def update_braille_job(row_id: int, **fields: Any) -> None:
    """Update a braille job and log a FIELD_UPDATE audit event (FIX-001, FIX-016)."""
    old = get_braille_job(row_id)
    allowed = {
        "title", "braille_type", "embosser_id", "requester", "request_date", "due_date",
        "priority", "digitized", "formatted", "brailled", "proofread", "delivered",
        "notes", "student_id",
        # FIX-016: delivery columns
        "delivery_date", "delivery_method", "delivery_recipient", "delivery_notes",
    }
    sql, vals = _build_update_sql("braille_job", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])
    log_event(
        "braille", row_id, "FIELD_UPDATE", "SUCCESS",
        agent="system",
        detail=f"Updated fields: {list(fields.keys())}",
        extra_metadata={
            "changed_fields": list(fields.keys()),
            "previous_values": {k: old.get(k) for k in fields if old},
        },
    )


def delete_braille_job(row_id: int) -> None:
    """Delete a braille job, logging a DELETE audit event first (FIX-002)."""
    old = get_braille_job(row_id)
    if old:
        log_event(
            "braille", row_id, "DELETE", "SUCCESS",
            agent="system",
            detail=f"Job deleted: {old.get('title', '')}",
            extra_metadata={k: old.get(k) for k in
                            ["title", "braille_type", "requester", "priority", "created_at"]},
        )
    with get_conn() as conn:
        conn.execute("DELETE FROM braille_job WHERE id = ?", (row_id,))
        _delete_job_orphans(conn, "braille", row_id)


# ── LP/eBraille jobs ──────────────────────────────────────────────────────────

def list_lp_jobs(
    job_type: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
    search: Optional[str] = None,
    priority: Optional[str] = None,
) -> list[dict[str, Any]]:
    filters: list[str] = []
    params: list[Any] = []
    if job_type:
        filters.append("job_type = ?")
        params.append(job_type)
    if search:
        term = f"%{search}%"
        filters.append("(title LIKE ? OR requester LIKE ?)")
        params.extend([term, term])
    if priority:
        filters.append("priority = ?")
        params.append(priority)
    where = ("WHERE " + " AND ".join(filters)) if filters else ""
    with get_conn() as conn:
        sql = f"SELECT * FROM lp_ebraille_job {where} ORDER BY created_at DESC"  # noqa: S608
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, max(0, offset)])
        return _rows(conn.execute(sql, params))


def get_lp_job(row_id: int) -> Optional[dict[str, Any]]:
    with get_conn() as conn:
        rows = _rows(conn.execute("SELECT * FROM lp_ebraille_job WHERE id = ?", (row_id,)))
        return rows[0] if rows else None


def add_lp_job(
    title: str, job_type: str,
    requester: str = "", request_date: Optional[str] = None,
    due_date: Optional[str] = None, priority: str = "normal", notes: str = "",
    student_id: Optional[int] = None,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO lp_ebraille_job (title,job_type,requester,request_date,"
            "due_date,priority,notes,student_id) VALUES (?,?,?,?,?,?,?,?)",
            (title, job_type, requester, request_date, due_date, priority, notes, student_id),
        )
        new_id = int(cur.lastrowid)
    log_event("lp_ebraille", new_id, "CREATE", "SUCCESS", detail=f"Job created: {title}")
    return new_id


def update_lp_job(row_id: int, **fields: Any) -> None:
    """Update an LP/eBraille job and log a FIELD_UPDATE audit event (FIX-001, FIX-016)."""
    old = get_lp_job(row_id)
    allowed = {
        "title", "job_type", "requester", "request_date", "due_date",
        "priority", "digitized", "formatted", "converted", "proofread",
        "delivered", "notes", "student_id",
        # FIX-016
        "delivery_date", "delivery_method", "delivery_recipient", "delivery_notes",
    }
    sql, vals = _build_update_sql("lp_ebraille_job", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])
    log_event(
        "lp_ebraille", row_id, "FIELD_UPDATE", "SUCCESS",
        agent="system",
        detail=f"Updated fields: {list(fields.keys())}",
        extra_metadata={
            "changed_fields": list(fields.keys()),
            "previous_values": {k: old.get(k) for k in fields if old},
        },
    )


def delete_lp_job(row_id: int) -> None:
    """Delete an LP/eBraille job, logging a DELETE audit event first (FIX-002)."""
    old = get_lp_job(row_id)
    if old:
        log_event(
            "lp_ebraille", row_id, "DELETE", "SUCCESS",
            agent="system",
            detail=f"Job deleted: {old.get('title', '')}",
            extra_metadata={k: old.get(k) for k in
                            ["title", "job_type", "requester", "priority", "created_at"]},
        )
    with get_conn() as conn:
        conn.execute("DELETE FROM lp_ebraille_job WHERE id = ?", (row_id,))
        _delete_job_orphans(conn, "lp_ebraille", row_id)


# ── Tactile graphics jobs ─────────────────────────────────────────────────────

def list_tactile_jobs(
    limit: Optional[int] = None,
    offset: int = 0,
    search: Optional[str] = None,
    tactile_type: Optional[str] = None,
    priority: Optional[str] = None,
) -> list[dict[str, Any]]:
    filters: list[str] = []
    params: list[Any] = []
    if search:
        term = f"%{search}%"
        filters.append("(title LIKE ? OR requester LIKE ?)")
        params.extend([term, term])
    if tactile_type:
        filters.append("tactile_type = ?")
        params.append(tactile_type)
    if priority:
        filters.append("priority = ?")
        params.append(priority)
    where = ("WHERE " + " AND ".join(filters)) if filters else ""
    with get_conn() as conn:
        sql = f"SELECT * FROM tactile_graphics_job {where} ORDER BY created_at DESC"  # noqa: S608
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, max(0, offset)])
        return _rows(conn.execute(sql, params))


def get_tactile_job(row_id: int) -> Optional[dict[str, Any]]:
    with get_conn() as conn:
        rows = _rows(conn.execute("SELECT * FROM tactile_graphics_job WHERE id = ?", (row_id,)))
        return rows[0] if rows else None


def add_tactile_job(
    title: str, tactile_type: str,
    requester: str = "", request_date: Optional[str] = None,
    due_date: Optional[str] = None, priority: str = "normal", notes: str = "",
    student_id: Optional[int] = None,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO tactile_graphics_job (title,tactile_type,requester,request_date,"
            "due_date,priority,notes,student_id) VALUES (?,?,?,?,?,?,?,?)",
            (title, tactile_type, requester, request_date, due_date, priority, notes, student_id),
        )
        new_id = int(cur.lastrowid)
    log_event("tactile", new_id, "CREATE", "SUCCESS", detail=f"Job created: {title}")
    return new_id


def update_tactile_job(row_id: int, **fields: Any) -> None:
    """Update a tactile job and log a FIELD_UPDATE audit event (FIX-001, FIX-016)."""
    old = get_tactile_job(row_id)
    allowed = {
        "title", "tactile_type", "requester", "request_date", "due_date",
        "priority", "designed", "produced", "qa_reviewed", "delivered",
        "notes", "student_id",
        # FIX-016
        "delivery_date", "delivery_method", "delivery_recipient", "delivery_notes",
    }
    sql, vals = _build_update_sql("tactile_graphics_job", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])
    log_event(
        "tactile", row_id, "FIELD_UPDATE", "SUCCESS",
        agent="system",
        detail=f"Updated fields: {list(fields.keys())}",
        extra_metadata={
            "changed_fields": list(fields.keys()),
            "previous_values": {k: old.get(k) for k in fields if old},
        },
    )


def delete_tactile_job(row_id: int) -> None:
    """Delete a tactile job, logging a DELETE audit event first (FIX-002)."""
    old = get_tactile_job(row_id)
    if old:
        log_event(
            "tactile", row_id, "DELETE", "SUCCESS",
            agent="system",
            detail=f"Job deleted: {old.get('title', '')}",
            extra_metadata={k: old.get(k) for k in
                            ["title", "tactile_type", "requester", "priority", "created_at"]},
        )
    with get_conn() as conn:
        conn.execute("DELETE FROM tactile_graphics_job WHERE id = ?", (row_id,))
        _delete_job_orphans(conn, "tactile", row_id)


# ── File objects ──────────────────────────────────────────────────────────────

def list_file_objects(
    limit: Optional[int] = None,
    offset: int = 0,
) -> list[dict[str, Any]]:
    with get_conn() as conn:
        sql = "SELECT * FROM file_object ORDER BY created_at DESC"
        params: list[Any] = []
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, max(0, offset)])
        return _rows(conn.execute(sql, params))


def get_file_object(file_id: int) -> Optional[dict[str, Any]]:
    with get_conn() as conn:
        rows = _rows(conn.execute("SELECT * FROM file_object WHERE id = ?", (file_id,)))
        return rows[0] if rows else None


def ingest_file(
    source_path: str,
    file_use: str = "ORIGINAL",
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
    """Copy a file into the artifact store, compute SHA-256, and create a file_object record.

    SEC-004 / FUN-023: the *source_path* must exist and must resolve to a path
    inside FILES_DIR (the staging area).  This prevents callers from staging
    arbitrary files from anywhere on the filesystem into the artifact store.
    """
    src = Path(source_path).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")

    # SEC-004: ensure source resolves inside the permitted staging directory
    try:
        src.relative_to(FILES_DIR.resolve())
    except ValueError:
        raise PermissionError(
            f"ingest_file: source '{src}' is outside the permitted staging directory "
            f"'{FILES_DIR}'.  Stage files via the upload handler before ingesting."
        )

    file_uuid = str(uuid.uuid4())

    if project_title:
        safe_project_title = _sanitize_name(project_title) or file_uuid[:8]
        project_dir = ARTIFACTS_DIR / safe_project_title
        project_dir.mkdir(parents=True, exist_ok=True)

        name_parts: list[str] = []
        if student_initials:
            cleaned = _sanitize_name(student_initials)
            if cleaned:
                name_parts.append(cleaned)
        if school_name:
            cleaned = _sanitize_name(school_name)
            if cleaned:
                name_parts.append(cleaned)
        if grade_level:
            cleaned = _sanitize_name(grade_level)
            if cleaned:
                name_parts.append(f"Grade{cleaned}")
        if subject:
            cleaned = _sanitize_name(subject)
            if cleaned:
                name_parts.append(cleaned)

        artifact_stem = "_".join(name_parts) or file_uuid[:8]
        max_path_len = 240

        # Keep destination paths safely below typical filesystem path limits.
        while len(str(project_dir / f"{artifact_stem}{src.suffix}")) > max_path_len and len(artifact_stem) > 16:
            artifact_stem = artifact_stem[:-8]

        if len(f"{artifact_stem}{src.suffix}") > 255:
            raise ValueError("Artifact file name exceeds filesystem component limits")

        dest = project_dir / f"{artifact_stem}{src.suffix}"
        if len(str(dest)) > max_path_len:
            raise ValueError(
                "Artifact destination path is too long; shorten project or metadata values"
            )
        if dest.exists():
            dest = project_dir / f"{artifact_stem}_{file_uuid[:8]}{src.suffix}"
            if len(str(dest)) > max_path_len:
                raise ValueError(
                    "Artifact destination path is too long after collision handling"
                )
        stored_path_val = str(dest)
    else:
        dest = FILES_DIR / f"{file_uuid}{src.suffix}"
        stored_path_val = dest.name

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
    allowed = {"file_use", "format_name", "format_version", "encoding", "extra_metadata"}
    sql, vals = _build_update_sql("file_object", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [file_id])


def delete_file_object(file_id: int) -> None:
    """Delete a file object, logging a DELETE audit event first (FIX-002)."""
    row = get_file_object(file_id)
    if row:
        # FIX-002: log before deleting
        log_event(
            "file", file_id, "DELETE", "SUCCESS",
            agent="system",
            detail=f"File object deleted: {row.get('original_name', '')}",
            extra_metadata={k: row.get(k) for k in
                            ["original_name", "stored_path", "checksum_sha256", "file_use"]},
        )
        _sp = Path(row["stored_path"])
        stored = _sp if _sp.is_absolute() else FILES_DIR / _sp
        stored = stored.resolve()
        # SEC-004: only unlink if the resolved path is inside ARTIFACTS_DIR or FILES_DIR
        safe_roots = (ARTIFACTS_DIR.resolve(), FILES_DIR.resolve())
        if any(str(stored).startswith(str(root)) for root in safe_roots):
            stored.unlink(missing_ok=True)
        else:
            import logging as _log
            _log.getLogger(__name__).warning(
                "delete_file_object: refusing to unlink '%s' outside permitted dirs", stored
            )
    with get_conn() as conn:
        conn.execute("DELETE FROM file_object WHERE id = ?", (file_id,))


# ── Job file links ────────────────────────────────────────────────────────────

def link_file_to_job(
    file_object_id: int, job_type: str, job_id: int,
    step_key: Optional[str] = None, sequence_num: int = 0,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO job_file_link (file_object_id,job_type,job_id,step_key,sequence_num) "
            "VALUES (?,?,?,?,?)",
            (file_object_id, job_type, job_id, step_key, sequence_num),
        )
        return int(cur.lastrowid)


def list_files_for_job(job_type: str, job_id: int) -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute("""
            SELECT fo.*, jfl.id AS link_id, jfl.step_key, jfl.sequence_num
            FROM file_object fo
            JOIN job_file_link jfl ON jfl.file_object_id = fo.id
            WHERE jfl.job_type = ? AND jfl.job_id = ?
            ORDER BY jfl.sequence_num, fo.created_at
        """, (job_type, job_id)))


def unlink_file_from_job(link_id: int) -> None:
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
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO metadata_event (job_type,job_id,event_type,event_outcome,"
            "step_key,file_object_id,agent,detail,extra_metadata) VALUES (?,?,?,?,?,?,?,?,?)",
            (job_type, job_id, event_type, event_outcome, step_key, file_object_id,
             agent, detail, json.dumps(extra_metadata) if extra_metadata else None),
        )
        return int(cur.lastrowid)


def list_events_for_job(job_type: str, job_id: int) -> list[dict[str, Any]]:
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
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO structural_map_node (job_type,job_id,parent_id,label,"
            "div_type,order_num,file_object_id) VALUES (?,?,?,?,?,?,?)",
            (job_type, job_id, parent_id, label, div_type, order_num, file_object_id),
        )
        return int(cur.lastrowid)


def list_struct_nodes(job_type: str, job_id: int) -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute("""
            SELECT sn.*, fo.original_name AS file_name
            FROM structural_map_node sn
            LEFT JOIN file_object fo ON fo.id = sn.file_object_id
            WHERE sn.job_type = ? AND sn.job_id = ?
            ORDER BY sn.order_num
        """, (job_type, job_id)))


def delete_struct_node(node_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM structural_map_node WHERE id = ?", (node_id,))


# ── Job metadata ──────────────────────────────────────────────────────────────

def set_job_metadata(job_type: str, job_id: int, meta_key: str, meta_value: str) -> None:
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO job_metadata (job_type,job_id,meta_key,meta_value) VALUES (?,?,?,?)
            ON CONFLICT(job_type,job_id,meta_key) DO UPDATE SET
                meta_value = excluded.meta_value,
                updated_at = datetime('now')
        """, (job_type, job_id, meta_key, meta_value))


def get_job_metadata(job_type: str, job_id: int, meta_key: str) -> Optional[str]:
    with get_conn() as conn:
        rows = _rows(conn.execute(
            "SELECT meta_value FROM job_metadata WHERE job_type=? AND job_id=? AND meta_key=?",
            (job_type, job_id, meta_key),
        ))
        return rows[0]["meta_value"] if rows else None


def list_job_metadata(job_type: str, job_id: int) -> dict[str, str]:
    with get_conn() as conn:
        rows = _rows(conn.execute(
            "SELECT meta_key, meta_value FROM job_metadata "
            "WHERE job_type=? AND job_id=? ORDER BY meta_key",
            (job_type, job_id),
        ))
        return {r["meta_key"]: r["meta_value"] for r in rows}


def delete_job_metadata(job_type: str, job_id: int, meta_key: str) -> None:
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
    """Normalise and backfill typo'd metadata keys into approved keys (writes to DB)."""
    if not approved_keys:
        return {"updated_rows": 0, "deleted_rows": 0, "mappings": {}, "skipped_keys": []}

    def _norm(k: str) -> str:
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


def preview_backfill_metadata_keys(approved_keys: list[str]) -> dict[str, Any]:
    """Return proposed key mappings without writing to the database (FIX-017 dry-run)."""
    if not approved_keys:
        return {"mappings": {}, "skipped_keys": [], "usage_counts": {}}

    def _norm(k: str) -> str:
        k = k.strip().lower().replace(" ", "_").replace("-", "_")
        return re.sub(r"[^a-z0-9_:]", "", k)

    approved_set = set(approved_keys)
    norm_to_key = {_norm(k): k for k in approved_keys}
    norm_candidates = list(norm_to_key.keys())

    with get_conn() as conn:
        distinct = _rows(conn.execute(
            "SELECT meta_key, COUNT(*) AS usage_count FROM job_metadata "
            "GROUP BY meta_key ORDER BY meta_key"
        ))

    mappings: dict[str, str] = {}
    skipped: list[str] = []
    usage_counts: dict[str, int] = {r["meta_key"]: r["usage_count"] for r in distinct}

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

    return {
        "mappings": mappings,
        "skipped_keys": skipped,
        "usage_counts": usage_counts,
    }


# ── Step helpers ──────────────────────────────────────────────────────────────

_STEP_TABLES: dict[str, str] = {
    "braille": "braille_job",
    "lp_ebraille": "lp_ebraille_job",
    "tactile": "tactile_graphics_job",
    "print": "print_job",   # FIX-007
}
_ALLOWED_STEPS: dict[str, list[str]] = {
    "braille":     ["digitized", "formatted", "brailled", "proofread", "delivered"],
    "lp_ebraille": ["digitized", "formatted", "converted", "proofread", "delivered"],
    "tactile":     ["designed", "produced", "qa_reviewed", "delivered"],
    "print":       ["designed", "sliced", "printed", "inspected", "delivered"],  # FIX-007
}


def complete_step(job_type: str, job_id: int, step_key: str, agent: str = "user") -> None:
    """Mark a workflow step as complete and log a STEP_COMPLETE event."""
    table = _STEP_TABLES.get(job_type)
    if not table or step_key not in _ALLOWED_STEPS.get(job_type, []):
        raise ValueError(f"Unknown step '{step_key}' for job type '{job_type}'")
    step_date_col = f"{step_key}_date"
    with get_conn() as conn:
        conn.execute(
            f"UPDATE {table} SET {step_key} = 1, {step_date_col} = datetime('now'), updated_at = datetime('now') WHERE id = ?",  # noqa: S608 - table/step/date columns come from fixed maps, never raw user SQL.
            (job_id,),
        )
    log_event(job_type, job_id, "STEP_COMPLETE", "SUCCESS",
              step_key=step_key, agent=agent, detail=f"Step '{step_key}' marked complete")


def revert_step(
    job_type: str, job_id: int, step_key: str,
    agent: str = "user", reason: str = "",
) -> None:
    """Revert a workflow step and log a STEP_REVERT event."""
    table = _STEP_TABLES.get(job_type)
    if not table or step_key not in _ALLOWED_STEPS.get(job_type, []):
        raise ValueError(f"Unknown step '{step_key}' for job type '{job_type}'")
    step_date_col = f"{step_key}_date"
    with get_conn() as conn:
        conn.execute(
            f"UPDATE {table} SET {step_key} = 0, {step_date_col} = NULL, updated_at = datetime('now') WHERE id = ?",  # noqa: S608 - table/step/date columns come from fixed maps, never raw user SQL.
            (job_id,),
        )
    log_event(job_type, job_id, "STEP_REVERT", "WARNING",
              step_key=step_key, agent=agent,
              detail=f"Step '{step_key}' reverted" + (f": {reason}" if reason else ""))


def record_delivery(
    job_type: str, job_id: int,
    delivery_method: str,
    delivery_recipient: str,
    delivery_date: Optional[str] = None,
    delivery_notes: str = "",
    agent: str = "user",
) -> None:
    """Record delivery details, complete the 'delivered' step, and log a DELIVERY event (FIX-016)."""
    from datetime import date
    d_date = delivery_date or date.today().isoformat()

    # Update delivery columns directly without emitting a redundant FIELD_UPDATE event.
    _table_map = {
        "braille":     "braille_job",
        "lp_ebraille": "lp_ebraille_job",
        "tactile":     "tactile_graphics_job",
        "print":       "print_job",
    }
    table = _table_map.get(job_type)
    if table and table in _SAFE_TABLES:
        with get_conn() as conn:
            conn.execute(  # noqa: S608 - table comes from a fixed allow-map, not user input.
                f"UPDATE {table} SET delivered=1, delivery_date=?, delivery_method=?, "
                f"delivery_recipient=?, delivery_notes=?, updated_at=datetime('now') WHERE id=?",
                (d_date, delivery_method, delivery_recipient, delivery_notes, job_id),
            )

    log_event(
        job_type, job_id, "DELIVERY", "SUCCESS",
        step_key="delivered",
        agent=agent,
        detail=f"Delivered to {delivery_recipient} via {delivery_method} on {d_date}",
        extra_metadata={
            "delivery_method": delivery_method,
            "delivery_recipient": delivery_recipient,
            "delivery_date": d_date,
            "delivery_notes": delivery_notes,
        },
    )


# ── Lookup tables ─────────────────────────────────────────────────────────────

def list_material_categories(
    section: Optional[str] = None, active_only: bool = True,
) -> list[dict[str, Any]]:
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
            f"SELECT * FROM material_category {where} ORDER BY section, sort_order, label",  # noqa: S608 - where clause is assembled from fixed SQL fragments.
            params,
        ))


def add_material_category(section: str, value: str, label: str, sort_order: int = 0) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO material_category (section,value,label,sort_order) VALUES (?,?,?,?)",
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
    """Soft-delete a material category (sets active=0)."""
    set_material_category_active(row_id, 0)


def list_workflow_steps(
    job_type: Optional[str] = None, active_only: bool = True,
) -> list[dict[str, Any]]:
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
            f"SELECT * FROM workflow_step {where} ORDER BY job_type, sort_order, label",  # noqa: S608 - where clause is assembled from fixed SQL fragments.
            params,
        ))


def add_workflow_step(
    job_type: str, step_key: str, label: str,
    description: str = "", sort_order: int = 0,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO workflow_step (job_type,step_key,label,description,sort_order) "
            "VALUES (?,?,?,?,?)",
            (job_type, step_key, label, description, sort_order),
        )
        return int(cur.lastrowid)


def update_workflow_step(row_id: int, **fields: Any) -> None:
    allowed = {"job_type", "step_key", "label", "description", "sort_order", "active"}
    sql, vals = _build_update_sql("workflow_step", fields, allowed, has_updated_at=True)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def set_workflow_step_active(row_id: int, active: int) -> None:
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
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO pipeline_run (pipeline_name,status) VALUES (?,?)",
            (pipeline_name, "running"),
        )
        return int(cur.lastrowid)


def finish_pipeline_run(run_id: int, status: str = "completed") -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE pipeline_run SET status=?, finished_at=datetime('now') WHERE id=?",
            (status, run_id),
        )


def log_pipeline_step(
    pipeline_run_id: int, step_name: str, tool: str,
    command: str, success: bool, output: str,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO pipeline_step_run (pipeline_run_id,step_name,tool,command,success,output) "
            "VALUES (?,?,?,?,?,?)",
            (pipeline_run_id, step_name, tool, command, 1 if success else 0, output),
        )
        return int(cur.lastrowid)


def list_pipeline_runs(limit: int = 50) -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT * FROM pipeline_run ORDER BY started_at DESC LIMIT ?", (limit,),
        ))


def list_pipeline_step_runs(pipeline_run_id: int) -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT * FROM pipeline_step_run WHERE pipeline_run_id=? ORDER BY ran_at",
            (pipeline_run_id,),
        ))


# ── Backup log ────────────────────────────────────────────────────────────────

def log_backup(backup_path: str, size_bytes: int, trigger: str = "scheduled",
               status: str = "ok") -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO backup_log (backup_path, size_bytes, trigger, status) VALUES (?,?,?,?)",
            (backup_path, size_bytes, trigger, status),
        )
        return int(cur.lastrowid)


def list_backup_log(limit: int = 50) -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute(
            "SELECT * FROM backup_log ORDER BY created_at DESC LIMIT ?", (limit,),
        ))


# ── Students (FIX-010) ────────────────────────────────────────────────────────

def list_students(active_only: bool = True) -> list[dict[str, Any]]:
    """Return student records ordered by last name, first name."""
    with get_conn() as conn:
        where = "WHERE active = 1" if active_only else ""
        return _rows(conn.execute(
            f"SELECT * FROM student {where} ORDER BY last_name, first_name"  # noqa: S608 - where clause is a fixed toggle, no user-supplied SQL.
        ))


def list_students_page(
    search: Optional[str] = None,
    active_only: bool = True,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Return a paginated page of student records with optional search."""
    filters: list[str] = []
    params: list[Any] = []
    if active_only:
        filters.append("active = 1")
    if search:
        term = f"%{search}%"
        filters.append("(last_name LIKE ? OR first_name LIKE ? OR school LIKE ?)")
        params.extend([term, term, term])
    where = ("WHERE " + " AND ".join(filters)) if filters else ""
    params.extend([limit, max(0, offset)])
    with get_conn() as conn:
        return _rows(conn.execute(
            f"SELECT * FROM student {where} ORDER BY last_name, first_name LIMIT ? OFFSET ?",  # noqa: S608 - where clause from fixed SQL fragments; values parameterised.
            params,
        ))


def get_student(student_id: int) -> Optional[dict[str, Any]]:
    """Fetch a single student record by id."""
    with get_conn() as conn:
        rows = _rows(conn.execute("SELECT * FROM student WHERE id = ?", (student_id,)))
        return rows[0] if rows else None


def add_student(
    last_name: str, first_name: str,
    school: str = "", grade: str = "",
    preferred_formats: str = "", notes: str = "",
) -> int:
    """Create a student record and return the new id."""
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO student (last_name,first_name,school,grade,preferred_formats,notes) "
            "VALUES (?,?,?,?,?,?)",
            (last_name, first_name, school, grade, preferred_formats, notes),
        )
        return int(cur.lastrowid)


def update_student(student_id: int, **fields: Any) -> None:
    """Update a student record."""
    allowed = {"last_name", "first_name", "school", "grade", "preferred_formats",
               "notes", "active"}
    sql, vals = _build_update_sql("student", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [student_id])


def delete_student(student_id: int) -> None:
    """Soft-delete a student (sets active=0)."""
    update_student(student_id, active=0)


def count_jobs_for_students(student_ids: list[int]) -> dict[int, int]:
    """Return total job counts for a batch of students in a single query.

    Issues one SQL UNION ALL query rather than four separate queries per
    student. Returns {student_id: total_count}.
    """
    if not student_ids:
        return {}
    placeholders = ",".join("?" * len(student_ids))
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT student_id, COUNT(*) AS cnt FROM (
                SELECT student_id FROM braille_job         WHERE student_id IN ({placeholders})
                UNION ALL
                SELECT student_id FROM lp_ebraille_job     WHERE student_id IN ({placeholders})
                UNION ALL
                SELECT student_id FROM tactile_graphics_job WHERE student_id IN ({placeholders})
                UNION ALL
                SELECT student_id FROM print_job            WHERE student_id IN ({placeholders})
            ) GROUP BY student_id
            """,  # noqa: S608 - placeholders are '?' only; no user content in SQL.
            student_ids * 4,
        ).fetchall()
    return {row[0]: row[1] for row in rows}


def list_jobs_for_student(student_id: int) -> dict[str, list[dict[str, Any]]]:
    """Return all jobs linked to a student, grouped by type."""
    with get_conn() as conn:
        braille = _rows(conn.execute(
            "SELECT *, 'braille' AS job_type FROM braille_job WHERE student_id = ? ORDER BY created_at DESC",
            (student_id,),
        ))
        lp = _rows(conn.execute(
            "SELECT *, job_type FROM lp_ebraille_job WHERE student_id = ? ORDER BY created_at DESC",
            (student_id,),
        ))
        tactile = _rows(conn.execute(
            "SELECT *, 'tactile' AS job_type FROM tactile_graphics_job WHERE student_id = ? ORDER BY created_at DESC",
            (student_id,),
        ))
        print_jobs = _rows(conn.execute(
            "SELECT *, 'print' AS job_type FROM print_job WHERE student_id = ? ORDER BY printed_at DESC",
            (student_id,),
        ))
    return {
        "braille": braille,
        "lp_ebraille": lp,
        "tactile": tactile,
        "print": print_jobs,
    }


# ── Search (FIX-009, FIX-014) ─────────────────────────────────────────────────

def search_all(query: str, limit: int = 200) -> dict[str, list[dict[str, Any]]]:
    """Search all job tables, files, metadata, and event log using SQL LIKE queries.

    Replaces the in-memory Python filtering in the UI layer (FIX-009).
    Also searches event log detail text (FIX-014) and file checksums.

    Parameters
    ----------
    query : str
        The search term. Applied with LIKE '%term%' across text columns.
        If exactly 64 hex characters, also tested as an exact SHA-256 match.
    limit : int
        Maximum rows returned per result category.
    """
    term = f"%{query}%"
    # SHA-256 exact match for 64-char hex strings
    is_checksum = len(query) == 64 and all(c in "0123456789abcdefABCDEF" for c in query)

    with get_conn() as conn:
        if not is_checksum:
            try:
                def _fts_ids(table: str) -> list[int]:
                    rows = conn.execute(
                        f"SELECT id FROM {table} WHERE {table} MATCH ? LIMIT ?",  # noqa: S608 - table comes from fixed in-function constants.
                        (query, limit),
                    ).fetchall()
                    return [int(r[0]) for r in rows]

                def _rows_by_ids(
                    table: str,
                    columns: str,
                    order_by: str,
                    ids: list[int],
                ) -> list[dict[str, Any]]:
                    if not ids:
                        return []
                    placeholders = ",".join("?" for _ in ids)
                    sql = (
                        f"SELECT {columns} FROM {table} "
                        f"WHERE id IN ({placeholders}) ORDER BY {order_by} LIMIT ?"
                    )
                    return _rows(conn.execute(sql, [*ids, limit]))

                braille_jobs = _rows_by_ids(
                    "braille_job",
                    "id, title, braille_type, requester, priority, created_at",
                    "created_at DESC",
                    _fts_ids("braille_job_fts"),
                )
                lp_jobs = _rows_by_ids(
                    "lp_ebraille_job",
                    "id, title, job_type, requester, priority, created_at",
                    "created_at DESC",
                    _fts_ids("lp_ebraille_job_fts"),
                )
                tactile_jobs = _rows_by_ids(
                    "tactile_graphics_job",
                    "id, title, tactile_type, requester, priority, created_at",
                    "created_at DESC",
                    _fts_ids("tactile_graphics_job_fts"),
                )
                print_jobs = _rows_by_ids(
                    "print_job",
                    "id, object_name, file_name, requester, successful, printed_at",
                    "printed_at DESC",
                    _fts_ids("print_job_fts"),
                )
                files = _rows_by_ids(
                    "file_object",
                    "id, original_name, stored_path, file_use, format_name, checksum_sha256, created_at",
                    "created_at DESC",
                    _fts_ids("file_object_fts"),
                )
                metadata = _rows(conn.execute(
                    "SELECT job_type, CAST(job_id AS INTEGER) AS job_id, meta_key, meta_value "
                    "FROM job_metadata_fts WHERE job_metadata_fts MATCH ? LIMIT ?",
                    (query, limit),
                ))
                events = _rows(conn.execute(
                    "SELECT id, job_type, CAST(job_id AS INTEGER) AS job_id, event_type, agent, detail "
                    "FROM metadata_event_fts WHERE metadata_event_fts MATCH ? LIMIT ?",
                    (query, limit),
                ))
                students = _rows(conn.execute(
                    "SELECT id, last_name, first_name, school, grade "
                    "FROM student WHERE last_name LIKE ? OR first_name LIKE ? "
                    "OR school LIKE ? OR notes LIKE ? ORDER BY last_name LIMIT ?",
                    (term, term, term, term, limit),
                ))

                return {
                    "braille_jobs": braille_jobs,
                    "lp_jobs": lp_jobs,
                    "tactile_jobs": tactile_jobs,
                    "print_jobs": print_jobs,
                    "files": files,
                    "metadata": metadata,
                    "events": events,
                    "students": students,
                }
            except sqlite3.OperationalError:
                # Fallback for environments where FTS tables are unavailable.
                pass

        braille_jobs = _rows(conn.execute(
            "SELECT id, title, braille_type, requester, priority, created_at "
            "FROM braille_job WHERE title LIKE ? OR requester LIKE ? OR notes LIKE ? "
            "ORDER BY created_at DESC LIMIT ?",
            (term, term, term, limit),
        ))

        lp_jobs = _rows(conn.execute(
            "SELECT id, title, job_type, requester, priority, created_at "
            "FROM lp_ebraille_job WHERE title LIKE ? OR requester LIKE ? OR notes LIKE ? "
            "ORDER BY created_at DESC LIMIT ?",
            (term, term, term, limit),
        ))

        tactile_jobs = _rows(conn.execute(
            "SELECT id, title, tactile_type, requester, priority, created_at "
            "FROM tactile_graphics_job WHERE title LIKE ? OR requester LIKE ? OR notes LIKE ? "
            "ORDER BY created_at DESC LIMIT ?",
            (term, term, term, limit),
        ))

        print_jobs = _rows(conn.execute(
            "SELECT id, object_name, file_name, requester, successful, printed_at "
            "FROM print_job WHERE object_name LIKE ? OR requester LIKE ? "
            "OR file_name LIKE ? OR notes LIKE ? ORDER BY printed_at DESC LIMIT ?",
            (term, term, term, term, limit),
        ))

        if is_checksum:
            files = _rows(conn.execute(
                "SELECT id, original_name, stored_path, file_use, format_name, "
                "checksum_sha256, created_at FROM file_object "
                "WHERE original_name LIKE ? OR stored_path LIKE ? OR format_name LIKE ? "
                "OR encoding LIKE ? OR checksum_sha256 = ? ORDER BY created_at DESC LIMIT ?",
                (term, term, term, term, query, limit),
            ))
        else:
            files = _rows(conn.execute(
                "SELECT id, original_name, stored_path, file_use, format_name, "
                "checksum_sha256, created_at FROM file_object "
                "WHERE original_name LIKE ? OR stored_path LIKE ? OR format_name LIKE ? "
                "OR encoding LIKE ? ORDER BY created_at DESC LIMIT ?",
                (term, term, term, term, limit),
            ))

        metadata = _rows(conn.execute(
            "SELECT jm.job_type, jm.job_id, jm.meta_key, jm.meta_value "
            "FROM job_metadata jm WHERE jm.meta_key LIKE ? OR jm.meta_value LIKE ? "
            "ORDER BY jm.job_type, jm.job_id LIMIT ?",
            (term, term, limit),
        ))

        # FIX-014: event log search
        events = _rows(conn.execute(
            "SELECT me.id, me.job_type, me.job_id, me.event_type, me.agent, "
            "me.detail, me.event_datetime "
            "FROM metadata_event me "
            "WHERE me.detail LIKE ? OR me.agent LIKE ? OR me.event_type LIKE ? "
            "ORDER BY me.event_datetime DESC LIMIT ?",
            (term, term, term, limit),
        ))

        students = _rows(conn.execute(
            "SELECT id, last_name, first_name, school, grade "
            "FROM student WHERE last_name LIKE ? OR first_name LIKE ? "
            "OR school LIKE ? OR notes LIKE ? ORDER BY last_name LIMIT ?",
            (term, term, term, term, limit),
        ))

    return {
        "braille_jobs": braille_jobs,
        "lp_jobs": lp_jobs,
        "tactile_jobs": tactile_jobs,
        "print_jobs": print_jobs,
        "files": files,
        "metadata": metadata,
        "events": events,
        "students": students,
    }


# ── Reporting (FIX-015) ───────────────────────────────────────────────────────

def report_jobs(
    school: Optional[str] = None,
    grade: Optional[str] = None,
    job_type: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    student_id: Optional[int] = None,
) -> dict[str, Any]:
    """Return filtered job lists grouped by type with summary counts.

    Parameters
    ----------
    school : str, optional
        Filter by student.school (exact) or dc:coverage metadata value (LIKE).
    grade : str, optional
        Filter by student.grade or grade_level metadata value (LIKE).
    job_type : str, optional
        One of 'braille', 'lp_ebraille', 'tactile', 'print'. If None, all types returned.
    status : str, optional
        'not_started', 'in_progress', or 'delivered'.
    priority : str, optional
        One of 'low', 'normal', 'high', 'urgent'.
    date_from : str, optional
        ISO date string — jobs created on or after this date.
    date_to : str, optional
        ISO date string — jobs created on or before this date.
    student_id : int, optional
        Return only jobs for this student.
    """

    def _step_status_expr(steps: list[str]) -> str:
        """Build SQL CASE expression deriving a status label from step columns."""
        delivered_col = steps[-1]
        any_done = " + ".join(f"COALESCE({s}, 0)" for s in steps)
        return (
            f"CASE WHEN {delivered_col} = 1 THEN 'delivered' "
            f"WHEN ({any_done}) > 0 THEN 'in_progress' "
            f"ELSE 'not_started' END"
        )

    def _run(
        table: str,
        type_label: str,
        steps: list[str],
        title_col: str = "title",
        date_col: str = "created_at",
        priority_expr: str = "j.priority",
        type_expr: str | None = None,
    ) -> list[dict[str, Any]]:
        # SAFE: all SQL-interpolated identifiers come from fixed in-function constants,
        # not user input. User-supplied values are bound via '?' parameterisation only.
        filters: list[str] = []
        params: list[Any] = []

        if student_id is not None:
            filters.append("j.student_id = ?")
            params.append(student_id)
        if date_from:
            filters.append(f"j.{date_col} >= ?")
            params.append(date_from)
        if date_to:
            filters.append(f"j.{date_col} <= ?")
            params.append(date_to)
        if school:
            filters.append(
                "(s.school LIKE ? OR EXISTS ("
                "  SELECT 1 FROM job_metadata jm "
                "  WHERE jm.job_type=? AND jm.job_id=j.id "
                "  AND jm.meta_key='dc:coverage' AND jm.meta_value LIKE ?"
                "))"
            )
            params += [f"%{school}%", type_label, f"%{school}%"]
        if grade:
            filters.append(
                "(s.grade LIKE ? OR EXISTS ("
                "  SELECT 1 FROM job_metadata jm "
                "  WHERE jm.job_type=? AND jm.job_id=j.id "
                "  AND jm.meta_key='grade_level' AND jm.meta_value LIKE ?"
                "))"
            )
            params += [f"%{grade}%", type_label, f"%{grade}%"]

        status_expr = _step_status_expr(steps)
        if status:
            filters.append(f"({status_expr}) = ?")
            params.append(status)
        if priority and priority_expr != "NULL":
            filters.append(f"{priority_expr} = ?")
            params.append(priority)

        where = ("WHERE " + " AND ".join(filters)) if filters else ""
        resolved_type_expr = type_expr or f"'{type_label}'"

        sql = f"""
                                 SELECT j.id, j.{title_col} AS title, {resolved_type_expr} AS job_type,
                 j.requester, {priority_expr} AS priority, j.{date_col} AS created_at,
                   s.last_name, s.first_name, s.school, s.grade,
                   ({status_expr}) AS status
            FROM {table} j
            LEFT JOIN student s ON s.id = j.student_id
            {where}
                 ORDER BY j.{date_col} DESC
        """  # noqa: S608 - table/column identifiers come from trusted in-module constants.
        with get_conn() as conn:
            return _rows(conn.execute(sql, params))

    b_steps   = ["digitized", "formatted", "brailled", "proofread", "delivered"]
    lp_steps  = ["digitized", "formatted", "converted", "proofread", "delivered"]
    tac_steps = ["designed", "produced", "qa_reviewed", "delivered"]
    prt_steps = ["designed", "sliced", "printed", "inspected", "delivered"]

    results: dict[str, list[dict[str, Any]]] = {}

    if job_type in (None, "braille"):
        results["braille"] = _run("braille_job", "braille", b_steps)
    if job_type in (None, "lp_ebraille"):
        results["lp_ebraille"] = _run(
            "lp_ebraille_job",
            "lp_ebraille",
            lp_steps,
            type_expr="COALESCE(j.job_type, 'lp_ebraille')",
        )
    if job_type in (None, "tactile"):
        results["tactile"] = _run("tactile_graphics_job", "tactile", tac_steps)
    if job_type in (None, "print"):
        results["print"] = _run(
            "print_job",
            "print",
            prt_steps,
            title_col="object_name",
            date_col="printed_at",
            priority_expr="'normal'",
        )

    all_jobs: list[dict[str, Any]] = []
    for rows in results.values():
        all_jobs.extend(rows)

    by_type = {k: len(v) for k, v in results.items()}
    return {
        "total_jobs": len(all_jobs),
        "by_type": by_type,
        "jobs": all_jobs,
        "by_type_lists": results,
    }
