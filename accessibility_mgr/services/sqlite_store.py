"""SQLite-backed persistence infrastructure.

Provides durable persistence for provenance events,
QA reports, pipeline history, and KPI metrics.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


DB_PATH = Path("accessibility_mgr.db")


class SQLiteStore:
    """Central SQLite persistence adapter."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DB_PATH
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS provenance_event (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS qa_report (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id INTEGER NOT NULL,
                    pipeline_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    findings_json TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS pipeline_run (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id INTEGER NOT NULL,
                    pipeline_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    retry_count INTEGER NOT NULL,
                    logs_json TEXT,
                    persisted_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS analytics_metric (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    category TEXT NOT NULL,
                    metadata_json TEXT,
                    recorded_at TEXT NOT NULL
                );
                """
            )

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
        with self._connect() as conn:
            conn.execute(query, params)
            conn.commit()

    def fetch_all(
        self,
        query: str,
        params: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]


__all__ = ["SQLiteStore", "DB_PATH"]
