"""Persistent provenance registry — SQLite-backed provenance events.

AUDIT-FIX-007: this was previously an empty subclass of ProvenanceRegistry
with no override at all, so despite the name every provenance event was
stored in a plain Python list and lost on every restart. It now persists
events to a real SQLite table in the same database the rest of the
application uses.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .provenance_registry import ProvenanceEvent, ProvenanceRegistry


def _default_db_path() -> Path:
    try:
        from ..db.schema import DB_PATH
        return DB_PATH
    except Exception:
        return Path("accessibility_mgr.db")


class PersistentProvenanceRegistry(ProvenanceRegistry):
    """SQLite-backed provenance registry."""

    def __init__(self, database_path: Path | None = None) -> None:
        super().__init__()
        self.database_path = database_path or _default_db_path()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS provenance_event (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata TEXT
                )
                """
            )

    def register_event(
        self,
        *,
        asset_id: int,
        event_type: str,
        summary: str,
        metadata: dict[str, Any] | None = None,
    ) -> ProvenanceEvent:
        event = ProvenanceEvent(
            asset_id=asset_id,
            event_type=event_type,
            summary=summary,
            created_at=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )

        with self._connect() as connection:
            connection.execute(
                "INSERT INTO provenance_event "
                "(asset_id, event_type, summary, created_at, metadata) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    event.asset_id,
                    event.event_type,
                    event.summary,
                    event.created_at,
                    json.dumps(event.metadata),
                ),
            )

        return event

    def list_events(
        self,
        *,
        asset_id: int | None = None,
    ) -> list[dict[str, Any]]:
        with self._connect() as connection:
            if asset_id is not None:
                rows = connection.execute(
                    "SELECT asset_id, event_type, summary, created_at, metadata "
                    "FROM provenance_event WHERE asset_id = ? ORDER BY id ASC",
                    (asset_id,),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT asset_id, event_type, summary, created_at, metadata "
                    "FROM provenance_event ORDER BY id ASC"
                ).fetchall()

        results = []
        for row_asset_id, event_type, summary, created_at, metadata in rows:
            results.append(
                {
                    "asset_id": row_asset_id,
                    "event_type": event_type,
                    "summary": summary,
                    "created_at": created_at,
                    "metadata": json.loads(metadata) if metadata else {},
                }
            )
        return results


__all__ = [
    "PersistentProvenanceRegistry",
]
