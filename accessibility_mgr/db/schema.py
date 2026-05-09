"""
Database schema and initialization helpers.

This module defines the complete SQLite schema for the Accessibility Materials
Project Manager. It includes:

  - Inventory tables (filament, paper, electronics)
  - Job tracking tables (braille, large-print/eBraille, 3-D print)
  - A METS-inspired metadata/provenance system that records every workflow
    step, intermediate file, and structural-metadata event for every job.
  - A file-object registry that stores checksums, MIME types, and arbitrary
    key-value metadata for every file attached to any job or step.
  - Configurable lookup tables (material_category, workflow_step) so new
    material types and workflow stages can be added without schema changes.

METS analogy
------------
  job_metadata_event  ≈  METS <amdSec>/<digiprovMD>/<mdWrap> (PREMIS events)
  job_file_object     ≈  METS <fileSec>/<file>
  job_file_link       ≈  Links file objects to jobs and/or steps (structMap)
  job_structural_map  ≈  METS <structMap> div hierarchy per job
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "project_manager.db"
PRINTS_DIR = Path(__file__).parent.parent / "prints_files"
FILES_DIR = Path(__file__).parent.parent / "job_files"


@contextmanager
def get_conn() -> Generator[sqlite3.Connection, None, None]:
    """Yield a configured SQLite connection with commit/rollback/close lifecycle."""
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
-- ═══════════════════════════════════════════════════════════════════════════
-- INVENTORY TABLES
-- ═══════════════════════════════════════════════════════════════════════════

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

-- ═══════════════════════════════════════════════════════════════════════════
-- PRINTER REFERENCE
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS printer (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL UNIQUE,
    model TEXT,
    notes TEXT
);

-- ═══════════════════════════════════════════════════════════════════════════
-- 3-D PRINT JOBS
-- ═══════════════════════════════════════════════════════════════════════════

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

-- ═══════════════════════════════════════════════════════════════════════════
-- BRAILLE JOBS
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS braille_job (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    braille_type TEXT NOT NULL,
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

-- ═══════════════════════════════════════════════════════════════════════════
-- LARGE PRINT / eBRAILLE JOBS
-- ═══════════════════════════════════════════════════════════════════════════

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

-- ═══════════════════════════════════════════════════════════════════════════
-- METS-INSPIRED METADATA SYSTEM
-- ═══════════════════════════════════════════════════════════════════════════

-- FILE OBJECT REGISTRY
-- Every file (source, intermediate, final) gets one row here with a stable
-- UUID, checksum, MIME type, and arbitrary JSON metadata.
-- Analogous to METS <fileSec>/<file> + <FContent>/<FLocat>
CREATE TABLE IF NOT EXISTS file_object (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid          TEXT NOT NULL UNIQUE,          -- stable identifier
    original_name TEXT NOT NULL,
    stored_path   TEXT NOT NULL,                  -- relative to FILES_DIR
    mime_type     TEXT,
    size_bytes    INTEGER,
    checksum_sha256 TEXT,
    file_use      TEXT NOT NULL DEFAULT 'MASTER', -- MASTER|DERIVATIVE|INTERMEDIATE|SOURCE|REFERENCE
    format_name   TEXT,                           -- e.g. 'BRF', 'BRL', 'PDF', '3MF', 'STL'
    format_version TEXT,
    encoding      TEXT,
    extra_metadata TEXT,                          -- JSON blob for arbitrary key-value pairs
    created_at    TEXT DEFAULT (datetime('now')),
    updated_at    TEXT DEFAULT (datetime('now'))
);

-- JOB FILE LINK
-- Associates a file_object with a job (and optionally a workflow step).
-- Analogous to METS <structMap> entries.
CREATE TABLE IF NOT EXISTS job_file_link (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    file_object_id INTEGER NOT NULL REFERENCES file_object(id),
    job_type      TEXT NOT NULL,   -- 'braille'|'lp_ebraille'|'print'
    job_id        INTEGER NOT NULL,
    step_key      TEXT,            -- which workflow step this file belongs to (nullable = job-level)
    sequence_num  INTEGER DEFAULT 0,
    created_at    TEXT DEFAULT (datetime('now'))
);

-- METADATA EVENT LOG (PREMIS-style provenance)
-- Every significant action on a job is recorded here: step transitions,
-- file ingests, QA checks, manual edits, corrections, delivery confirmations.
-- Analogous to METS <amdSec>/<digiprovMD> PREMIS:event elements.
CREATE TABLE IF NOT EXISTS metadata_event (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type      TEXT NOT NULL,
    job_id        INTEGER NOT NULL,
    event_type    TEXT NOT NULL,    -- 'CREATE'|'INGEST'|'TRANSFORM'|'QA_CHECK'|'VALIDATE'
                                    -- |'MIGRATION'|'DELIVER'|'NOTE'|'STEP_COMPLETE'|'STEP_REVERT'
    event_outcome TEXT,             -- 'SUCCESS'|'FAILURE'|'WARNING'
    step_key      TEXT,             -- which step this event relates to (nullable)
    file_object_id INTEGER REFERENCES file_object(id),
    agent         TEXT,             -- who/what performed the action
    detail        TEXT,             -- human-readable description
    extra_metadata TEXT,            -- JSON blob for tool names, parameters, etc.
    event_datetime TEXT DEFAULT (datetime('now'))
);

-- STRUCTURAL MAP (job-level document hierarchy)
-- Allows recording the logical structure of multi-part jobs
-- (e.g. a textbook with chapters, a music score with movements).
-- Analogous to METS <structMap>/<div>.
CREATE TABLE IF NOT EXISTS structural_map_node (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type      TEXT NOT NULL,
    job_id        INTEGER NOT NULL,
    parent_id     INTEGER REFERENCES structural_map_node(id),
    label         TEXT NOT NULL,
    div_type      TEXT DEFAULT 'section',  -- 'volume'|'chapter'|'section'|'page'|'part'
    order_num     INTEGER DEFAULT 0,
    file_object_id INTEGER REFERENCES file_object(id),  -- optional file for this node
    created_at    TEXT DEFAULT (datetime('now'))
);

-- JOB METADATA (descriptive metadata, Dublin Core-inspired)
-- Stores key-value descriptive metadata for any job.
-- Analogous to METS <dmdSec>/<mdWrap> Dublin Core fields.
CREATE TABLE IF NOT EXISTS job_metadata (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type   TEXT NOT NULL,
    job_id     INTEGER NOT NULL,
    meta_key   TEXT NOT NULL,   -- e.g. 'dc:title', 'dc:creator', 'dc:subject', 'grade_level'
    meta_value TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(job_type, job_id, meta_key)
);

-- ═══════════════════════════════════════════════════════════════════════════
-- CONFIGURABLE LOOKUP TABLES
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS material_category (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    section     TEXT NOT NULL,
    value       TEXT NOT NULL,
    label       TEXT NOT NULL,
    sort_order  INTEGER DEFAULT 0,
    active      INTEGER DEFAULT 1,
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now')),
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

-- ═══════════════════════════════════════════════════════════════════════════
-- SEED DATA
-- ═══════════════════════════════════════════════════════════════════════════

INSERT OR IGNORE INTO printer (name, model) VALUES
    ('BambuLabs P1S', 'P1S'),
    ('Sovol SV08 Max', 'SV08 Max');

INSERT OR IGNORE INTO material_category (section, value, label, sort_order) VALUES
    -- Paper types
    ('paper_type','sheet_feed_11.5x11',     'Sheet Feed 11.5×11',      1),
    ('paper_type','sheet_feed_8.5x11',      'Sheet Feed 8.5×11',       2),
    ('paper_type','pin_feed_11.5x11',       'Pin Feed 11.5×11',        3),
    ('paper_type','pin_feed_labels_8.5x11', 'Pin Feed Labels 8.5×11',  4),
    ('paper_type','generic_label',          'Generic Label',            5),
    -- Electronics categories
    ('elec_cat','board',       'TRRS Trinkey / Micro:bit Board', 1),
    ('elec_cat','microswitch', 'Microswitch',                    2),
    ('elec_cat','wire',        'Wire',                           3),
    ('elec_cat','mono_jack',   'Mono Jack',                      4),
    ('elec_cat','bolt_nut',    'Bolt / Nut',                     5),
    ('elec_cat','hex_screw',   'Hex Screw',                      6),
    ('elec_cat','solder',      'Solder',                         7),
    ('elec_cat','other',       'Other',                          8),
    -- Electronics units
    ('elec_unit','pcs',  'pcs',  1),
    ('elec_unit','m',    'm',    2),
    ('elec_unit','g',    'g',    3),
    ('elec_unit','roll', 'roll', 4),
    ('elec_unit','ft',   'ft',   5),
    -- Braille types
    ('braille_type','literary', 'Literary', 1),
    ('braille_type','math',     'Math',     2),
    ('braille_type','science',  'Science',  3),
    ('braille_type','music',    'Music',    4),
    -- LP/eBraille types
    ('lp_type','large_print', 'Large Print', 1),
    ('lp_type','ebraille',    'eBraille',    2),
    -- Filament types
    ('filament_type','PLA',   'PLA',   1),
    ('filament_type','PETG',  'PETG',  2),
    ('filament_type','ABS',   'ABS',   3),
    ('filament_type','TPU',   'TPU',   4),
    ('filament_type','ASA',   'ASA',   5),
    ('filament_type','Nylon', 'Nylon', 6),
    -- Diameters
    ('diameter_mm','1.75', '1.75 mm', 1),
    ('diameter_mm','2.85', '2.85 mm', 2),
    -- Job priorities
    ('priority','low',    'Low',    1),
    ('priority','normal', 'Normal', 2),
    ('priority','high',   'High',   3),
    ('priority','urgent', 'Urgent', 4),
    -- File use categories
    ('file_use','MASTER',       'Master',        1),
    ('file_use','DERIVATIVE',   'Derivative',    2),
    ('file_use','INTERMEDIATE', 'Intermediate',  3),
    ('file_use','SOURCE',       'Source',        4),
    ('file_use','REFERENCE',    'Reference',     5),
    -- Braille file formats
    ('braille_format','BRF',   'BRF (Braille Ready Format)', 1),
    ('braille_format','BRL',   'BRL (Braille)',               2),
    ('braille_format','BRA',   'BRA',                         3),
    ('braille_format','EBRF',  'EBRF (eBraille)',             4),
    ('braille_format','BES',   'BES',                         5),
    ('braille_format','PDF',   'PDF',                         6),
    ('braille_format','DOCX',  'DOCX',                        7),
    ('braille_format','ODT',   'ODT',                         8),
    ('braille_format','TXT',   'TXT',                         9),
    ('braille_format','XML',   'XML',                        10),
    ('braille_format','HTML',  'HTML',                       11),
    ('braille_format','EPUB',  'EPUB',                       12),
    ('braille_format','MUS',   'MusicXML / MUS',             13),
    -- 3D print formats
    ('print_format','3MF',    '3MF',             1),
    ('print_format','STL',    'STL',             2),
    ('print_format','GCODE',  'G-Code',          3),
    ('print_format','OBJ',    'OBJ',             4),
    ('print_format','STEP',   'STEP / STP',      5),
    ('print_format','F3D',    'Fusion 360 F3D',  6),
    -- METS event types
    ('event_type','CREATE',        'Created',           1),
    ('event_type','INGEST',        'File Ingested',     2),
    ('event_type','TRANSFORM',     'Transformed',       3),
    ('event_type','QA_CHECK',      'QA Check',          4),
    ('event_type','VALIDATE',      'Validated',         5),
    ('event_type','MIGRATION',     'Migrated',          6),
    ('event_type','DELIVER',       'Delivered',         7),
    ('event_type','NOTE',          'Note Added',        8),
    ('event_type','STEP_COMPLETE', 'Step Completed',    9),
    ('event_type','STEP_REVERT',   'Step Reverted',    10),
    ('event_type','CORRECTION',    'Correction Made',  11);

INSERT OR IGNORE INTO workflow_step (job_type, step_key, label, description, sort_order) VALUES
    ('braille','digitized', 'Digitized',  'Source document scanned or received in digital form', 1),
    ('braille','formatted', 'Formatted',  'Document formatted for braille transcription',         2),
    ('braille','brailled',  'Brailled',   'Braille translation completed; BRF/BRL generated',    3),
    ('braille','proofread', 'Proofread',  'Braille output proofread and verified',                4),
    ('braille','delivered', 'Delivered',  'Final files and/or embossed copies delivered',         5),
    ('lp_ebraille','digitized',  'Digitized',              'Source document scanned or received', 1),
    ('lp_ebraille','formatted',  'Formatted',              'Document formatted for output',        2),
    ('lp_ebraille','converted',  'eBraille / Large Print', 'Conversion to target format done',    3),
    ('lp_ebraille','proofread',  'Proofread',              'Output proofread and verified',        4),
    ('lp_ebraille','delivered',  'Delivered',              'Final files and/or print copies delivered', 5),
    ('print','designed',   'Designed',    'CAD/3D model designed or obtained',                    1),
    ('print','sliced',     'Sliced',      'Model sliced; G-code generated',                       2),
    ('print','printed',    'Printed',     'Print job completed',                                  3),
    ('print','inspected',  'Inspected',   'Print inspected for quality',                          4),
    ('print','delivered',  'Delivered',   'Physical object delivered to requester',               5);
"""


def init_db() -> None:
    """Create all tables, directories, and seed data if they do not exist."""
    PRINTS_DIR.mkdir(exist_ok=True)
    FILES_DIR.mkdir(exist_ok=True)
    with get_conn() as conn:
        conn.executescript(_SCHEMA_SQL)
