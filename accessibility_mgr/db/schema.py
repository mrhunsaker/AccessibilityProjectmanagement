"""
Database schema, connection helpers, and initialisation.

Changes applied (see fix_specs.json):
  FIX-007  print_job gains five workflow step columns.
  FIX-010  student table added; all job tables gain student_id FK.
  FIX-011  file_use seed value changed from MASTER → ORIGINAL.
  FIX-016  All job tables gain delivery_date/method/recipient/notes columns.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


def _resolve_db_path() -> Path:
    configured = os.getenv("ACCESSMAN_DB_PATH", "").strip()
    if configured:
        return Path(configured).expanduser()

    xdg_data_home = Path(
        os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share")
    )
    return xdg_data_home / "accessibility_mgr" / "accessibility_manager.db"


DB_PATH       = _resolve_db_path()
DATA_DIR      = DB_PATH.parent
PRINTS_DIR    = DATA_DIR / "prints_files"
FILES_DIR     = DATA_DIR / "job_files"
BACKUPS_DIR   = DATA_DIR / "backups"
ARTIFACTS_DIR = DATA_DIR / "artifacts"


@contextmanager
def get_conn() -> Generator[sqlite3.Connection, None, None]:
    """Yield a configured SQLite connection; commit on success, rollback on error."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


_SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ═══════════════════════════════════════════════════════════════
-- STUDENTS (FIX-010)
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS student (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    last_name         TEXT NOT NULL,
    first_name        TEXT NOT NULL,
    school            TEXT,
    grade             TEXT,
    preferred_formats TEXT,
    notes             TEXT,
    active            INTEGER DEFAULT 1,
    created_at        TEXT DEFAULT (datetime('now')),
    updated_at        TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════
-- INVENTORY
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS filament (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    brand         TEXT NOT NULL,
    color         TEXT NOT NULL,
    filament_type TEXT NOT NULL,
    diameter_mm   REAL NOT NULL DEFAULT 1.75,
    quantity_g    REAL NOT NULL DEFAULT 0,
    cost_per_kg   REAL,
    supplier      TEXT,
    notes         TEXT,
    created_at    TEXT DEFAULT (datetime('now')),
    updated_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS braille_paper (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_type  TEXT NOT NULL,
    size        TEXT,
    label_type  TEXT,
    quantity    INTEGER NOT NULL DEFAULT 0,
    supplier    TEXT,
    notes       TEXT,
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS electronics (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category    TEXT NOT NULL,
    name        TEXT NOT NULL,
    brand       TEXT,
    spec        TEXT,
    quantity    REAL NOT NULL DEFAULT 0,
    unit        TEXT NOT NULL DEFAULT 'pcs',
    cost_each   REAL,
    supplier    TEXT,
    notes       TEXT,
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════
-- PRINTERS & EMBOSSERS
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS printer (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE,
    model      TEXT,
    notes      TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS embosser (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE,
    model      TEXT,
    paper_type TEXT,
    notes      TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════
-- JOBS
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS print_job (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id       INTEGER NOT NULL REFERENCES printer(id),
    filament_id      INTEGER REFERENCES filament(id),
    filament_used_g  REAL,
    file_path        TEXT,
    file_name        TEXT,
    successful       INTEGER NOT NULL DEFAULT 1,
    failure_reason   TEXT,
    object_name      TEXT,
    requester        TEXT,
    request_date     TEXT,
    notes            TEXT,
    student_id       INTEGER REFERENCES student(id),
    -- FIX-007: workflow step columns for print jobs
    designed         INTEGER DEFAULT 0,
    sliced           INTEGER DEFAULT 0,
    printed          INTEGER DEFAULT 0,
    inspected        INTEGER DEFAULT 0,
    delivered        INTEGER DEFAULT 0,
    -- FIX-016: delivery tracking
    delivery_date      TEXT,
    delivery_method    TEXT,
    delivery_recipient TEXT,
    delivery_notes     TEXT,
    printed_at       TEXT DEFAULT (datetime('now')),
    updated_at       TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS braille_job (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    braille_type TEXT NOT NULL,
    embosser_id  INTEGER REFERENCES embosser(id),
    requester    TEXT,
    request_date TEXT,
    due_date     TEXT,
    priority     TEXT DEFAULT 'normal',
    digitized    INTEGER DEFAULT 0,
    formatted    INTEGER DEFAULT 0,
    brailled     INTEGER DEFAULT 0,
    proofread    INTEGER DEFAULT 0,
    delivered    INTEGER DEFAULT 0,
    notes        TEXT,
    student_id   INTEGER REFERENCES student(id),
    -- FIX-016: delivery tracking
    delivery_date      TEXT,
    delivery_method    TEXT,
    delivery_recipient TEXT,
    delivery_notes     TEXT,
    created_at   TEXT DEFAULT (datetime('now')),
    updated_at   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tactile_graphics_job (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    tactile_type TEXT NOT NULL,
    requester    TEXT,
    request_date TEXT,
    due_date     TEXT,
    priority     TEXT DEFAULT 'normal',
    designed     INTEGER DEFAULT 0,
    produced     INTEGER DEFAULT 0,
    qa_reviewed  INTEGER DEFAULT 0,
    delivered    INTEGER DEFAULT 0,
    notes        TEXT,
    student_id   INTEGER REFERENCES student(id),
    -- FIX-016: delivery tracking
    delivery_date      TEXT,
    delivery_method    TEXT,
    delivery_recipient TEXT,
    delivery_notes     TEXT,
    created_at   TEXT DEFAULT (datetime('now')),
    updated_at   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS lp_ebraille_job (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    job_type     TEXT NOT NULL,
    requester    TEXT,
    request_date TEXT,
    due_date     TEXT,
    priority     TEXT DEFAULT 'normal',
    digitized    INTEGER DEFAULT 0,
    formatted    INTEGER DEFAULT 0,
    converted    INTEGER DEFAULT 0,
    proofread    INTEGER DEFAULT 0,
    delivered    INTEGER DEFAULT 0,
    notes        TEXT,
    student_id   INTEGER REFERENCES student(id),
    -- FIX-016: delivery tracking
    delivery_date      TEXT,
    delivery_method    TEXT,
    delivery_recipient TEXT,
    delivery_notes     TEXT,
    created_at   TEXT DEFAULT (datetime('now')),
    updated_at   TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════
-- QA RUNS
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS qa_run (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name   TEXT NOT NULL,
    command     TEXT NOT NULL,
    job_type    TEXT,
    job_id      INTEGER,
    success     INTEGER NOT NULL DEFAULT 0,
    output      TEXT,
    ran_at      TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════
-- PIPELINE EXECUTIONS
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS pipeline_run (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_name TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'pending',
    started_at    TEXT DEFAULT (datetime('now')),
    finished_at   TEXT
);

CREATE TABLE IF NOT EXISTS pipeline_step_run (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_run_id INTEGER NOT NULL REFERENCES pipeline_run(id),
    step_name       TEXT NOT NULL,
    tool            TEXT NOT NULL,
    command         TEXT NOT NULL,
    success         INTEGER NOT NULL DEFAULT 0,
    output          TEXT,
    ran_at          TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════
-- METS-INSPIRED METADATA
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS file_object (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid             TEXT NOT NULL UNIQUE,
    original_name    TEXT NOT NULL,
    stored_path      TEXT NOT NULL,
    mime_type        TEXT,
    size_bytes       INTEGER,
    checksum_sha256  TEXT,
    file_use         TEXT NOT NULL DEFAULT 'ORIGINAL',
    format_name      TEXT,
    format_version   TEXT,
    encoding         TEXT,
    extra_metadata   TEXT,
    created_at       TEXT DEFAULT (datetime('now')),
    updated_at       TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS job_file_link (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    file_object_id INTEGER NOT NULL REFERENCES file_object(id),
    job_type       TEXT NOT NULL,
    job_id         INTEGER NOT NULL,
    step_key       TEXT,
    sequence_num   INTEGER DEFAULT 0,
    created_at     TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS metadata_event (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type       TEXT NOT NULL,
    job_id         INTEGER NOT NULL,
    event_type     TEXT NOT NULL,
    event_outcome  TEXT,
    step_key       TEXT,
    file_object_id INTEGER REFERENCES file_object(id),
    agent          TEXT,
    detail         TEXT,
    extra_metadata TEXT,
    event_datetime TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS structural_map_node (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type       TEXT NOT NULL,
    job_id         INTEGER NOT NULL,
    parent_id      INTEGER REFERENCES structural_map_node(id),
    label          TEXT NOT NULL,
    div_type       TEXT DEFAULT 'section',
    order_num      INTEGER DEFAULT 0,
    file_object_id INTEGER REFERENCES file_object(id),
    created_at     TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS job_metadata (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type   TEXT NOT NULL,
    job_id     INTEGER NOT NULL,
    meta_key   TEXT NOT NULL,
    meta_value TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(job_type, job_id, meta_key)
);

-- ═══════════════════════════════════════════════════════════════
-- CONFIGURABLE LOOKUP TABLES
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS material_category (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    section    TEXT NOT NULL,
    value      TEXT NOT NULL,
    label      TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    active     INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(section, value)
);

CREATE TABLE IF NOT EXISTS workflow_step (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type    TEXT NOT NULL,
    step_key    TEXT NOT NULL,
    label       TEXT NOT NULL,
    description TEXT,
    sort_order  INTEGER DEFAULT 0,
    active      INTEGER DEFAULT 1,
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now')),
    UNIQUE(job_type, step_key)
);

-- ═══════════════════════════════════════════════════════════════
-- BACKUP LOG
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS backup_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_path TEXT NOT NULL,
    size_bytes  INTEGER,
    trigger     TEXT NOT NULL DEFAULT 'scheduled',
    status      TEXT NOT NULL DEFAULT 'ok',
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS schema_migration (
    migration_id TEXT PRIMARY KEY,
    applied_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_braille_job_student ON braille_job(student_id);
CREATE INDEX IF NOT EXISTS idx_lp_job_student ON lp_ebraille_job(student_id);
CREATE INDEX IF NOT EXISTS idx_tactile_job_student ON tactile_graphics_job(student_id);
CREATE INDEX IF NOT EXISTS idx_print_job_student ON print_job(student_id);

CREATE INDEX IF NOT EXISTS idx_braille_job_delivered ON braille_job(delivered);
CREATE INDEX IF NOT EXISTS idx_lp_job_delivered ON lp_ebraille_job(delivered);
CREATE INDEX IF NOT EXISTS idx_tactile_job_delivered ON tactile_graphics_job(delivered);
CREATE INDEX IF NOT EXISTS idx_print_job_delivered ON print_job(delivered);

CREATE INDEX IF NOT EXISTS idx_metadata_event_job ON metadata_event(job_type, job_id);
CREATE INDEX IF NOT EXISTS idx_job_metadata_job ON job_metadata(job_type, job_id);
CREATE INDEX IF NOT EXISTS idx_job_file_link_job ON job_file_link(job_type, job_id);
CREATE INDEX IF NOT EXISTS idx_job_file_link_step ON job_file_link(job_type, job_id, step_key);

-- ═══════════════════════════════════════════════════════════════
-- SEED DATA
-- ═══════════════════════════════════════════════════════════════

INSERT OR IGNORE INTO printer (name, model) VALUES
    ('BambuLabs P1S',  'P1S'),
    ('Sovol SV08 Max', 'SV08 Max');

INSERT OR IGNORE INTO embosser (name, model, paper_type, notes) VALUES
    ('Index-D V5 Embosser', 'Index-D V5', 'pin_feed_11.5x11', 'Uses pin-feed paper'),
    ('ViewPlus Columbia Embosser', 'Columbia', 'pin_feed_11.5x11', 'Uses pin-feed paper'),
    ('ViewPlus Delta Embosser', 'Delta', 'sheet_feed_11.5x11', 'Uses sheet-feed paper');

INSERT OR IGNORE INTO material_category (section, value, label, sort_order) VALUES
    ('paper_type','sheet_feed_11.5x11',     'Sheet Feed 11.5×11',     1),
    ('paper_type','sheet_feed_8.5x11',      'Sheet Feed 8.5×11',      2),
    ('paper_type','pin_feed_11.5x11',       'Pin Feed 11.5×11',       3),
    ('paper_type','pin_feed_labels_8.5x11', 'Pin Feed Labels 8.5×11', 4),
    ('paper_type','generic_label',          'Generic Label',           5),
    ('elec_cat','board',       'TRRS Trinkey / Micro:bit', 1),
    ('elec_cat','microswitch', 'Microswitch',              2),
    ('elec_cat','wire',        'Wire',                     3),
    ('elec_cat','mono_jack',   'Mono Jack',                4),
    ('elec_cat','bolt_nut',    'Bolt / Nut',               5),
    ('elec_cat','hex_screw',   'Hex Screw',                6),
    ('elec_cat','solder',      'Solder',                   7),
    ('elec_cat','other',       'Other',                    8),
    ('elec_unit','pcs',  'pcs',  1),
    ('elec_unit','m',    'm',    2),
    ('elec_unit','g',    'g',    3),
    ('elec_unit','roll', 'roll', 4),
    ('elec_unit','ft',   'ft',   5),
    ('braille_type','literary', 'Literary', 1),
    ('braille_type','math',     'Math',     2),
    ('braille_type','science',  'Science',  3),
    ('braille_type','music',    'Music',    4),
    ('tactile_type','thermoform_swell',  'Thermoform / SWELL', 1),
    ('tactile_type','hand_tooled',       'Hand Tooled',        2),
    ('tactile_type','embossed_figures',  'Embossed Figures',   3),
    ('lp_type','large_print', 'Large Print', 1),
    ('lp_type','ebraille',    'eBraille',    2),
    ('lp_type','epub3_daisy', 'EPUB3 / DAISY', 3),
    ('metadata_dublin_core','dc:title',       'dc:title',       1),
    ('metadata_dublin_core','dc:creator',     'dc:creator',     2),
    ('metadata_dublin_core','dc:subject',     'dc:subject',     3),
    ('metadata_dublin_core','dc:description', 'dc:description', 4),
    ('metadata_dublin_core','dc:publisher',   'dc:publisher',   5),
    ('metadata_dublin_core','dc:contributor', 'dc:contributor', 6),
    ('metadata_dublin_core','dc:date',        'dc:date',        7),
    ('metadata_dublin_core','dc:type',        'dc:type',        8),
    ('metadata_dublin_core','dc:format',      'dc:format',      9),
    ('metadata_dublin_core','dc:identifier',  'dc:identifier',  10),
    ('metadata_dublin_core','dc:source',      'dc:source',      11),
    ('metadata_dublin_core','dc:language',    'dc:language',    12),
    ('metadata_dublin_core','dc:relation',    'dc:relation',    13),
    ('metadata_dublin_core','dc:coverage',    'dc:coverage',    14),
    ('metadata_dublin_core','dc:rights',      'dc:rights',      15),
    ('metadata_ebraille_profile','grade_level',             'grade_level',             1),
    ('metadata_ebraille_profile','subject_area',            'subject_area',            2),
    ('metadata_ebraille_profile','isbn',                    'isbn',                    3),
    ('metadata_ebraille_profile','oclc_number',             'oclc_number',             4),
    ('metadata_ebraille_profile','series',                  'series',                  5),
    ('metadata_ebraille_profile','volume',                  'volume',                  6),
    ('metadata_ebraille_profile','edition',                 'edition',                 7),
    ('metadata_ebraille_profile','transcriber',             'transcriber',             8),
    ('metadata_ebraille_profile','proofreader',             'proofreader',             9),
    ('metadata_ebraille_profile','embosser',                'embosser',                10),
    ('metadata_ebraille_profile','emboss_date',             'emboss_date',             11),
    ('metadata_ebraille_profile','braille_code',            'braille_code',            12),
    ('metadata_ebraille_profile','contracted_status',       'contracted_status',       13),
    ('metadata_ebraille_profile','nemeth_used',             'nemeth_used',             14),
    ('metadata_ebraille_profile','tactile_graphics_present','tactile_graphics_present',15),
    ('metadata_ebraille_profile','reading_level',           'reading_level',           16),
    ('metadata_mets_premis','mets:file_group',            'mets:file_group',            1),
    ('metadata_mets_premis','mets:div_type',              'mets:div_type',              2),
    ('metadata_mets_premis','mets:struct_order',          'mets:struct_order',          3),
    ('metadata_mets_premis','mets:amdsec_id',             'mets:amdsec_id',             4),
    ('metadata_mets_premis','premis:event_type',          'premis:event_type',          5),
    ('metadata_mets_premis','premis:event_datetime',      'premis:event_datetime',      6),
    ('metadata_mets_premis','premis:event_outcome',       'premis:event_outcome',       7),
    ('metadata_mets_premis','premis:agent',               'premis:agent',               8),
    ('metadata_mets_premis','premis:object_identifier',   'premis:object_identifier',   9),
    ('metadata_mets_premis','premis:rights_basis',        'premis:rights_basis',        10),
    ('metadata_mets_premis','premis:significant_properties','premis:significant_properties',11),
    ('metadata_mets_premis','premis:storage_location',    'premis:storage_location',    12),
    ('filament_type','PLA',   'PLA',   1),
    ('filament_type','PETG',  'PETG',  2),
    ('filament_type','ABS',   'ABS',   3),
    ('filament_type','TPU',   'TPU',   4),
    ('filament_type','ASA',   'ASA',   5),
    ('filament_type','Nylon', 'Nylon', 6),
    ('diameter_mm','1.75', '1.75 mm', 1),
    ('diameter_mm','2.85', '2.85 mm', 2),
    ('priority','low',    'Low',    1),
    ('priority','normal', 'Normal', 2),
    ('priority','high',   'High',   3),
    ('priority','urgent', 'Urgent', 4),
    -- FIX-011: standardised on ORIGINAL (was MASTER)
    ('file_use','ORIGINAL',     'Original',     1),
    ('file_use','DERIVATIVE',   'Derivative',   2),
    ('file_use','INTERMEDIATE', 'Intermediate', 3),
    ('file_use','SOURCE',       'Source',       4),
    ('file_use','REFERENCE',    'Reference',    5),
    ('braille_format','BRF',  'BRF',  1),
    ('braille_format','BRL',  'BRL',  2),
    ('braille_format','EBRF', 'EBRF', 3),
    ('braille_format','PDF',  'PDF',  4),
    ('braille_format','DOCX', 'DOCX', 5),
    ('braille_format','EPUB', 'EPUB', 6),
    ('print_format','3MF',   '3MF',   1),
    ('print_format','STL',   'STL',   2),
    ('print_format','GCODE', 'G-Code',3),
    -- FIX-016: delivery method options
    ('delivery_method','physical',  'Physical Copy',             1),
    ('delivery_method','email',     'Email',                     2),
    ('delivery_method','lms',       'Learning Management System',3),
    ('delivery_method','usb',       'USB / Media',               4),
    ('delivery_method','pickup',    'Pickup',                    5),
    ('delivery_method','other',     'Other',                     6);

INSERT OR IGNORE INTO workflow_step (job_type, step_key, label, description, sort_order) VALUES
    ('braille','digitized','Digitized', 'Source document scanned or received',          1),
    ('braille','formatted','Formatted', 'Document formatted for braille transcription',  2),
    ('braille','brailled', 'Brailled',  'Braille translation completed',                 3),
    ('braille','proofread','Proofread', 'Braille output proofread and verified',         4),
    ('braille','delivered','Delivered', 'Final files and/or embossed copies delivered',  5),
    ('lp_ebraille','digitized', 'Digitized',            'Source document received',              1),
    ('lp_ebraille','formatted', 'Formatted',            'Document formatted for output',          2),
    ('lp_ebraille','converted', 'eBraille / Large Print','Conversion to target format complete',  3),
    ('lp_ebraille','proofread', 'Proofread',            'Output proofread and verified',          4),
    ('lp_ebraille','delivered', 'Delivered',            'Final files delivered',                  5),
    ('tactile','designed',   'Designed',    'Figure or diagram design prepared',                 1),
    ('tactile','produced',   'Produced',    'Tactile graphic manufactured',                       2),
    ('tactile','qa_reviewed','QA Reviewed', 'Tactile output checked for accessibility',           3),
    ('tactile','delivered',  'Delivered',   'Final tactile graphic delivered',                    4),
    -- FIX-007: print workflow steps now enforced in schema
    ('print','designed',  'Designed',  'CAD/3D model obtained or designed',             1),
    ('print','sliced',    'Sliced',    'Model sliced; G-code generated',                2),
    ('print','printed',   'Printed',   'Print job completed',                           3),
    ('print','inspected', 'Inspected', 'Print inspected for quality',                   4),
    ('print','delivered', 'Delivered', 'Object delivered to requester',                 5);
"""


def _table_has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()  # noqa: S608 - table names are internal migration constants.
    return any(row[1] == column for row in rows)


def _ensure_migration_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migration (
            migration_id TEXT PRIMARY KEY,
            applied_at   TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )


def _migration_applied(conn: sqlite3.Connection, migration_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM schema_migration WHERE migration_id = ?",
        (migration_id,),
    ).fetchone()
    return row is not None


def _mark_migration_applied(conn: sqlite3.Connection, migration_id: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO schema_migration (migration_id) VALUES (?)",
        (migration_id,),
    )


def _apply_migration(conn: sqlite3.Connection, migration_id: str, fn) -> None:
    if _migration_applied(conn, migration_id):
        return
    fn()
    _mark_migration_applied(conn, migration_id)


def _migrate(conn: sqlite3.Connection) -> None:
    """Apply incremental schema migrations to existing databases."""
    _ensure_migration_table(conn)

    # ── Pre-existing migrations ───────────────────────────────────────────────
    def _m001_braille_embosser_and_timestamps() -> None:
        if not _table_has_column(conn, "braille_job", "embosser_id"):
            conn.execute(
                "ALTER TABLE braille_job ADD COLUMN embosser_id INTEGER REFERENCES embosser(id)"
            )

        for tbl in ("printer", "embosser"):
            if not _table_has_column(conn, tbl, "created_at"):
                conn.execute(f"ALTER TABLE {tbl} ADD COLUMN created_at TEXT")  # noqa: S608 - tbl is selected from a fixed tuple.
            if not _table_has_column(conn, tbl, "updated_at"):
                conn.execute(f"ALTER TABLE {tbl} ADD COLUMN updated_at TEXT")  # noqa: S608 - tbl is selected from a fixed tuple.

    _apply_migration(conn, "m001_braille_embosser_and_timestamps", _m001_braille_embosser_and_timestamps)

    def _m002_workflow_step_columns() -> None:
        if not _table_has_column(conn, "workflow_step", "updated_at"):
            conn.execute("ALTER TABLE workflow_step ADD COLUMN updated_at TEXT")

        if not _table_has_column(conn, "workflow_step", "description"):
            conn.execute("ALTER TABLE workflow_step ADD COLUMN description TEXT")

    _apply_migration(conn, "m002_workflow_step_columns", _m002_workflow_step_columns)

    def _m003_backup_log_table() -> None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS backup_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_path TEXT NOT NULL,
                size_bytes  INTEGER,
                trigger     TEXT NOT NULL DEFAULT 'scheduled',
                status      TEXT NOT NULL DEFAULT 'ok',
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)

    _apply_migration(conn, "m003_backup_log_table", _m003_backup_log_table)

    # ── FIX-010: student table and student_id FK columns ─────────────────────
    def _m004_student_table_and_links() -> None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS student (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                last_name         TEXT NOT NULL,
                first_name        TEXT NOT NULL,
                school            TEXT,
                grade             TEXT,
                preferred_formats TEXT,
                notes             TEXT,
                active            INTEGER DEFAULT 1,
                created_at        TEXT DEFAULT (datetime('now')),
                updated_at        TEXT DEFAULT (datetime('now'))
            )
        """)

        for tbl in ("braille_job", "lp_ebraille_job", "tactile_graphics_job", "print_job"):
            if not _table_has_column(conn, tbl, "student_id"):
                conn.execute(
                    f"ALTER TABLE {tbl} ADD COLUMN student_id INTEGER REFERENCES student(id)"  # noqa: S608 - tbl is selected from a fixed tuple.
                )

    _apply_migration(conn, "m004_student_table_and_links", _m004_student_table_and_links)

    # ── FIX-007: print_job workflow step columns ──────────────────────────────
    def _m005_print_step_columns() -> None:
        for col in ("designed", "sliced", "printed", "inspected", "delivered"):
            if not _table_has_column(conn, "print_job", col):
                conn.execute(
                    f"ALTER TABLE print_job ADD COLUMN {col} INTEGER DEFAULT 0"  # noqa: S608 - col is selected from a fixed tuple.
                )

    _apply_migration(conn, "m005_print_step_columns", _m005_print_step_columns)

    # ── FIX-016: delivery tracking columns on all job tables ─────────────────
    def _m006_delivery_columns() -> None:
        delivery_cols = [
            ("delivery_date",      "TEXT"),
            ("delivery_method",    "TEXT"),
            ("delivery_recipient", "TEXT"),
            ("delivery_notes",     "TEXT"),
        ]
        for tbl in ("braille_job", "lp_ebraille_job", "tactile_graphics_job", "print_job"):
            for col, col_type in delivery_cols:
                if not _table_has_column(conn, tbl, col):
                    conn.execute(
                        f"ALTER TABLE {tbl} ADD COLUMN {col} {col_type}"  # noqa: S608 - tbl/col/col_type are from fixed migration constants.
                    )

    _apply_migration(conn, "m006_delivery_columns", _m006_delivery_columns)

    # ── FIX-011: normalise MASTER → ORIGINAL in existing records ─────────────
    def _m007_normalize_file_use_master() -> None:
        conn.execute(
            "UPDATE file_object SET file_use = 'ORIGINAL' WHERE file_use = 'MASTER'"
        )
        conn.execute(
            "UPDATE material_category SET value='ORIGINAL', label='Original' "
            "WHERE section='file_use' AND value='MASTER'"
        )

    _apply_migration(conn, "m007_normalize_file_use_master", _m007_normalize_file_use_master)

    # ── IMP-022: workflow step timestamp columns ────────────────────────────
    def _m008_step_completion_timestamps() -> None:
        step_columns = {
            "braille_job": ["digitized", "formatted", "brailled", "proofread", "delivered"],
            "lp_ebraille_job": ["digitized", "formatted", "converted", "proofread", "delivered"],
            "tactile_graphics_job": ["designed", "produced", "qa_reviewed", "delivered"],
            "print_job": ["designed", "sliced", "printed", "inspected", "delivered"],
        }
        for table, steps in step_columns.items():
            for step in steps:
                date_col = f"{step}_date"
                if not _table_has_column(conn, table, date_col):
                    conn.execute(
                        f"ALTER TABLE {table} ADD COLUMN {date_col} TEXT"  # noqa: S608 - table/column values are fixed migration constants.
                    )

    _apply_migration(conn, "m008_step_completion_timestamps", _m008_step_completion_timestamps)

    # ── IMP-023: FTS5 search indexes and change triggers ────────────────────
    def _m009_full_text_search_indexes() -> None:
        conn.executescript(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS braille_job_fts USING fts5(
                id UNINDEXED,
                title,
                requester,
                notes
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS lp_ebraille_job_fts USING fts5(
                id UNINDEXED,
                title,
                requester,
                notes
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS tactile_graphics_job_fts USING fts5(
                id UNINDEXED,
                title,
                requester,
                notes
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS print_job_fts USING fts5(
                id UNINDEXED,
                object_name,
                file_name,
                requester,
                notes
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS file_object_fts USING fts5(
                id UNINDEXED,
                original_name,
                stored_path,
                format_name,
                encoding
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS job_metadata_fts USING fts5(
                row_key UNINDEXED,
                job_type,
                job_id,
                meta_key,
                meta_value
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS metadata_event_fts USING fts5(
                id UNINDEXED,
                job_type,
                job_id,
                event_type,
                agent,
                detail
            );

            CREATE TRIGGER IF NOT EXISTS braille_job_ai AFTER INSERT ON braille_job BEGIN
                INSERT INTO braille_job_fts (id, title, requester, notes)
                VALUES (new.id, COALESCE(new.title, ''), COALESCE(new.requester, ''), COALESCE(new.notes, ''));
            END;
            CREATE TRIGGER IF NOT EXISTS braille_job_au AFTER UPDATE ON braille_job BEGIN
                DELETE FROM braille_job_fts WHERE id = old.id;
                INSERT INTO braille_job_fts (id, title, requester, notes)
                VALUES (new.id, COALESCE(new.title, ''), COALESCE(new.requester, ''), COALESCE(new.notes, ''));
            END;
            CREATE TRIGGER IF NOT EXISTS braille_job_ad AFTER DELETE ON braille_job BEGIN
                DELETE FROM braille_job_fts WHERE id = old.id;
            END;

            CREATE TRIGGER IF NOT EXISTS lp_ebraille_job_ai AFTER INSERT ON lp_ebraille_job BEGIN
                INSERT INTO lp_ebraille_job_fts (id, title, requester, notes)
                VALUES (new.id, COALESCE(new.title, ''), COALESCE(new.requester, ''), COALESCE(new.notes, ''));
            END;
            CREATE TRIGGER IF NOT EXISTS lp_ebraille_job_au AFTER UPDATE ON lp_ebraille_job BEGIN
                DELETE FROM lp_ebraille_job_fts WHERE id = old.id;
                INSERT INTO lp_ebraille_job_fts (id, title, requester, notes)
                VALUES (new.id, COALESCE(new.title, ''), COALESCE(new.requester, ''), COALESCE(new.notes, ''));
            END;
            CREATE TRIGGER IF NOT EXISTS lp_ebraille_job_ad AFTER DELETE ON lp_ebraille_job BEGIN
                DELETE FROM lp_ebraille_job_fts WHERE id = old.id;
            END;

            CREATE TRIGGER IF NOT EXISTS tactile_graphics_job_ai AFTER INSERT ON tactile_graphics_job BEGIN
                INSERT INTO tactile_graphics_job_fts (id, title, requester, notes)
                VALUES (new.id, COALESCE(new.title, ''), COALESCE(new.requester, ''), COALESCE(new.notes, ''));
            END;
            CREATE TRIGGER IF NOT EXISTS tactile_graphics_job_au AFTER UPDATE ON tactile_graphics_job BEGIN
                DELETE FROM tactile_graphics_job_fts WHERE id = old.id;
                INSERT INTO tactile_graphics_job_fts (id, title, requester, notes)
                VALUES (new.id, COALESCE(new.title, ''), COALESCE(new.requester, ''), COALESCE(new.notes, ''));
            END;
            CREATE TRIGGER IF NOT EXISTS tactile_graphics_job_ad AFTER DELETE ON tactile_graphics_job BEGIN
                DELETE FROM tactile_graphics_job_fts WHERE id = old.id;
            END;

            CREATE TRIGGER IF NOT EXISTS print_job_ai AFTER INSERT ON print_job BEGIN
                INSERT INTO print_job_fts (id, object_name, file_name, requester, notes)
                VALUES (new.id, COALESCE(new.object_name, ''), COALESCE(new.file_name, ''), COALESCE(new.requester, ''), COALESCE(new.notes, ''));
            END;
            CREATE TRIGGER IF NOT EXISTS print_job_au AFTER UPDATE ON print_job BEGIN
                DELETE FROM print_job_fts WHERE id = old.id;
                INSERT INTO print_job_fts (id, object_name, file_name, requester, notes)
                VALUES (new.id, COALESCE(new.object_name, ''), COALESCE(new.file_name, ''), COALESCE(new.requester, ''), COALESCE(new.notes, ''));
            END;
            CREATE TRIGGER IF NOT EXISTS print_job_ad AFTER DELETE ON print_job BEGIN
                DELETE FROM print_job_fts WHERE id = old.id;
            END;

            CREATE TRIGGER IF NOT EXISTS file_object_ai AFTER INSERT ON file_object BEGIN
                INSERT INTO file_object_fts (id, original_name, stored_path, format_name, encoding)
                VALUES (new.id, COALESCE(new.original_name, ''), COALESCE(new.stored_path, ''), COALESCE(new.format_name, ''), COALESCE(new.encoding, ''));
            END;
            CREATE TRIGGER IF NOT EXISTS file_object_au AFTER UPDATE ON file_object BEGIN
                DELETE FROM file_object_fts WHERE id = old.id;
                INSERT INTO file_object_fts (id, original_name, stored_path, format_name, encoding)
                VALUES (new.id, COALESCE(new.original_name, ''), COALESCE(new.stored_path, ''), COALESCE(new.format_name, ''), COALESCE(new.encoding, ''));
            END;
            CREATE TRIGGER IF NOT EXISTS file_object_ad AFTER DELETE ON file_object BEGIN
                DELETE FROM file_object_fts WHERE id = old.id;
            END;

            CREATE TRIGGER IF NOT EXISTS job_metadata_ai AFTER INSERT ON job_metadata BEGIN
                INSERT INTO job_metadata_fts (row_key, job_type, job_id, meta_key, meta_value)
                VALUES (CAST(new.id AS TEXT), COALESCE(new.job_type, ''), CAST(COALESCE(new.job_id, 0) AS TEXT), COALESCE(new.meta_key, ''), COALESCE(new.meta_value, ''));
            END;
            CREATE TRIGGER IF NOT EXISTS job_metadata_au AFTER UPDATE ON job_metadata BEGIN
                DELETE FROM job_metadata_fts WHERE row_key = CAST(old.id AS TEXT);
                INSERT INTO job_metadata_fts (row_key, job_type, job_id, meta_key, meta_value)
                VALUES (CAST(new.id AS TEXT), COALESCE(new.job_type, ''), CAST(COALESCE(new.job_id, 0) AS TEXT), COALESCE(new.meta_key, ''), COALESCE(new.meta_value, ''));
            END;
            CREATE TRIGGER IF NOT EXISTS job_metadata_ad AFTER DELETE ON job_metadata BEGIN
                DELETE FROM job_metadata_fts WHERE row_key = CAST(old.id AS TEXT);
            END;

            CREATE TRIGGER IF NOT EXISTS metadata_event_ai AFTER INSERT ON metadata_event BEGIN
                INSERT INTO metadata_event_fts (id, job_type, job_id, event_type, agent, detail)
                VALUES (new.id, COALESCE(new.job_type, ''), CAST(COALESCE(new.job_id, 0) AS TEXT), COALESCE(new.event_type, ''), COALESCE(new.agent, ''), COALESCE(new.detail, ''));
            END;
            CREATE TRIGGER IF NOT EXISTS metadata_event_au AFTER UPDATE ON metadata_event BEGIN
                DELETE FROM metadata_event_fts WHERE id = old.id;
                INSERT INTO metadata_event_fts (id, job_type, job_id, event_type, agent, detail)
                VALUES (new.id, COALESCE(new.job_type, ''), CAST(COALESCE(new.job_id, 0) AS TEXT), COALESCE(new.event_type, ''), COALESCE(new.agent, ''), COALESCE(new.detail, ''));
            END;
            CREATE TRIGGER IF NOT EXISTS metadata_event_ad AFTER DELETE ON metadata_event BEGIN
                DELETE FROM metadata_event_fts WHERE id = old.id;
            END;
            """
        )

        # Seed indexes for existing rows (safe to run once due migration tracking).
        conn.execute("INSERT INTO braille_job_fts (id, title, requester, notes) SELECT id, COALESCE(title, ''), COALESCE(requester, ''), COALESCE(notes, '') FROM braille_job")
        conn.execute("INSERT INTO lp_ebraille_job_fts (id, title, requester, notes) SELECT id, COALESCE(title, ''), COALESCE(requester, ''), COALESCE(notes, '') FROM lp_ebraille_job")
        conn.execute("INSERT INTO tactile_graphics_job_fts (id, title, requester, notes) SELECT id, COALESCE(title, ''), COALESCE(requester, ''), COALESCE(notes, '') FROM tactile_graphics_job")
        conn.execute("INSERT INTO print_job_fts (id, object_name, file_name, requester, notes) SELECT id, COALESCE(object_name, ''), COALESCE(file_name, ''), COALESCE(requester, ''), COALESCE(notes, '') FROM print_job")
        conn.execute("INSERT INTO file_object_fts (id, original_name, stored_path, format_name, encoding) SELECT id, COALESCE(original_name, ''), COALESCE(stored_path, ''), COALESCE(format_name, ''), COALESCE(encoding, '') FROM file_object")
        conn.execute("INSERT INTO job_metadata_fts (row_key, job_type, job_id, meta_key, meta_value) SELECT CAST(id AS TEXT), COALESCE(job_type, ''), CAST(COALESCE(job_id, 0) AS TEXT), COALESCE(meta_key, ''), COALESCE(meta_value, '') FROM job_metadata")
        conn.execute("INSERT INTO metadata_event_fts (id, job_type, job_id, event_type, agent, detail) SELECT id, COALESCE(job_type, ''), CAST(COALESCE(job_id, 0) AS TEXT), COALESCE(event_type, ''), COALESCE(agent, ''), COALESCE(detail, '') FROM metadata_event")

    _apply_migration(conn, "m009_full_text_search_indexes", _m009_full_text_search_indexes)

    def _m010_step_date_columns() -> None:
        """Add *_date tracking columns for each workflow step."""
        step_pairs: list[tuple[str, str]] = [
            ("braille_job",           "digitized_date"),
            ("braille_job",           "formatted_date"),
            ("braille_job",           "brailled_date"),
            ("braille_job",           "proofread_date"),
            ("braille_job",           "delivered_date"),
            ("lp_ebraille_job",       "digitized_date"),
            ("lp_ebraille_job",       "formatted_date"),
            ("lp_ebraille_job",       "converted_date"),
            ("lp_ebraille_job",       "proofread_date"),
            ("lp_ebraille_job",       "delivered_date"),
            ("tactile_graphics_job",  "designed_date"),
            ("tactile_graphics_job",  "produced_date"),
            ("tactile_graphics_job",  "qa_reviewed_date"),
            ("tactile_graphics_job",  "delivered_date"),
            ("print_job",             "designed_date"),
            ("print_job",             "sliced_date"),
            ("print_job",             "printed_date"),
            ("print_job",             "inspected_date"),
            ("print_job",             "delivered_date"),
        ]
        for table, col in step_pairs:
            if not _table_has_column(conn, table, col):
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT")  # noqa: S608 - table/col come from fixed in-function constants.

    _apply_migration(conn, "m010_step_date_columns", _m010_step_date_columns)


def init_db() -> None:
    """Create all tables, directories, and seed data if they do not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PRINTS_DIR.mkdir(exist_ok=True)
    FILES_DIR.mkdir(exist_ok=True)
    BACKUPS_DIR.mkdir(exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.executescript(_SCHEMA_SQL)
        _migrate(conn)
    _validate_step_columns()


_STEP_DATE_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "braille_job":          [("digitized", "digitized_date"), ("formatted", "formatted_date"),
                             ("brailled", "brailled_date"), ("proofread", "proofread_date"),
                             ("delivered", "delivered_date")],
    "lp_ebraille_job":      [("digitized", "digitized_date"), ("formatted", "formatted_date"),
                             ("converted", "converted_date"), ("proofread", "proofread_date"),
                             ("delivered", "delivered_date")],
    "tactile_graphics_job": [("designed", "designed_date"), ("produced", "produced_date"),
                             ("qa_reviewed", "qa_reviewed_date"), ("delivered", "delivered_date")],
    "print_job":            [("designed", "designed_date"), ("sliced", "sliced_date"),
                             ("printed", "printed_date"), ("inspected", "inspected_date"),
                             ("delivered", "delivered_date")],
}


def _validate_step_columns() -> None:
    """Verify every _date column for each step exists in the actual table schema."""
    import logging as _logging
    log = _logging.getLogger(__name__)
    missing: list[str] = []
    with get_conn() as conn:
        for table, pairs in _STEP_DATE_COLUMNS.items():
            existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}  # noqa: S608
            for step, date_col in pairs:
                if date_col not in existing:
                    missing.append(f"{table}.{date_col} (step: {step})")
    if missing:
        raise RuntimeError(
            "Database schema is missing step date columns. "
            "Run a migration to add them before starting the app.\n"
            + "\n".join(f"  - {m}" for m in missing)
        )
    log.debug("Step column validation passed (%d tables).", len(_STEP_DATE_COLUMNS))
