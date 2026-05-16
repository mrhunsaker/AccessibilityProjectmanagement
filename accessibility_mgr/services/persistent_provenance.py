"""Persistent provenance registry."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .sqlite_store import SQLiteStore


class PersistentProvenanceRegistry:
    """SQLite-backed provenance registry."""

    def __init__(self, store: SQLiteStore | None = None) -> None:
        self.store = store or SQLiteStore()

    def register_event(
        self,
        *,
        asset_id: int,
        event_type: str,
        summary: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.store.execute(
            """
            INSERT INTO provenance_event (
                asset_id,
                event_type,
                summary,
                metadata_json,
                created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                asset_id,
                event_type,
                summary,
                json.dumps(metadata or {}),
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    def list_events(self) -> list[dict[str, Any]]:
        return self.store.fetch_all(
            """
            SELECT *
            FROM provenance_event
            ORDER BY created_at DESC
            """
        )


__all__ = ["PersistentProvenanceRegistry"]
