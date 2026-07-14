"""Event streaming and webhook infrastructure — SQLite-backed."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _default_db_path() -> Path:
    try:
        from ..db.schema import DB_PATH
        return DB_PATH
    except Exception:
        return Path("accessibility_mgr.db")


class EventStreamService:
    """SQLite-backed internal event stream.

    Future targets:
    - webhook delivery
    - Kafka/NATS adapters
    - distributed event streaming
    - audit event propagation
    """

    def __init__(self, database_path: Path | None = None) -> None:
        self.database_path = database_path or _default_db_path()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS event_subscription (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    callback_url TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS platform_event (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                )"""
            )

    def subscribe(
        self,
        *,
        event_type: str,
        callback_url: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO event_subscription (event_type, callback_url, active) VALUES (?, ?, 1)",
                (event_type, callback_url),
            )

    def publish(
        self,
        *,
        event_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        created_at = datetime.now(UTC).isoformat()
        payload_json = json.dumps(payload, sort_keys=True)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO platform_event (event_type, payload_json, created_at) VALUES (?, ?, ?)",
                (event_type, payload_json, created_at),
            )
        return {
            "event_type": event_type,
            "payload": payload,
            "created_at": created_at,
        }

    def list_events(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            return [
                {
                    "event_type": r["event_type"],
                    "payload": json.loads(r["payload_json"]),
                    "created_at": r["created_at"],
                }
                for r in conn.execute(
                    "SELECT * FROM platform_event ORDER BY id"
                ).fetchall()
            ]

    def list_subscriptions(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            return [
                {
                    "event_type": r["event_type"],
                    "callback_url": r["callback_url"],
                    "active": bool(r["active"]),
                }
                for r in conn.execute("SELECT * FROM event_subscription").fetchall()
            ]


__all__ = ["EventStreamService"]
