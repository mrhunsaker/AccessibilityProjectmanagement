"""
Database schema, connection helpers, and initialisation.

This is the SOLE database initialisation path.  All other modules that
previously imported from db.database should import from here instead.

Schema is METS/PREMIS-inspired:
  file_object         ≈  METS <fileSec>/<file>
  job_file_link       ≈  METS <structMap> pointer
  structural_map_node ≈  METS <structMap>/<div> hierarchy
  metadata_event      ≈  PREMIS event record
  job_metadata        ≈  Dublin-Core descriptive metadata
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

DB_PATH       = Path(__file__).parent.parent / "accessibility_manager.db"
PRINTS_DIR    = Path(__file__).parent.parent / "prints_files"
FILES_DIR     = Path(__file__).parent.parent / "job_files"
BACKUPS_DIR   = Path(__file__).parent.parent / "backups"
# Artifacts are stored one level above the package so the folder lives at the
# repository / project root: <repo root>/artifacts/<project title>/
ARTIFACTS_DIR = Path(__file__).parent.parent.parent / "artifacts"


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
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id      INTEGER NOT NULL REFERENCES printer(id),
    filament_id     INTEGER REFERENCES filament(id),
    filament_used_g REAL,
    file_path       TEXT,
    file_name       TEXT,
    successful      INTEGER NOT NULL DEFAULT 1,
    failure_reason  TEXT,
    object_name     TEXT,
    requester       TEXT,
    request_date    TEXT,
    notes           TEXT,
    printed_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
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
    file_use         TEXT NOT NULL DEFAULT 'MASTER',
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

-- workflow_step now includes updated_at for consistency with all other mutable tables
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
-- BACKUP LOG (tracks automated and manual backup runs)
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS backup_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_path TEXT NOT NULL,
    size_bytes  INTEGER,
    trigger     TEXT NOT NULL DEFAULT 'scheduled',
    status      TEXT NOT NULL DEFAULT 'ok',
    created_at  TEXT DEFAULT (datetime('now'))
);

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
    ('file_use','MASTER',       'Master',       1),
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
    ('print_format','GCODE', 'G-Code',3);

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
    ('print','designed',  'Designed',  'CAD/3D model obtained or designed',             1),
    ('print','sliced',    'Sliced',    'Model sliced; G-code generated',                2),
    ('print','printed',   'Printed',   'Print job completed',                           3),
    ('print','inspected', 'Inspected', 'Print inspected for quality',                   4),
    ('print','delivered', 'Delivered', 'Object delivered to requester',                 5);
"""


def _table_has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """ table has column.
    
    Parameters
    ----------
    conn : Any
        conn parameter.
    
    table : Any
        table parameter.
    
    column : Any
        column parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()  # noqa: S608
    return any(row[1] == column for row in rows)


def _migrate(conn: sqlite3.Connection) -> None:
    """Apply incremental schema migrations to existing databases."""
    # braille_job.embosser_id — added post-initial release
    if not _table_has_column(conn, "braille_job", "embosser_id"):
        conn.execute(
            "ALTER TABLE braille_job ADD COLUMN embosser_id INTEGER REFERENCES embosser(id)"
        )

    # printer / embosser — add created_at / updated_at if absent (older DBs)
    for tbl in ("printer", "embosser"):
        if not _table_has_column(conn, tbl, "created_at"):
            conn.execute(f"ALTER TABLE {tbl} ADD COLUMN created_at TEXT")  # noqa: S608
        if not _table_has_column(conn, tbl, "updated_at"):
            conn.execute(f"ALTER TABLE {tbl} ADD COLUMN updated_at TEXT")  # noqa: S608

    # workflow_step — add updated_at if absent (pre-fix databases)
    if not _table_has_column(conn, "workflow_step", "updated_at"):
        conn.execute(
            "ALTER TABLE workflow_step ADD COLUMN updated_at TEXT"
        )

    # workflow_step — add description if absent
    if not _table_has_column(conn, "workflow_step", "description"):
        conn.execute(
            "ALTER TABLE workflow_step ADD COLUMN description TEXT"
        )

    # backup_log — new table added for automated backup tracking
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


def init_db() -> None:
    """Create all tables, directories, and seed data if they do not exist."""
    PRINTS_DIR.mkdir(exist_ok=True)
    FILES_DIR.mkdir(exist_ok=True)
    BACKUPS_DIR.mkdir(exist_ok=True)
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    with get_conn() as conn:
        conn.executescript(_SCHEMA_SQL)
        _migrate(conn)
