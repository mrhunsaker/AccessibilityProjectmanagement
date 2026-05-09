"""Database schema and initialization helpers."""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "project_manager.db"
PRINTS_DIR = Path(__file__).parent.parent / "prints_files"


@contextmanager
def get_conn() -> Generator[sqlite3.Connection, None, None]:
    """Yield a configured SQLite connection and ensure commit/close."""
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


def init_db() -> None:
    PRINTS_DIR.mkdir(exist_ok=True)
    with get_conn() as conn:
        conn.executescript("""
    CREATE TABLE IF NOT EXISTS filament (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        brand       TEXT NOT NULL,
        color       TEXT NOT NULL,
        filament_type TEXT NOT NULL,          -- PLA, PETG, ABS, TPU, etc.
        diameter_mm REAL NOT NULL DEFAULT 1.75,
        quantity_g  REAL NOT NULL DEFAULT 0,  -- grams remaining
        notes       TEXT,
        created_at  TEXT DEFAULT (datetime('now')),
        updated_at  TEXT DEFAULT (datetime('now'))
    );

    -- ── Braille paper supplies ──────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS braille_paper (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_type   TEXT NOT NULL,  -- 'sheet_feed_11.5x11','sheet_feed_8.5x11','pin_feed_11.5x11','pin_feed_labels_8.5x11','generic_label'
        size         TEXT,           -- for generic labels, e.g. '4x2'
        label_type   TEXT,           -- for generic labels, e.g. 'removable', 'permanent'
        quantity     INTEGER NOT NULL DEFAULT 0,
        notes        TEXT,
        created_at   TEXT DEFAULT (datetime('now')),
        updated_at   TEXT DEFAULT (datetime('now'))
    );

    -- ── Electronics supplies ────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS electronics (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        category     TEXT NOT NULL,  -- 'board','microswitch','wire','mono_jack','bolt_nut','hex_screw','solder','other'
        name         TEXT NOT NULL,
        brand        TEXT,
        spec         TEXT,           -- size, gauge, resistance, etc.
        quantity     REAL NOT NULL DEFAULT 0,
        unit         TEXT NOT NULL DEFAULT 'pcs',  -- pcs, m, g, roll
        notes        TEXT,
        created_at   TEXT DEFAULT (datetime('now')),
        updated_at   TEXT DEFAULT (datetime('now'))
    );

    -- ── 3-D Printers (reference) ────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS printer (
        id    INTEGER PRIMARY KEY AUTOINCREMENT,
        name  TEXT NOT NULL UNIQUE   -- 'BambuLabs P1S', 'Sovol SV08 Max'
    );

    -- ── 3-D Print jobs ──────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS print_job (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        printer_id      INTEGER NOT NULL REFERENCES printer(id),
        filament_id     INTEGER REFERENCES filament(id),
        filament_used_g REAL,
        file_path       TEXT,        -- relative path inside prints_files/
        file_name       TEXT,
        successful      INTEGER NOT NULL DEFAULT 1,  -- 1=yes, 0=no
        failure_reason  TEXT,
        notes           TEXT,
        printed_at      TEXT DEFAULT (datetime('now'))
    );

    -- ── Braille jobs ────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS braille_job (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        title        TEXT NOT NULL,
        braille_type TEXT NOT NULL,  -- 'literary','math','science','music'
        digitized    INTEGER DEFAULT 0,
        formatted    INTEGER DEFAULT 0,
        brailled     INTEGER DEFAULT 0,
        proofread    INTEGER DEFAULT 0,
        delivered    INTEGER DEFAULT 0,
        notes        TEXT,
        created_at   TEXT DEFAULT (datetime('now')),
        updated_at   TEXT DEFAULT (datetime('now'))
    );

    -- ── Large Print / eBraille jobs ─────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS lp_ebraille_job (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        title        TEXT NOT NULL,
        job_type     TEXT NOT NULL,  -- 'large_print','ebraille'
        digitized    INTEGER DEFAULT 0,
        formatted    INTEGER DEFAULT 0,
        converted    INTEGER DEFAULT 0,  -- eBraille OR converted to large print
        proofread    INTEGER DEFAULT 0,
        delivered    INTEGER DEFAULT 0,
        notes        TEXT,
        created_at   TEXT DEFAULT (datetime('now')),
        updated_at   TEXT DEFAULT (datetime('now'))
    );

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
        sort_order  INTEGER DEFAULT 0,
        active      INTEGER DEFAULT 1,
        created_at  TEXT DEFAULT (datetime('now')),
        updated_at  TEXT DEFAULT (datetime('now')),
        UNIQUE(job_type, step_key)
    );

    -- Seed printers
    INSERT OR IGNORE INTO printer (name) VALUES ('BambuLabs P1S');
    INSERT OR IGNORE INTO printer (name) VALUES ('Sovol SV08 Max');

    INSERT OR IGNORE INTO material_category (section, value, label, sort_order) VALUES
        ('paper_type',   'sheet_feed_11.5x11',     'Sheet Feed 11.5x11',      1),
        ('paper_type',   'sheet_feed_8.5x11',      'Sheet Feed 8.5x11',       2),
        ('paper_type',   'pin_feed_11.5x11',       'Pin Feed 11.5x11',        3),
        ('paper_type',   'pin_feed_labels_8.5x11', 'Pin Feed Labels 8.5x11',  4),
        ('paper_type',   'generic_label',          'Generic Label',           5),
        ('elec_cat',     'board',                  'TRRS Trinkey / Micro:bit Board', 1),
        ('elec_cat',     'microswitch',            'Microswitch',             2),
        ('elec_cat',     'wire',                   'Wire',                    3),
        ('elec_cat',     'mono_jack',              'Mono Jack',               4),
        ('elec_cat',     'bolt_nut',               'Bolt / Nut',              5),
        ('elec_cat',     'hex_screw',              'Hex Screw',               6),
        ('elec_cat',     'solder',                 'Solder',                  7),
        ('elec_cat',     'other',                  'Other',                   8),
        ('elec_unit',    'pcs',                    'pcs',                     1),
        ('elec_unit',    'm',                      'm',                       2),
        ('elec_unit',    'g',                      'g',                       3),
        ('elec_unit',    'roll',                   'roll',                    4),
        ('elec_unit',    'ft',                     'ft',                      5),
        ('braille_type', 'literary',               'Literary',                1),
        ('braille_type', 'math',                   'Math',                    2),
        ('braille_type', 'science',                'Science',                 3),
        ('braille_type', 'music',                  'Music',                   4),
        ('lp_type',      'large_print',            'Large Print',             1),
        ('lp_type',      'ebraille',               'eBraille',                2),
        ('filament_type','PLA',                    'PLA',                     1),
        ('filament_type','PETG',                   'PETG',                    2),
        ('filament_type','ABS',                    'ABS',                     3),
        ('filament_type','TPU',                    'TPU',                     4),
        ('filament_type','ASA',                    'ASA',                     5),
        ('filament_type','Nylon',                  'Nylon',                   6),
        ('diameter_mm',  '1.75',                   '1.75 mm',                 1),
        ('diameter_mm',  '2.85',                   '2.85 mm',                 2);

    INSERT OR IGNORE INTO workflow_step (job_type, step_key, label, sort_order) VALUES
        ('braille',     'digitized',  'Digitized',   1),
        ('braille',     'formatted',  'Formatted',   2),
        ('braille',     'brailled',   'Brailled',    3),
        ('braille',     'proofread',  'Proofread',   4),
        ('braille',     'delivered',  'Delivered',   5),
        ('lp_ebraille', 'digitized',  'Digitized',   1),
        ('lp_ebraille', 'formatted',  'Formatted',   2),
        ('lp_ebraille', 'converted',  'eBraille / To Large Print', 3),
        ('lp_ebraille', 'proofread',  'Proofread',   4),
        ('lp_ebraille', 'delivered',  'Delivered',   5);
    """)
