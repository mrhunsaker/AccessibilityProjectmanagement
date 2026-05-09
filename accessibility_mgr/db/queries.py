"""
Data access helpers for the Accessibility Materials Project Manager.

ALL SQL lives in this module. No SQL strings are constructed outside it.
All parameterized queries use '?' placeholders.

METS-style metadata functions follow conventional helpers so the
database layer provides a clear API for provenance recording.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import uuid
import warnings
from pathlib import Path
from typing import Any, Optional

from .schema import FILES_DIR, PRINTS_DIR, get_conn

__all__ = [
    # Filament
    "list_filaments", "add_filament", "update_filament", "delete_filament", "deduct_filament",
    # Paper
    "list_paper", "add_paper", "update_paper", "delete_paper",
    # Electronics
    "list_electronics", "add_electronic", "update_electronic", "delete_electronic",
    # Printers
    "list_printers", "add_printer", "update_printer", "delete_printer",
    # Print jobs
    "list_print_jobs", "add_print_job", "update_print_job", "delete_print_job",
    # Braille jobs
    "list_braille_jobs", "get_braille_job", "add_braille_job", "update_braille_job", "delete_braille_job",
    # LP/eBraille jobs
    "list_lp_jobs", "get_lp_job", "add_lp_job", "update_lp_job", "delete_lp_job",
    # File objects
    "list_file_objects", "get_file_object", "ingest_file", "update_file_object", "delete_file_object",
    # Job file links
    "link_file_to_job", "list_files_for_job", "unlink_file_from_job",
    # Metadata events
    "log_event", "list_events_for_job",
    # Structural map
    "add_struct_node", "list_struct_nodes", "delete_struct_node",
    # Job metadata (descriptive)
    "set_job_metadata", "get_job_metadata", "list_job_metadata", "delete_job_metadata",
    # Lookup tables
    "list_material_categories", "add_material_category", "update_material_category",
    "set_material_category_active", "delete_material_category",
    "list_workflow_steps", "add_workflow_step", "update_workflow_step",
    "set_workflow_step_active", "delete_workflow_step",
    # Step helpers
    "complete_step", "revert_step",
    # Files dir
    "FILES_DIR", "PRINTS_DIR",
]


# ─── Internal helpers ──────────────────────────────────────────────────────────

def _rows(cur: Any) -> list[dict[str, Any]]:
    cols = [col[0] for col in cur.description]
    return [{cols[i]: row[i] for i in range(len(cols))} for row in cur.fetchall()]


def _build_update_sql(
    table: str,
    fields: dict[str, Any],
    allowed: set[str],
    include_updated_at: bool = True,
) -> tuple[str, list[Any]]:
    _ALLOWED_TABLES = {
        "filament", "braille_paper", "electronics", "printer",
        "print_job", "braille_job", "lp_ebraille_job",
        "file_object", "job_metadata", "material_category", "workflow_step",
    }
    if table not in _ALLOWED_TABLES:
        raise ValueError(f"Disallowed table '{table}'")
    safe = {k: v for k, v in fields.items() if k in allowed}
    if not safe:
        raise ValueError(f"No valid fields to update in '{table}'")
    sets = ", ".join(f"{c} = ?" for c in safe)
    ts = ", updated_at = datetime('now')" if include_updated_at else ""
    return f"UPDATE {table} SET {sets}{ts} WHERE id = ?", list(safe.values())


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ─── FILAMENT ──────────────────────────────────────────────────────────────────

def list_filaments() -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM filament ORDER BY brand, color"))


def add_filament(
    brand: str, color: str, filament_type: str,
    diameter_mm: float = 1.75, quantity_g: float = 0,
    cost_per_kg: Optional[float] = None, supplier: str = "", notes: str = "",
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO filament (brand,color,filament_type,diameter_mm,quantity_g,cost_per_kg,supplier,notes)"
            " VALUES (?,?,?,?,?,?,?,?)",
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
        conn.execute("DELETE FROM filament WHERE id=?", (row_id,))


def deduct_filament(row_id: int, grams: float) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE filament SET quantity_g=MAX(0,quantity_g-?), updated_at=datetime('now') WHERE id=?",
            (grams, row_id),
        )


# ─── PAPER ─────────────────────────────────────────────────────────────────────

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
            "INSERT INTO braille_paper (paper_type,size,label_type,quantity,supplier,notes) VALUES (?,?,?,?,?,?)",
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
        conn.execute("DELETE FROM braille_paper WHERE id=?", (row_id,))


# ─── ELECTRONICS ───────────────────────────────────────────────────────────────

def list_electronics(category: Optional[str] = None) -> list[dict[str, Any]]:
    with get_conn() as conn:
        if category:
            return _rows(conn.execute(
                "SELECT * FROM electronics WHERE category=? ORDER BY name", (category,)
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
            "INSERT INTO electronics (category,name,brand,spec,quantity,unit,cost_each,supplier,notes)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
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
        conn.execute("DELETE FROM electronics WHERE id=?", (row_id,))


# ─── PRINTERS ──────────────────────────────────────────────────────────────────

def list_printers() -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM printer ORDER BY name"))


def add_printer(name: str, model: str = "", notes: str = "") -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO printer (name,model,notes) VALUES (?,?,?)", (name, model, notes)
        )
        return int(cur.lastrowid)


def update_printer(row_id: int, **fields: Any) -> None:
    allowed = {"name", "model", "notes"}
    sql, vals = _build_update_sql("printer", fields, allowed, include_updated_at=False)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_printer(row_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM printer WHERE id=?", (row_id,))


# ─── PRINT JOBS ────────────────────────────────────────────────────────────────

def list_print_jobs() -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute("""
            SELECT pj.*,
                   p.name AS printer_name,
                   f.brand||' '||f.color||' '||f.filament_type AS filament_desc
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
                warnings.warn(f"Could not copy print file '{src}': {exc}", RuntimeWarning, stacklevel=2)
        elif src == dest:
            file_path = str(dest.relative_to(PRINTS_DIR.parent))
            file_name = src.name

    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO print_job
               (printer_id,filament_id,filament_used_g,file_path,file_name,
                successful,failure_reason,object_name,requester,request_date,notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (printer_id, filament_id, filament_used_g, file_path, file_name,
             successful, failure_reason, object_name, requester, request_date, notes),
        )
        new_id = int(cur.lastrowid)

    if filament_id and filament_used_g:
        deduct_filament(filament_id, filament_used_g)

    log_event("print", new_id, "CREATE", "SUCCESS", detail=f"Print job created: {object_name or file_name or 'unnamed'}")
    return new_id


def update_print_job(row_id: int, **fields: Any) -> None:
    allowed = {"printer_id", "filament_id", "filament_used_g", "successful",
               "failure_reason", "object_name", "requester", "request_date", "notes"}
    sql, vals = _build_update_sql("print_job", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_print_job(row_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM print_job WHERE id=?", (row_id,))


# ─── BRAILLE JOBS ──────────────────────────────────────────────────────────────

def list_braille_jobs() -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM braille_job ORDER BY created_at DESC"))


def get_braille_job(row_id: int) -> Optional[dict[str, Any]]:
    with get_conn() as conn:
        rows = _rows(conn.execute("SELECT * FROM braille_job WHERE id=?", (row_id,)))
        return rows[0] if rows else None


def add_braille_job(
    title: str, braille_type: str,
    requester: str = "", request_date: Optional[str] = None,
    due_date: Optional[str] = None, priority: str = "normal", notes: str = "",
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO braille_job (title,braille_type,requester,request_date,due_date,priority,notes)"
            " VALUES (?,?,?,?,?,?,?)",
            (title, braille_type, requester, request_date, due_date, priority, notes),
        )
        new_id = int(cur.lastrowid)
    log_event("braille", new_id, "CREATE", "SUCCESS", detail=f"Braille job created: {title}")
    return new_id


def update_braille_job(row_id: int, **fields: Any) -> None:
    allowed = {"title", "braille_type", "requester", "request_date", "due_date",
               "priority", "digitized", "formatted", "brailled", "proofread", "delivered", "notes"}
    sql, vals = _build_update_sql("braille_job", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_braille_job(row_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM braille_job WHERE id=?", (row_id,))


# ─── LP/eBRAILLE JOBS ──────────────────────────────────────────────────────────

def list_lp_jobs() -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute("SELECT * FROM lp_ebraille_job ORDER BY created_at DESC"))


def get_lp_job(row_id: int) -> Optional[dict[str, Any]]:
    with get_conn() as conn:
        rows = _rows(conn.execute("SELECT * FROM lp_ebraille_job WHERE id=?", (row_id,)))
        return rows[0] if rows else None


def add_lp_job(
    title: str, job_type: str,
    requester: str = "", request_date: Optional[str] = None,
    due_date: Optional[str] = None, priority: str = "normal", notes: str = "",
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO lp_ebraille_job (title,job_type,requester,request_date,due_date,priority,notes)"
            " VALUES (?,?,?,?,?,?,?)",
            (title, job_type, requester, request_date, due_date, priority, notes),
        )
        new_id = int(cur.lastrowid)
    log_event("lp_ebraille", new_id, "CREATE", "SUCCESS", detail=f"LP/eBraille job created: {title}")
    return new_id


def update_lp_job(row_id: int, **fields: Any) -> None:
    allowed = {"title", "job_type", "requester", "request_date", "due_date",
               "priority", "digitized", "formatted", "converted", "proofread", "delivered", "notes"}
    sql, vals = _build_update_sql("lp_ebraille_job", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def delete_lp_job(row_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM lp_ebraille_job WHERE id=?", (row_id,))


# ─── FILE OBJECTS ──────────────────────────────────────────────────────────────

def list_file_objects(job_type: Optional[str] = None, job_id: Optional[int] = None) -> list[dict[str, Any]]:
    with get_conn() as conn:
        if job_type and job_id is not None:
            return _rows(conn.execute("""
                SELECT fo.*, jfl.step_key, jfl.sequence_num
                FROM file_object fo
                JOIN job_file_link jfl ON jfl.file_object_id = fo.id
                WHERE jfl.job_type=? AND jfl.job_id=?
                ORDER BY jfl.sequence_num, fo.created_at
            """, (job_type, job_id)))
        return _rows(conn.execute("SELECT * FROM file_object ORDER BY created_at DESC"))


def get_file_object(file_id: int) -> Optional[dict[str, Any]]:
    with get_conn() as conn:
        rows = _rows(conn.execute("SELECT * FROM file_object WHERE id=?", (file_id,)))
        return rows[0] if rows else None


def ingest_file(
    source_path: str,
    file_use: str = "MASTER",
    format_name: str = "",
    format_version: str = "",
    encoding: str = "",
    extra_metadata: Optional[dict[str, Any]] = None,
) -> int:
    """
    Copy a file into the job_files store, compute its SHA-256, assign a UUID,
    and insert a file_object row.  Returns the new file_object id.
    """
    src = Path(source_path)
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")

    file_uuid = str(uuid.uuid4())
    suffix = src.suffix
    dest_name = f"{file_uuid}{suffix}"
    dest = FILES_DIR / dest_name

    shutil.copy2(src, dest)
    checksum = _sha256(dest)
    size_bytes = dest.stat().st_size

    import mimetypes
    mime_type = mimetypes.guess_type(src.name)[0] or "application/octet-stream"

    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO file_object
               (uuid,original_name,stored_path,mime_type,size_bytes,checksum_sha256,
                file_use,format_name,format_version,encoding,extra_metadata)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                file_uuid, src.name, dest_name, mime_type, size_bytes, checksum,
                file_use, format_name, format_version, encoding,
                json.dumps(extra_metadata) if extra_metadata else None,
            ),
        )
        return int(cur.lastrowid)


def update_file_object(file_id: int, **fields: Any) -> None:
    allowed = {"file_use", "format_name", "format_version", "encoding", "extra_metadata"}
    sql, vals = _build_update_sql("file_object", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [file_id])


def delete_file_object(file_id: int) -> None:
    row = get_file_object(file_id)
    if row:
        stored = FILES_DIR / row["stored_path"]
        if stored.exists():
            stored.unlink(missing_ok=True)
    with get_conn() as conn:
        conn.execute("DELETE FROM file_object WHERE id=?", (file_id,))


# ─── JOB FILE LINKS ────────────────────────────────────────────────────────────

def link_file_to_job(
    file_object_id: int, job_type: str, job_id: int,
    step_key: Optional[str] = None, sequence_num: int = 0,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO job_file_link (file_object_id,job_type,job_id,step_key,sequence_num)"
            " VALUES (?,?,?,?,?)",
            (file_object_id, job_type, job_id, step_key, sequence_num),
        )
        return int(cur.lastrowid)


def list_files_for_job(job_type: str, job_id: int) -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute("""
            SELECT fo.*, jfl.id AS link_id, jfl.step_key, jfl.sequence_num
            FROM file_object fo
            JOIN job_file_link jfl ON jfl.file_object_id = fo.id
            WHERE jfl.job_type=? AND jfl.job_id=?
            ORDER BY jfl.sequence_num, fo.created_at
        """, (job_type, job_id)))


def unlink_file_from_job(link_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM job_file_link WHERE id=?", (link_id,))


# ─── METADATA EVENTS (PREMIS provenance) ──────────────────────────────────────

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
            """INSERT INTO metadata_event
               (job_type,job_id,event_type,event_outcome,step_key,file_object_id,agent,detail,extra_metadata)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                job_type, job_id, event_type, event_outcome, step_key,
                file_object_id, agent,detail,
                json.dumps(extra_metadata) if extra_metadata else None,
            ),
        )
        return int(cur.lastrowid)


def list_events_for_job(job_type: str, job_id: int) -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute("""
            SELECT me.*,
                   fo.original_name AS file_name
            FROM metadata_event me
            LEFT JOIN file_object fo ON fo.id = me.file_object_id
            WHERE me.job_type=? AND me.job_id=?
            ORDER BY me.event_datetime ASC
        """, (job_type, job_id)))


# ─── STRUCTURAL MAP ────────────────────────────────────────────────────────────

def add_struct_node(
    job_type: str, job_id: int, label: str,
    parent_id: Optional[int] = None, div_type: str = "section",
    order_num: int = 0, file_object_id: Optional[int] = None,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO structural_map_node
               (job_type,job_id,parent_id,label,div_type,order_num,file_object_id)
               VALUES (?,?,?,?,?,?,?)""",
            (job_type, job_id, parent_id, label, div_type, order_num, file_object_id),
        )
        return int(cur.lastrowid)


def list_struct_nodes(job_type: str, job_id: int) -> list[dict[str, Any]]:
    with get_conn() as conn:
        return _rows(conn.execute("""
            SELECT sn.*, fo.original_name AS file_name
            FROM structural_map_node sn
            LEFT JOIN file_object fo ON fo.id = sn.file_object_id
            WHERE sn.job_type=? AND sn.job_id=?
            ORDER BY sn.order_num
        """, (job_type, job_id)))


def delete_struct_node(node_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM structural_map_node WHERE id=?", (node_id,))


# ─── JOB METADATA (descriptive / Dublin Core-style) ───────────────────────────

def set_job_metadata(job_type: str, job_id: int, meta_key: str, meta_value: str) -> None:
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO job_metadata (job_type,job_id,meta_key,meta_value)
            VALUES (?,?,?,?)
            ON CONFLICT(job_type,job_id,meta_key) DO UPDATE SET
                meta_value=excluded.meta_value,
                updated_at=datetime('now')
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
            "SELECT meta_key, meta_value FROM job_metadata WHERE job_type=? AND job_id=? ORDER BY meta_key",
            (job_type, job_id),
        ))
        return {r["meta_key"]: r["meta_value"] for r in rows}


def delete_job_metadata(job_type: str, job_id: int, meta_key: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM job_metadata WHERE job_type=? AND job_id=? AND meta_key=?",
            (job_type, job_id, meta_key),
        )


# ─── STEP HELPERS ──────────────────────────────────────────────────────────────

_STEP_TABLES: dict[str, str] = {
    "braille": "braille_job",
    "lp_ebraille": "lp_ebraille_job",
}

_ALLOWED_STEPS: dict[str, list[str]] = {
    "braille": ["digitized", "formatted", "brailled", "proofread", "delivered"],
    "lp_ebraille": ["digitized", "formatted", "converted", "proofread", "delivered"],
}


def complete_step(job_type: str, job_id: int, step_key: str, agent: str = "user") -> None:
    """Mark a workflow step as complete and log a PREMIS event."""
    table = _STEP_TABLES.get(job_type)
    if not table or step_key not in _ALLOWED_STEPS.get(job_type, []):
        raise ValueError(f"Unknown step '{step_key}' for job type '{job_type}'")
    with get_conn() as conn:
        conn.execute(
            f"UPDATE {table} SET {step_key}=1, updated_at=datetime('now') WHERE id=?",
            (job_id,),
        )
    log_event(job_type, job_id, "STEP_COMPLETE", "SUCCESS", step_key=step_key, agent=agent,
              detail=f"Step '{step_key}' marked complete")


def revert_step(job_type: str, job_id: int, step_key: str, agent: str = "user", reason: str = "") -> None:
    """Revert a workflow step and log a PREMIS event."""
    table = _STEP_TABLES.get(job_type)
    if not table or step_key not in _ALLOWED_STEPS.get(job_type, []):
        raise ValueError(f"Unknown step '{step_key}' for job type '{job_type}'")
    with get_conn() as conn:
        conn.execute(
            f"UPDATE {table} SET {step_key}=0, updated_at=datetime('now') WHERE id=?",
            (job_id,),
        )
    log_event(job_type, job_id, "STEP_REVERT", "WARNING", step_key=step_key, agent=agent,
              detail=f"Step '{step_key}' reverted" + (f": {reason}" if reason else ""))


# ─── LOOKUP TABLES ─────────────────────────────────────────────────────────────

def list_material_categories(
    section: Optional[str] = None, active_only: bool = True,
) -> list[dict[str, Any]]:
    with get_conn() as conn:
        filters: list[str] = []
        params: list[Any] = []
        if section:
            filters.append("section=?")
            params.append(section)
        if active_only:
            filters.append("active=1")
        where = ("WHERE " + " AND ".join(filters)) if filters else ""
        return _rows(conn.execute(
            f"SELECT * FROM material_category {where} ORDER BY section,sort_order,label", params
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
            "UPDATE material_category SET active=?,updated_at=datetime('now') WHERE id=?",
            (active, row_id),
        )


def delete_material_category(row_id: int) -> None:
    set_material_category_active(row_id, 0)


def list_workflow_steps(job_type: Optional[str] = None, active_only: bool = True) -> list[dict[str, Any]]:
    with get_conn() as conn:
        filters: list[str] = []
        params: list[Any] = []
        if job_type:
            filters.append("job_type=?")
            params.append(job_type)
        if active_only:
            filters.append("active=1")
        where = ("WHERE " + " AND ".join(filters)) if filters else ""
        return _rows(conn.execute(
            f"SELECT * FROM workflow_step {where} ORDER BY job_type,sort_order,label", params
        ))


def add_workflow_step(job_type: str, step_key: str, label: str,
                      description: str = "", sort_order: int = 0) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO workflow_step (job_type,step_key,label,description,sort_order) VALUES (?,?,?,?,?)",
            (job_type, step_key, label, description, sort_order),
        )
        return int(cur.lastrowid)


def update_workflow_step(row_id: int, **fields: Any) -> None:
    allowed = {"job_type", "step_key", "label", "description", "sort_order", "active"}
    sql, vals = _build_update_sql("workflow_step", fields, allowed)
    with get_conn() as conn:
        conn.execute(sql, vals + [row_id])


def set_workflow_step_active(row_id: int, active: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE workflow_step SET active=?,updated_at=datetime('now') WHERE id=?",
            (active, row_id),
        )


def delete_workflow_step(row_id: int) -> None:
    set_workflow_step_active(row_id, 0)


def list_print_files() -> list[Path]:
    return sorted(PRINTS_DIR.glob("*"))
