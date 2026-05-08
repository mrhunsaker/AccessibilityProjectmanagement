"""
Database schema and initialization for Braille/Maker Project Manager.
Uses SQLite with best-practice normalized tables.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "project_manager.db"
PRINTS_DIR = Path(__file__).parent.parent / "prints_files"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db():
    PRINTS_DIR.mkdir(exist_ok=True)
    conn = get_conn()
    cur = conn.cursor()

    # ── Filament inventory ──────────────────────────────────────────────────
    cur.executescript("""
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

    -- Seed printers
    INSERT OR IGNORE INTO printer (name) VALUES ('BambuLabs P1S');
    INSERT OR IGNORE INTO printer (name) VALUES ('Sovol SV08 Max');
    """)

    conn.commit()
    conn.close()
